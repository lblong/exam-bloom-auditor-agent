import re
from pathlib import Path
from typing import List

import pandas as pd
from docx import Document

from models import Question

RE_CAU = re.compile(r"^C[âa]u\s*(\d+)\s*[\.\:\)]\s*(.*)", re.IGNORECASE)
RE_PA = re.compile(r"^([A-J])\s*[\.\)]\s*(.*)")
RE_DAP_AN = re.compile(r"^[ĐD][áa]p\s*[áa]n\s*[:\-]?\s*(.*)", re.IGNORECASE)


def doc_dap_an(phan_sau):
    """'A' -> 'A'; 'A, C' / 'A và C' / 'AC' -> 'A,C'; không đọc được -> None"""
    if not phan_sau or not str(phan_sau).strip():
        return None
    # Cắt bỏ phần giải thích nếu gặp ., (, -, :, ; hoặc các từ giải thích thông dụng
    doan = re.split(r"[.\(\-\:\;]|\b(?:do|vì|vi|bởi|boi|giải thích|giai thich)\b", str(phan_sau), flags=re.IGNORECASE)[0].strip().upper()
    cac_chu = []
    for p in re.split(r"[^A-ZÀ-Ỹ]+", doan):
        if not p or p in ("VÀ", "AND", "&"):
            continue
        # Chỉ nhận chữ cái phương án hợp lệ (A đến J), tối đa 4 ký tự nếu viết liền (ví dụ: AB, CD)
        if re.fullmatch(r"[A-J]{1,4}", p):
            cac_chu.extend(p)
        else:
            break
    return ",".join(sorted(set(cac_chu))) or None


def parse_lines(lines):
    questions, current = [], None
    dang_o = "than"   # than (thân câu hỏi) -> pa (đang đọc phương án) -> xong (đã gặp Đáp án)
    chu_cuoi = ""
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        m = RE_CAU.match(line)
        if m:
            current = Question(so_cau=int(m.group(1)), than_cau_hoi=m.group(2).strip())
            questions.append(current)
            dang_o, chu_cuoi = "than", ""
            continue
        if current is None or dang_o == "xong":
            continue   # chưa vào câu nào, hoặc đang là phần giải thích sau Đáp án

        m = RE_DAP_AN.match(line)
        if m:
            current.dap_an_dung = doc_dap_an(m.group(1))
            dang_o = "xong"
            continue

        m = RE_PA.match(line)
        if m and m.group(1) > chu_cuoi:   # chỉ nhận chữ cái tăng dần: A, B, C...
            current.phuong_an[m.group(1)] = m.group(2).strip()
            chu_cuoi = m.group(1)
            dang_o = "pa"
            continue

        # Dòng không khớp gì: nối vào phương án cuối (nếu đang đọc phương án) hoặc thân câu hỏi
        if dang_o == "pa":
            current.phuong_an[chu_cuoi] = (current.phuong_an[chu_cuoi] + " " + line).strip()
        else:
            current.than_cau_hoi += " " + line
    return questions


def parse_docx(path):
    return parse_lines([p.text for p in Document(path).paragraphs])


def parse_xlsx(path: str) -> List[Question]:
    df = pd.read_excel(path, dtype=str).fillna("")
    # Chuẩn hóa tên cột: map tên cột viết hoa, bỏ khoảng trắng thừa -> tên cột gốc
    col_map = {str(c).strip().upper(): c for c in df.columns}

    col_stt = col_map.get("STT")
    col_cau_hoi = col_map.get("CÂU HỎI") or col_map.get("CAU HOI") or col_map.get("NỘI DUNG") or col_map.get("NOI DUNG")
    col_dap_an = col_map.get("ĐÁP ÁN") or col_map.get("DAP AN") or col_map.get("ANSWER")

    questions: List[Question] = []
    for i, row in df.iterrows():
        # Đọc phương án từ A đến J (hỗ trợ đề có 4, 5, 6... phương án: A, B, C, D, E, F...)
        phuong_an = {}
        for k in "ABCDEFGHIJ":
            col_k = col_map.get(k)
            if col_k and str(row[col_k]).strip():
                phuong_an[k] = str(row[col_k]).strip()

        # Chuẩn hóa đáp án qua doc_dap_an (A và C -> A,C; AC -> A,C; B do... -> B)
        raw_dap_an = str(row[col_dap_an]).strip() if col_dap_an else ""
        dap_an = doc_dap_an(raw_dap_an)

        raw_stt = str(row[col_stt]).strip() if col_stt else ""
        try:
            so_cau = int(float(raw_stt)) if raw_stt else i + 1
        except (ValueError, TypeError):
            so_cau = i + 1

        than_cau_hoi = str(row[col_cau_hoi]).strip() if col_cau_hoi else ""
        # Bỏ qua dòng trống hoàn toàn trong Excel
        if not than_cau_hoi and not phuong_an:
            continue

        questions.append(
            Question(
                so_cau=so_cau,
                than_cau_hoi=than_cau_hoi,
                phuong_an=phuong_an,
                dap_an_dung=dap_an,
            )
        )
    return questions


def parse_file(path: str) -> List[Question]:
    """Tool 1: tự nhận loại file và bóc tách thành danh sách Question."""
    ext = Path(path).suffix.lower()
    if ext == ".docx":
        return parse_docx(path)
    if ext in (".xlsx", ".xls"):
        return parse_xlsx(path)
    raise ValueError(f"Định dạng file không hỗ trợ: {ext}")
