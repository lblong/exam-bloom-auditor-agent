import json
import sys

import pandas as pd

from agent import run_audit

dung_bloom = "--bloom" in sys.argv   # mặc định KHÔNG gọi OpenAI

with open("data/ground_truth.json", encoding="utf-8") as f:
    truth = {t["so_cau"]: t for t in json.load(f)}

kq = run_audit("data/bo_test_40.docx", dung_bloom=dung_bloom, on_step=print)
if not kq["hoan_thanh"]:
    print("Agent không hoàn thành:", kq.get("ly_do"))
    sys.exit(1)

rows = []
for r in kq["bao_cao"]:
    t = truth[r["so_cau"]]
    rows.append({
        "so_cau": r["so_cau"],
        "co_loi_that": t["co_loi"],
        "ma_loi_ky_vong": t["ma_loi"],
        "trang_thai": r["trang_thai"],
        "loi_phat_hien": r["loi"],
        "bloom_that": t["bloom"],
        "bloom_du_doan": r["muc_bloom"],
        "ly_do_bloom": r["ly_do_bloom"],
    })
df = pd.DataFrame(rows)

print("\n" + "=" * 50)

# ---------- KPI 2: tỷ lệ lọt lưới câu lỗi ----------
loi = df[df.co_loi_that]
bat_duoc = loi[loi.trang_thai == "NEEDS_EDIT"]
lot_luoi = loi[loi.trang_thai != "NEEDS_EDIT"]
kpi2 = len(lot_luoi) / len(loi) * 100
print(f"KPI 2 (tỷ lệ lọt lưới): {len(lot_luoi)}/{len(loi)} = {kpi2:.1f}%   (mục tiêu 0%)")
if len(lot_luoi):
    print("  Câu LỌT LƯỚI:", lot_luoi.so_cau.tolist())

bao_nham = df[(~df.co_loi_that) & (df.trang_thai == "NEEDS_EDIT")]
print(f"  Báo nhầm (câu chuẩn bị gắn NEEDS_EDIT): {len(bao_nham)}/{(~df.co_loi_that).sum()}")

# ---------- KPI 1: độ chính xác Bloom ----------
if dung_bloom:
    chuan = df[~df.co_loi_that]
    dung = (chuan.bloom_that == chuan.bloom_du_doan).sum()
    kpi1 = dung / len(chuan) * 100
    print(f"\nKPI 1 (độ chính xác Bloom): {dung}/{len(chuan)} = {kpi1:.1f}%   (mục tiêu >= 85%)")
    sai = chuan[chuan.bloom_that != chuan.bloom_du_doan]
    print("\nCác câu gán SAI:")
    for _, r in sai.iterrows():
        print(f"  Câu {r.so_cau}: chuẩn={r.bloom_that}, AI={r.bloom_du_doan} | {r.ly_do_bloom}")
    print("\nMa trận nhầm lẫn (hàng = chuẩn, cột = AI dự đoán):")
    print(pd.crosstab(chuan.bloom_that, chuan.bloom_du_doan))
    print(f"\nToken đã dùng: vào={kq['token']['vao']}, ra={kq['token']['ra']}")
else:
    print("\n(Chưa chạy Bloom nên chưa đo KPI 1. Thêm --bloom để đo.)")

df.to_excel("data/ket_qua_kpi.xlsx", index=False)
print("\nĐã lưu chi tiết từng câu vào data/ket_qua_kpi.xlsx")