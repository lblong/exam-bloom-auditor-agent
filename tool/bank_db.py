import json
import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select

from database import QuestionRecord, SessionLocal, init_db
from models import BloomResult, Question, ValidationResult, VerifyReport

NGUONG_TIN_CAY = 0.6


def decide_status(v: ValidationResult, b: Optional[BloomResult]) -> str:
    """Guardrail: chỉ APPROVED khi qua 100% kiểm tra kỹ thuật VÀ Bloom rõ ràng."""
    if not v.passed:
        return "NEEDS_EDIT"
    if b is None or b.muc_do == "KHONG_XAC_DINH" or b.do_tin_cay < NGUONG_TIN_CAY:
        return "NEEDS_MANUAL_REVIEW"
    return "APPROVED"


def write_records(
    questions: List[Question],
    validations: List[ValidationResult],
    blooms: List[BloomResult],
    batch_id: Optional[str] = None,
) -> Tuple[str, List[Dict]]:
    """Tool 4: ghi vào DB. Trả về (batch_id, danh sách bản ghi KỲ VỌNG để Tool 5 đối chiếu)."""
    init_db()
    batch_id = batch_id or uuid.uuid4().hex[:8]
    b_map = {b.so_cau: b for b in blooms}
    expected: List[Dict] = []

    with SessionLocal() as s:
        for q, v in zip(questions, validations):
            b = b_map.get(q.so_cau)
            trang_thai = decide_status(v, b)
            s.add(
                QuestionRecord(
                    batch_id=batch_id,
                    so_cau=q.so_cau,
                    than_cau_hoi=q.than_cau_hoi,
                    phuong_an=json.dumps(q.phuong_an, ensure_ascii=False),
                    dap_an_dung=q.dap_an_dung,
                    trang_thai=trang_thai,
                    loi=json.dumps([l.model_dump() for l in v.loi], ensure_ascii=False),
                    muc_bloom=b.muc_do if b else None,
                    ly_do_bloom=b.ly_do if b else None,
                    do_tin_cay=b.do_tin_cay if b else None,
                )
            )
            expected.append(
                {
                    "so_cau": q.so_cau,
                    "trang_thai": trang_thai,
                    "muc_bloom": b.muc_do if b else None,
                    "than_cau_hoi": q.than_cau_hoi,
                    "dap_an_dung": q.dap_an_dung,
                }
            )
        s.commit()
    return batch_id, expected


def verify_records(batch_id: str, expected: List[Dict]) -> VerifyReport:
    """Tool 5: mở phiên MỚI, đọc lại từ DB và đối chiếu từng trường (Read-after-Write)."""
    sai_lech: List[str] = []
    with SessionLocal() as s:
        rows = s.execute(
            select(QuestionRecord)
            .where(QuestionRecord.batch_id == batch_id)
            .order_by(QuestionRecord.id)
        ).scalars().all()

        if len(rows) != len(expected):
            sai_lech.append(f"Số bản ghi lệch: kỳ vọng {len(expected)}, đọc được {len(rows)}")

        for exp, row in zip(expected, rows):
            for truong in ["so_cau", "trang_thai", "muc_bloom", "than_cau_hoi", "dap_an_dung"]:
                if getattr(row, truong) != exp[truong]:
                    sai_lech.append(
                        f"Câu {exp['so_cau']}: trường '{truong}' lệch "
                        f"(kỳ vọng {exp[truong]!r}, DB có {getattr(row, truong)!r})"
                    )

    return VerifyReport(
        ok=len(sai_lech) == 0,
        so_ky_vong=len(expected),
        so_doc_duoc=len(rows),
        sai_lech=sai_lech,
    )