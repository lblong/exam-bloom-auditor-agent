import os
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import run_audit

load_dotenv()

st.set_page_config(page_title="Exam Quality & Bloom Auditor", page_icon="📝", layout="wide")
st.title("📝 Exam Quality & Bloom's Auditor Agent")
st.caption("Kiểm định hình thức đề thi và phân loại Thang đo Bloom cho ngân hàng câu hỏi")

# ---------- Thanh bên: cài đặt ----------
with st.sidebar:
    st.header("⚙️ Cài đặt")
    dung_bloom = st.checkbox("Dùng GPT phân loại Bloom (💰 tốn token)", value=False)
    mat_khau = os.getenv("DEMO_PASSWORD", "")
    if dung_bloom and mat_khau:
        nhap = st.text_input("Mật khẩu demo (để dùng GPT)", type="password")
        if nhap != mat_khau:
            st.warning("Nhập đúng mật khẩu để bật GPT.")
            dung_bloom = False
    ca_cau_loi = st.checkbox(
        "Phân loại Bloom cả câu đã bị lỗi", value=False, disabled=not dung_bloom
    )
    st.caption(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    st.info(
        "Tắt ô GPT = chạy thử miễn phí (chỉ quét lỗi hình thức).\n\n"
        "Bật ô GPT = mỗi câu qua kiểm tra kỹ thuật sẽ gọi OpenAI 1 lần."
    )

# ---------- Tải file + chạy ----------
up = st.file_uploader("Tải file đề thi (.docx hoặc .xlsx)", type=["docx", "xlsx"])

if st.button("🚀 Chạy kiểm định", type="primary", disabled=up is None):
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    path = Path("data/uploads") / up.name
    path.write_bytes(up.getbuffer())

    with st.status("Agent đang chạy...", expanded=True) as status:
        kq = run_audit(
            str(path),
            dung_bloom=dung_bloom,
            danh_gia_ca_cau_loi=ca_cau_loi,
            on_step=lambda m: st.write(m),
        )
        status.update(label="Agent đã chạy xong", state="complete")
    st.session_state["kq"] = kq

# ---------- Hiển thị kết quả ----------
kq = st.session_state.get("kq")
if kq:
    if not kq["hoan_thanh"]:
        st.error(f"Không hoàn thành: {kq.get('ly_do')}")
        st.json(kq.get("verify", {}))
    else:
        th = kq["tong_hop_trang_thai"]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Tổng số câu", kq["tong_so_cau"])
        c2.metric("✅ APPROVED", th.get("APPROVED", 0))
        c3.metric("❌ NEEDS_EDIT", th.get("NEEDS_EDIT", 0))
        c4.metric("👀 NEEDS_MANUAL_REVIEW", th.get("NEEDS_MANUAL_REVIEW", 0))
        c5.metric("Token (vào/ra)", f"{kq['token']['vao']}/{kq['token']['ra']}")

        st.success(
            f"Đã ghi {kq['verify']['so_doc_duoc']} bản ghi vào DB và xác minh khớp 100% "
            f"(batch {kq['batch_id']})"
        )

        df = pd.DataFrame(kq["bao_cao"]).rename(
            columns={
                "so_cau": "Câu",
                "cau_hoi": "Nội dung câu hỏi",
                "trang_thai": "Trạng thái",
                "loi": "Lỗi hình thức",
                "muc_bloom": "Mức Bloom",
                "ly_do_bloom": "Lý do Bloom",
                "do_tin_cay": "Độ tin cậy",
            }
        )

        st.subheader("📋 Báo cáo kiểm định")
        st.dataframe(df, width="stretch", hide_index=True)

        if kq["ma_tran_bloom"]:
            st.subheader("📊 Ma trận đề thi theo Bloom")
            st.bar_chart(pd.Series(kq["ma_tran_bloom"], name="Số câu"))

        # Tải báo cáo
        buf = BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl")
        d1, d2 = st.columns(2)
        d1.download_button(
            "⬇️ Tải báo cáo Excel", buf.getvalue(), "bao_cao_kiem_dinh.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        d2.download_button(
            "⬇️ Tải báo cáo CSV", df.to_csv(index=False).encode("utf-8-sig"),
            "bao_cao_kiem_dinh.csv", "text/csv",
        )

        with st.expander("🔎 Nhật ký hoạt động của Agent"):
            st.json(kq["log"])