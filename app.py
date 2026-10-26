import os
import re
from io import BytesIO
from pathlib import Path
import time

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import run_audit

load_dotenv()

st.set_page_config(
    page_title="Exam Quality & Bloom Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- (CSS) ----------
st.html(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Tiêu đề chính Gradient */
    .hero-container {
        padding: 1.5rem 0 1rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
        border: 1px solid rgba(129, 140, 248, 0.35);
        color: #a5b4fc;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.5rem;
    }

    /* Thẻ Metrics Hiện Đại */
    .metric-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.75) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.25s ease, border-color 0.25s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.35rem;
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Stepper Container & Animations */
    .stepper-container {
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
        margin: 1.5rem 0;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 1rem 1.25rem;
        animation: slideInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    .step-item.active {
        border-color: rgba(99, 102, 241, 0.6);
        background: linear-gradient(145deg, rgba(49, 46, 129, 0.35) 0%, rgba(30, 27, 75, 0.4) 100%);
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.25);
        animation: slideInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards, pulseBorder 2s infinite ease-in-out;
    }
    .step-item.completed {
        border-color: rgba(16, 185, 129, 0.3);
    }

    .step-icon-box {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
        flex-shrink: 0;
    }
    .step-item.completed .step-icon-box {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .step-item.active .step-icon-box {
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.5);
    }
    .step-title {
        font-weight: 600;
        font-size: 0.96rem;
        color: #f1f5f9;
        margin: 0;
    }
    .step-status {
        margin-left: auto;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
    }
    .status-running {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .status-done {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .step-item.skipped {
        border-color: rgba(245, 158, 11, 0.35);
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.5) 0%, rgba(20, 20, 20, 0.5) 100%);
    }
    .step-item.skipped .step-icon-box {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .status-skipped {
        background: rgba(245, 158, 11, 0.15);
        color: #fcd34d;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }

    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    @keyframes pulseBorder {
        0%, 100% { border-color: rgba(99, 102, 241, 0.4); }
        50% { border-color: rgba(129, 140, 248, 0.85); box-shadow: 0 0 20px rgba(99, 102, 241, 0.35); }
    }
    @keyframes spinner {
        to { transform: rotate(360deg); }
    }
    .spinner-svg {
        animation: spinner 0.9s linear infinite;
    }
    </style>
    """
)

# ---------- HEADER ----------
st.html(
    """
    <div class="hero-container">
        <span class="hero-badge">AI Agent Quality & Guardrails</span>
        <h1 class="hero-title">Exam Quality & Bloom's Auditor</h1>
        <p class="hero-subtitle">Hệ thống thẩm định hình thức đề thi đa tầng và định mức nhận thức Thang đo Bloom tự động</p>
    </div>
    """
)

# ---------- THANH BÊN (SIDEBAR) ----------
with st.sidebar:
    st.markdown("### ⚙️ Cài đặt Agent")
    dung_bloom = st.checkbox("Dùng GPT phân loại Bloom (💰 tốn token)", value=False)
    mat_khau = os.getenv("DEMO_PASSWORD", "")
    if dung_bloom and mat_khau:
        nhap = st.text_input("Mật khẩu demo (để dùng GPT)", type="password")
        if nhap != mat_khau:
            st.warning("Nhập đúng mật khẩu để bật GPT.")
            dung_bloom = False

    st.markdown(f"**Mô hình LLM:** `{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}`")
    st.info(
        "💡 **Chế độ kiểm tra:**\n\n"
        "• **Tắt GPT:** Chạy kiểm định quy chế miễn phí (0 token, 0 đồng).\n\n"
        "• **Bật GPT:** Chỉ những câu đạt chuẩn kỹ thuật mới gửi sang GPT gán nhãn Bloom."
    )

# ---------- KHU VỰC TẢI FILE ----------
up = st.file_uploader("📥 Chọn hoặc kéo thả file đề thi (.docx hoặc .xlsx)", type=["docx", "xlsx"])

with st.expander("📌 Hướng dẫn định dạng file đề thi chuẩn"):
    st.markdown(
        """
**1. Cấu trúc câu hỏi trong file Word (`.docx`):**
- Mỗi câu bắt đầu bằng: `Câu 1. <Nội dung câu hỏi>`
- Các phương án trên từng dòng riêng: `A. ...`, `B. ...`, `C. ...`, `D. ...`
- Đáp án ở dòng riêng: `Đáp án: A` (hoặc `Đáp án: A, C` nếu nhiều đáp án)

**2. Quy định số đáp án:**
- **Mặc định:** Hệ thống mặc định mỗi câu hỏi chỉ có **1 đáp án đúng**.
- **Nếu là câu hỏi chọn nhiều đáp án:** Thân câu hỏi **bắt buộc có ghi chú trong ngoặc**, ví dụ:
  - `Câu 1. Giao thức nào hoạt động ở tầng Transport? (chọn 2 đáp án)`
  - `Câu 2. Các hệ điều hành mã nguồn mở gồm: (chọn 3 đáp án)`
  - `Câu 3. Thiết bị nào thuộc nhóm đầu ra? (chọn nhiều đáp án)`
- *Lưu ý:* Nếu không ghi `(chọn ... đáp án)` trong ngoặc mà câu có từ 2 đáp án trở lên, hệ thống sẽ đánh lỗi `NHIEU_DAP_AN`.
        """
    )

# Metadata icon và tên chuẩn cho 6 bước
STEP_CONFIG = {
    1: {"icon": "📥", "name": "Tiếp nhận & Xác thực file đề thi"},
    2: {"icon": "🔍", "name": "Bóc tách câu hỏi & phương án (Tool 1: File Parser)"},
    3: {"icon": "⚖️", "name": "Quét lỗi hình thức & quy chế (Tool 2: Rule Validator)"},
    4: {"icon": "🧠", "name": "Phân loại Thang đo Bloom (Tool 3: Bloom Evaluator)"},
    5: {"icon": "🛡️", "name": "Ghi Database & Xác minh Read-after-Write (Tool 4 & 5)"},
    6: {"icon": "📊", "name": "Tổng hợp kết quả & Xuất báo cáo kiểm định"}
}

def render_steps_ui(placeholder, completed_steps, current_step_info, dung_bloom: bool = False):
    """Render giao diện các bước với animation trực quan."""
    html = ['<div class="stepper-container">']
    
    # Render các bước đã hoàn thành
    for s_num in completed_steps:
        cfg = STEP_CONFIG.get(s_num, {"icon": "✓", "name": f"Bước {s_num}"})
        if s_num == 4 and not dung_bloom:
            html.append(f"""
            <div class="step-item skipped">
                <div class="step-icon-box">⏭</div>
                <div>
                    <p class="step-title">{cfg['icon']} {cfg['name']}</p>
                    <div style="font-size: 0.8rem; color: #fbbf24; margin-top: 2px;">Không thể đo do chưa bật tính năng AI (chế độ tiết kiệm token)</div>
                </div>
                <span class="step-status status-skipped">Chưa bật AI</span>
            </div>
            """)
        else:
            html.append(f"""
            <div class="step-item completed">
                <div class="step-icon-box">✓</div>
                <div>
                    <p class="step-title">{cfg['icon']} {cfg['name']}</p>
                </div>
                <span class="step-status status-done">Hoàn thành</span>
            </div>
            """)

    # Render bước đang chạy (hiện tại)
    if current_step_info:
        s_num, msg = current_step_info
        cfg = STEP_CONFIG.get(s_num, {"icon": "⚙️", "name": f"Bước {s_num}"})
        spinner_svg = """
        <svg class="spinner-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke-linecap="round"/>
        </svg>
        """
        if s_num == 4 and not dung_bloom:
            html.append(f"""
            <div class="step-item skipped">
                <div class="step-icon-box">⏭</div>
                <div>
                    <p class="step-title">{cfg['icon']} {cfg['name']}</p>
                    <div style="font-size: 0.8rem; color: #fbbf24; margin-top: 2px;">{msg}</div>
                </div>
                <span class="step-status status-skipped">Bỏ qua (Chưa bật AI)</span>
            </div>
            """)
        else:
            html.append(f"""
            <div class="step-item active">
                <div class="step-icon-box">{spinner_svg}</div>
                <div>
                    <p class="step-title">{cfg['icon']} {cfg['name']}</p>
                    <div style="font-size: 0.8rem; color: #a5b4fc; margin-top: 2px;">{msg}</div>
                </div>
                <span class="step-status status-running">Đang xử lý</span>
            </div>
            """)
        
    html.append('</div>')
    placeholder.html("\n".join(html))


if st.button("🚀 Chạy kiểm định", type="primary", disabled=up is None):
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    path = Path("data/uploads") / up.name
    path.write_bytes(up.getbuffer())

    # Khung chứa Stepper có animation
    progress_bar = st.progress(0)
    stepper_placeholder = st.empty()

    step_tracker = {"current": None, "completed": []}

    def on_step_callback(msg: str):
        # Tìm số bước dạng 'Bước X/6'
        m = re.search(r"Bước\s+(\d+)/6", msg)
        if m:
            step_num = int(m.group(1))
            cur = step_tracker["current"]
            if cur and cur[0] not in step_tracker["completed"]:
                step_tracker["completed"].append(cur[0])
            step_tracker["current"] = (step_num, msg)
            progress_bar.progress(int((step_num - 1) / 6.0 * 100))
        else:
            if step_tracker["current"]:
                step_tracker["current"] = (step_tracker["current"][0], msg)

        render_steps_ui(stepper_placeholder, step_tracker["completed"], step_tracker["current"], dung_bloom=dung_bloom)
        time.sleep(0.1)

    # Thực thi kiểm định
    kq = run_audit(
        str(path),
        dung_bloom=dung_bloom,
        on_step=on_step_callback,
    )

    # Khi xong toàn bộ
    cur = step_tracker["current"]
    if cur and cur[0] not in step_tracker["completed"]:
        step_tracker["completed"].append(cur[0])
    progress_bar.progress(100)
    render_steps_ui(stepper_placeholder, step_tracker["completed"], None, dung_bloom=dung_bloom)

    st.session_state["kq"] = kq


# ---------- HIỂN THỊ KẾT QUẢ KIỂM ĐỊNH ----------
kq = st.session_state.get("kq")
if kq:
    st.markdown("---")
    if not kq["hoan_thanh"]:
        st.error(f"❌ Kiểm định không hoàn thành: {kq.get('ly_do')}")
        st.json(kq.get("verify", {}))
    else:
        th = kq["tong_hop_trang_thai"]
        
        # Grid thẻ Metric màu sắc sang trọng
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.html(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #818cf8;">{kq["tong_so_cau"]}</div>
                    <div class="metric-label">Tổng số câu</div>
                </div>
                """
            )
        with c2:
            st.html(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #34d399;">{th.get("APPROVED", 0)}</div>
                    <div class="metric-label">✅ Đạt chuẩn</div>
                </div>
                """
            )
        with c3:
            st.html(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #f87171;">{th.get("NEEDS_EDIT", 0)}</div>
                    <div class="metric-label">❌ Cần sửa lại</div>
                </div>
                """
            )
        with c4:
            st.html(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #fbbf24;">{th.get("NEEDS_MANUAL_REVIEW", 0)}</div>
                    <div class="metric-label">👀 Chờ xem lại</div>
                </div>
                """
            )
        with c5:
            st.html(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #38bdf8; font-size: 1.5rem; margin-top: 5px;">
                        {kq['token']['vao']}/{kq['token']['ra']}
                    </div>
                    <div class="metric-label">Token (Vào/Ra)</div>
                </div>
                """
            )

        st.html("<div style='height: 1rem;'></div>")

        st.success(
            f"🛡️ **Guardrail Verified (Read-after-Write):** Đã lưu thành công "
            f"**{kq['verify']['so_doc_duoc']}** bản ghi vào CSDL và xác minh đối chiếu khớp 100% "
            f"(Mã Batch: `{kq['batch_id']}`)"
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

        st.subheader("📋 Bảng chi tiết kiểm định")
        st.dataframe(df, width="stretch", hide_index=True)

        st.subheader("📊 Ma trận độ khó đề thi theo Thang đo Bloom")
        
        bloom_counts = kq.get("ma_tran_bloom", {})
        if bloom_counts:
            # 4 cột thống kê 4 mức Bloom
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("🧠 Nhớ (NHO)", bloom_counts.get("NHO", 0))
            b2.metric("💡 Hiểu (HIEU)", bloom_counts.get("HIEU", 0))
            b3.metric("⚡ Vận dụng (VAN_DUNG)", bloom_counts.get("VAN_DUNG", 0))
            b4.metric("🔬 Phân tích (PHAN_TICH)", bloom_counts.get("PHAN_TICH", 0))

            # Biểu đồ phân bổ
            st.bar_chart(pd.Series(bloom_counts, name="Số câu"))
        else:
            st.info(
                "ℹ️ **Chưa có dữ liệu Ma trận Bloom:** Bạn đang chạy ở chế độ kiểm định hình thức miễn phí (chưa bật AI). "
                "Để kích hoạt phân tích độ khó và xem biểu đồ ma trận Bloom, hãy tích chọn **'Dùng GPT phân loại Bloom'** ở thanh bên trái trước khi bấm chạy."
            )

        # Xuất file báo cáo
        buf = BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl")
        d1, d2 = st.columns(2)
        d1.download_button(
            "⬇️ Tải báo cáo Excel (.xlsx)",
            buf.getvalue(),
            "bao_cao_kiem_dinh.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        d2.download_button(
            "⬇️ Tải báo cáo CSV (.csv)",
            df.to_csv(index=False).encode("utf-8-sig"),
            "bao_cao_kiem_dinh.csv",
            "text/csv",
            use_container_width=True
        )

        with st.expander("🔎 Xem chi tiết nhật ký thực thi của Agent (JSONL)"):
            st.json(kq["log"])