import re
import unicodedata
from typing import List

from models import Question, Issue, ValidationResult

# Các cụm bị cấm (viết chữ thường, không dấu câu). Có thể thêm theo quy chế của trường.
CUM_TU_CAM = [
    "tất cả các câu trên",
    "tất cả các đáp án trên",
    "tất cả đáp án trên",
    "tất cả các phương án trên",
    "không có đáp án nào đúng",
    "không đáp án nào đúng",
    "all of the above",
    "none of the above",
]


def chuan_hoa(s: str) -> str:
    """Chuẩn hóa chuỗi để so sánh: chữ thường, bỏ khoảng trắng thừa, bỏ dấu câu ở hai đầu."""
    s = unicodedata.normalize("NFC", s).lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,;:!?")


def validate_question(q: Question) -> ValidationResult:
    loi: List[Issue] = []

    # 1. Thân câu hỏi
    if not q.than_cau_hoi.strip():
        loi.append(Issue(ma_loi="THIEU_THAN_CAU_HOI", mo_ta="Câu hỏi không có nội dung"))

    # 2. Đủ 4 phương án A-D
    thieu = [k for k in "ABCD" if not q.phuong_an.get(k, "").strip()]
    if thieu:
        loi.append(Issue(ma_loi="THIEU_PHUONG_AN",
                         mo_ta=f"Thiếu hoặc rỗng phương án: {', '.join(thieu)}"))

    # 3. Trùng phương án
    da_thay = {}
    for k, v in q.phuong_an.items():
        n = chuan_hoa(v)
        if not n:
            continue
        if n in da_thay:
            loi.append(Issue(ma_loi="TRUNG_PHUONG_AN",
                             mo_ta=f"Phương án {da_thay[n]} và {k} trùng nội dung"))
        else:
            da_thay[n] = k

    # 4. Cụm từ bị cấm
    for k, v in q.phuong_an.items():
        n = chuan_hoa(v)
        for cum in CUM_TU_CAM:
            if cum in n:
                loi.append(Issue(ma_loi="VI_PHAM_QUY_CHE",
                                 mo_ta=f"Phương án {k} chứa cụm bị cấm: '{cum}'"))
                break

    # 5. Đáp án đúng
    if not q.dap_an_dung:
        loi.append(Issue(ma_loi="THIEU_DAP_AN", mo_ta="Câu hỏi không có đáp án đúng"))
    elif q.dap_an_dung not in q.phuong_an:
        loi.append(Issue(ma_loi="DAP_AN_KHONG_HOP_LE",
                         mo_ta=f"Đáp án '{q.dap_an_dung}' không nằm trong các phương án"))

    return ValidationResult(so_cau=q.so_cau, passed=len(loi) == 0, loi=loi)


def validate_all(questions: List[Question]) -> List[ValidationResult]:
    """Tool 2: quét toàn bộ danh sách câu hỏi."""
    return [validate_question(q) for q in questions]