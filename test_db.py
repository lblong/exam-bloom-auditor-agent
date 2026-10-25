import copy

from models import BloomResult
from tool.bank_db import verify_records, write_records
from tool.file_parser import parse_file
from tool.rule_validator import validate_all

ds = parse_file("data/de_mau.docx")
vals = validate_all(ds)

# Nhãn Bloom GIẢ để test, không gọi OpenAI nên không tốn token
blooms = [
    BloomResult(so_cau=1, muc_do="NHO", ly_do="giả", do_tin_cay=0.9),
    BloomResult(so_cau=2, muc_do="HIEU", ly_do="giả", do_tin_cay=0.9),
    BloomResult(so_cau=3, muc_do="VAN_DUNG", ly_do="giả", do_tin_cay=0.8),
]

batch_id, expected = write_records(ds, vals, blooms)
print(f"Đã ghi batch {batch_id}")
for e in expected:
    print(f"  Câu {e['so_cau']}: {e['trang_thai']}")

print("\n--- Tool 5: đọc lại và xác minh ---")
print(verify_records(batch_id, expected))

print("\n--- Thử cố tình sai để xem Tool 5 có bắt được không ---")
sai = copy.deepcopy(expected)
sai[0]["trang_thai"] = "NEEDS_EDIT"
print(verify_records(batch_id, sai))