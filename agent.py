import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from tool.bank_db import verify_records, write_records
from tool.bloom_evaluator import evaluate_all
from tool.file_parser import parse_file
from tool.rule_validator import validate_all

LOG_FILE = Path("data/agent_log.jsonl")


class AgentLogger:
    """Ghi nhật ký từng bước của Agent (vừa giữ trong bộ nhớ, vừa ghi ra file)."""

    def __init__(self):
        self.events = []

    def log(self, buoc: int, tool: str, mo_ta: str, **extra):
        ev = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "buoc": buoc,
            "tool": tool,
            "mo_ta": mo_ta,
            **extra,
        }
        self.events.append(ev)
        LOG_FILE.parent.mkdir(exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def run_audit(
    file_path: str,
    limit: Optional[int] = None,
    dung_bloom: bool = True,
    on_step: Optional[Callable[[str], None]] = None,
) -> Dict:
    lg = AgentLogger()

    def say(msg: str):
        if on_step:
            on_step(msg)

    # ---- Bước 1: Tiếp nhận ----
    say("Bước 1/6: Tiếp nhận file...")
    lg.log(1, "Intake", f"Nhận file {Path(file_path).name}")

    # ---- Bước 2: Trích xuất (Tool 1) ----
    say("Bước 2/6: Bóc tách câu hỏi (File Parser)...")
    questions = parse_file(file_path)
    if limit:
        questions = questions[:limit]
    lg.log(2, "File Parser Tool", f"Bóc tách được {len(questions)} câu")
    if not questions:
        return {"hoan_thanh": False, "ly_do": "Không đọc được câu hỏi nào từ file", "log": lg.events}

    # ---- Bước 3: Quét lỗi hình thức (Tool 2) ----
    say("Bước 3/6: Quét lỗi hình thức (Rule Validator)...")
    vals = validate_all(questions)
    n_loi = sum(1 for v in vals if not v.passed)
    lg.log(3, "Rule Validator Tool", f"{n_loi}/{len(vals)} câu có lỗi hình thức",
           cau_loi=[v.so_cau for v in vals if not v.passed])

    # ---- Bước 4: Phân loại Bloom (Tool 3) -- 💰 TỐN TOKEN ----
    blooms = []
    tok_in = tok_out = 0
    if dung_bloom:
        can_danh_gia = [q for q, v in zip(questions, vals) if v.passed]
        say(f"Bước 4/6: Phân loại Bloom bằng GPT ({len(can_danh_gia)} câu)...")
        blooms = evaluate_all(can_danh_gia) if can_danh_gia else []
        tok_in = sum(b.input_tokens for b in blooms)
        tok_out = sum(b.output_tokens for b in blooms)
        lg.log(4, "Bloom Evaluator Tool", f"Đã gán nhãn {len(blooms)} câu",
               model=blooms[0].model if blooms else "", input_tokens=tok_in, output_tokens=tok_out,
               chi_tiet=[{"so_cau": b.so_cau, "muc_do": b.muc_do, "do_tin_cay": b.do_tin_cay, "ly_do": b.ly_do}
                         for b in blooms])
    else:
        say("Bước 4/6: BỎ QUA Bloom (chế độ chạy thử, không tốn token)")
        lg.log(4, "Bloom Evaluator Tool", "Bỏ qua (dung_bloom=False)")

    # ---- Bước 5: Ghi sổ (Tool 4) + Xác minh (Tool 5) ----
    say("Bước 5/6: Ghi vào Database và đọc lại để xác minh...")
    batch_id, expected = write_records(questions, vals, blooms)
    lg.log(5, "Bank DB Writer Tool", f"Đã ghi {len(expected)} bản ghi", batch_id=batch_id)

    vr = verify_records(batch_id, expected)
    lg.log(5, "DB Verifier Tool", "Read-after-Write: " + ("KHỚP 100%" if vr.ok else "SAI LỆCH"),
           ok=vr.ok, sai_lech=vr.sai_lech)
    if not vr.ok:
        # Guardrail: chưa xác minh được thì KHÔNG báo hoàn thành
        say("Xác minh thất bại, dừng lại.")
        return {"hoan_thanh": False, "ly_do": "Xác minh DB thất bại", "verify": vr.model_dump(),
                "batch_id": batch_id, "log": lg.events}

    # ---- Bước 6: Xuất báo cáo ----
    say("Bước 6/6: Tạo báo cáo kiểm định...")
    b_map = {b.so_cau: b for b in blooms}
    rows = []
    for q, v, e in zip(questions, vals, expected):
        b = b_map.get(q.so_cau)
        if b:
            if b.muc_do == "KHONG_XAC_DINH" and "Lỗi" in b.ly_do:
                muc_bloom = "LỖI"
            else:
                muc_bloom = b.muc_do
            ly_do_bloom = b.ly_do
            do_tin_cay = b.do_tin_cay
        else:
            if not dung_bloom:
                muc_bloom = "CHƯA_ĐO"
                ly_do_bloom = "Không thể đo vì chưa bật tính năng AI phân tích Bloom"
            elif not v.passed:
                muc_bloom = "KHÔNG_ĐO"
                ly_do_bloom = "Không thể đo vì câu hỏi bị lỗi hình thức kỹ thuật (bị loại trước khi gọi AI)"
            else:
                muc_bloom = "LỖI"
                ly_do_bloom = "Không thể đo do lỗi phát sinh khi gọi AI"
            do_tin_cay = None

        rows.append({
            "so_cau": q.so_cau,
            "cau_hoi": q.than_cau_hoi,
            "trang_thai": e["trang_thai"],
            "loi": "; ".join(f"[{l.ma_loi}] {l.mo_ta}" for l in v.loi),
            "muc_bloom": muc_bloom,
            "ly_do_bloom": ly_do_bloom,
            "do_tin_cay": do_tin_cay,
        })

    ket_qua = {
        "hoan_thanh": True,
        "batch_id": batch_id,
        "tong_so_cau": len(rows),
        "tong_hop_trang_thai": dict(Counter(r["trang_thai"] for r in rows)),
        "ma_tran_bloom": dict(Counter(r["muc_bloom"] for r in rows if r["muc_bloom"] in ("NHO", "HIEU", "VAN_DUNG", "PHAN_TICH"))),
        "bao_cao": rows,
        "token": {"vao": tok_in, "ra": tok_out},
        "verify": vr.model_dump(),
        "log": lg.events,
    }
    lg.log(6, "Report", "Hoàn thành", tong_hop=ket_qua["tong_hop_trang_thai"])
    return ket_qua