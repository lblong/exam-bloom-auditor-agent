import re
import unicodedata
from typing import List

from models import Question, Issue, ValidationResult

SO_PA_TOI_THIEU = 2
CHO_PHEP_NHIEU_DAP_AN = True   # đổi False nếu quy chế chỉ cho phép 1 đáp án
# Các cụm bị cấm (viết chữ thường, không dấu câu). Có thể thêm theo quy chế của trường.
SO_CHU = {
    "một": 1, "hai": 2, "ba": 3, "bốn": 4, "năm": 5,
    "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mười": 10
}


def so_dap_an_yeu_cau(than):
    """
    Trả về số đáp án mà đề yêu cầu (int) hoặc 'NHIEU':
    - Nếu có dạng '(chọn X đáp án [đúng / đúng nhất / chính xác...])' (hoặc phương án/câu/ý) trong ngoặc: trả về X.
    - Nếu có dạng '(chọn nhiều/tất cả [các] đáp án [đúng...])': trả về 'NHIEU'.
    - Nếu không có ghi chú trong ngoặc: mặc định là 1 đáp án duy nhất.
    """
    t = than.lower()
    m = re.search(r"[\(\[\{]\s*chọn\s+(\d+|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười)\s+(?:đáp án|phương án|câu|ý|câu trả lời)(?:\s+[^)\]}]+)?\s*[\)\]\}]", t)
    if m:
        v = m.group(1)
        return int(v) if v.isdigit() else SO_CHU.get(v, 1)
    if re.search(r"[\(\[\{]\s*chọn\s+(?:tất cả|nhiều)(?:\s+[^)\]}]+)?\s*[\)\]\}]", t):
        return "NHIEU"
    return 1

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

    
    # 2. Phương án: tối thiểu 2, liên tục từ A, không rỗng
    chu_cai = sorted(q.phuong_an.keys())

    khong_hop_le = [
        k for k in chu_cai
        if len(k) != 1 or k not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ]

    if khong_hop_le:
        loi.append(Issue(
            ma_loi="KHOA_PHUONG_AN_KHONG_HOP_LE",
            mo_ta=f"Khóa phương án không hợp lệ: {', '.join(khong_hop_le)}"
        ))

    if len(chu_cai) < SO_PA_TOI_THIEU:
        loi.append(Issue(
            ma_loi="THIEU_PHUONG_AN",
            mo_ta=f"Chỉ có {len(chu_cai)} phương án, cần tối thiểu {SO_PA_TOI_THIEU}"
        ))

    if not khong_hop_le and chu_cai:
        mong_doi = [
            chr(ord("A") + i)
            for i in range(ord(chu_cai[-1]) - ord("A") + 1)
        ]

        thieu = [
            k for k in mong_doi
            if not q.phuong_an.get(k, "").strip()
        ]

        if thieu:
            loi.append(Issue(
                ma_loi="THIEU_PHUONG_AN",
                mo_ta=f"Thiếu hoặc rỗng phương án: {', '.join(thieu)}"
            ))


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

    # 5. Đáp án đúng (có thể nhiều đáp án, dạng 'A,C')
    cac_dap_an = []
    if not q.dap_an_dung or not q.dap_an_dung.strip():
        loi.append(Issue(ma_loi="THIEU_DAP_AN", mo_ta="Câu hỏi không có đáp án đúng"))
    else:
        cac_dap_an = [
            d.strip().upper()
            for d in q.dap_an_dung.split(",")
        ]

        if any(not d for d in cac_dap_an):
            loi.append(Issue(
                ma_loi="DAP_AN_RONG",
                mo_ta="Danh sách đáp án đúng có phần tử rỗng"
            ))
        if len(cac_dap_an) != len(set(cac_dap_an)):
            loi.append(Issue(
                ma_loi="TRUNG_DAP_AN",
                mo_ta="Đáp án đúng bị lặp"
            ))
        if len(cac_dap_an) > 1 and not CHO_PHEP_NHIEU_DAP_AN:
            loi.append(Issue(ma_loi="NHIEU_DAP_AN", mo_ta="Câu có nhiều hơn 1 đáp án đúng"))
        sai = [d for d in cac_dap_an if d and d not in q.phuong_an]
        if sai:
            loi.append(Issue(ma_loi="DAP_AN_KHONG_HOP_LE",
                             mo_ta=f"Đáp án {', '.join(sai)} không nằm trong các phương án"))

    
    # 6. Số đáp án phải khớp với yêu cầu ghi trong đề (mặc định 1 đáp án nếu không có ghi chú '(chọn ... đáp án)')
    yeu_cau = so_dap_an_yeu_cau(q.than_cau_hoi)

    if cac_dap_an and yeu_cau:
        n = len(cac_dap_an)

        if yeu_cau == "NHIEU" and n < 2:
            loi.append(Issue(
                ma_loi="SO_DAP_AN_KHONG_KHOP",
                mo_ta="Đề yêu cầu (chọn nhiều đáp án) nhưng chỉ có 1 đáp án"
            ))
        elif isinstance(yeu_cau, int) and n != yeu_cau:
            if yeu_cau == 1:
                loi.append(Issue(
                    ma_loi="NHIEU_DAP_AN",
                    mo_ta=f"Câu hỏi không có ghi chú '(chọn ... đáp án)' nên mặc định chỉ có 1 đáp án đúng, nhưng đề có {n} đáp án"
                ))
            else:
                loi.append(Issue(
                    ma_loi="SO_DAP_AN_KHONG_KHOP",
                    mo_ta=f"Đề yêu cầu (chọn {yeu_cau} đáp án) nhưng có {n} đáp án"
                ))

    return ValidationResult(
        so_cau=q.so_cau,
        passed=len(loi) == 0,
        loi=loi
    )



def validate_all(questions: List[Question]) -> List[ValidationResult]:
    """Tool 2: quét toàn bộ danh sách câu hỏi."""
    return [validate_question(q) for q in questions]
