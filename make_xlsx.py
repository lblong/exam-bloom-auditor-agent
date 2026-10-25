import pandas as pd
from tool.file_parser import parse_file

rows = []
for q in parse_file("data/de_mau.docx"):
    rows.append({
        "STT": q.so_cau,
        "Câu hỏi": q.than_cau_hoi,
        "A": q.phuong_an.get("A", ""),
        "B": q.phuong_an.get("B", ""),
        "C": q.phuong_an.get("C", ""),
        "D": q.phuong_an.get("D", ""),
        "Đáp án": q.dap_an_dung or "",
    })
pd.DataFrame(rows).to_excel("data/de_mau.xlsx", index=False)
print("Đã tạo data/de_mau.xlsx")