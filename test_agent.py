import json
import sys

from agent import run_audit

dung_bloom = "--bloom" in sys.argv   # mặc định KHÔNG gọi OpenAI

kq = run_audit("data/de_mau.docx", dung_bloom=dung_bloom, on_step=print)

print("\n===== KẾT QUẢ =====")
print("Hoàn thành:", kq["hoan_thanh"])
print("Tổng hợp trạng thái:", kq.get("tong_hop_trang_thai"))
print("Ma trận Bloom:", kq.get("ma_tran_bloom"))
print("Token:", kq.get("token"))
print("Xác minh DB:", kq.get("verify"))
print()
for r in kq.get("bao_cao", []):
    print(f"Câu {r['so_cau']}: {r['trang_thai']} | Bloom={r['muc_bloom']} | {r['loi']}")