from tool.file_parser import parse_file
from tool.rule_validator import validate_all

ket_qua = validate_all(parse_file("data/de_mau.docx"))
for r in ket_qua:
    print(f"Câu {r.so_cau}: {'[DAT]' if r.passed else '[LOI]'}")
    for l in r.loi:
        print(f"   - [{l.ma_loi}] {l.mo_ta}")