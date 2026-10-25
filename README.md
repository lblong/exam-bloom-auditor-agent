# Exam Quality & Bloom's Auditor Agent

Agent kiểm định hình thức đề thi trắc nghiệm và phân loại Thang đo Bloom (Nhớ, Hiểu, Vận dụng, Phân tích).

Demo: (điền link sau khi deploy)

## Luồng hoạt động
Tiếp nhận file → File Parser → Rule Validator → Bloom Evaluator (GPT) → Ghi DB → Đọc lại xác minh (Read-after-Write) → Báo cáo.

## Cài đặt
1. Cài Python 3.12+ rồi chạy: `pip install -r requirements.txt`
2. Copy `.env.example` thành `.env` và điền `OPENAI_API_KEY`
3. Chạy giao diện: `streamlit run app.py`

## Đo KPI
- Tạo bộ test 40 câu: `python build_testset.py`
- Đo KPI 2 (không tốn token): `python evaluate_kpi.py`
- Đo KPI 1 + KPI 2: `python evaluate_kpi.py --bloom`
- Kết quả chính thức bằng GPT-4o nằm trong thư mục `evidence/`

## Ranh giới an toàn
- Không tự sửa hoặc xóa nội dung câu hỏi.
- Không APPROVED nếu chưa qua 100% kiểm tra kỹ thuật.
- Câu mơ hồ hoặc độ tin cậy thấp → NEEDS_MANUAL_REVIEW.
- Ghi xong phải đọc lại DB để xác minh trước khi báo hoàn thành.