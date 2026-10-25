import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from models import Question, BloomLLMOutput, BloomResult

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Bạn là chuyên gia khảo thí đại học, phân loại câu hỏi trắc nghiệm theo Thang đo Bloom.
Chỉ dùng ĐÚNG 4 mức sau:

- NHO: câu hỏi yêu cầu nhớ lại, nhận diện sự kiện/định nghĩa/thuật ngữ có sẵn. Từ khóa: là gì, ai, khi nào, kể tên, liệt kê.
- HIEU: yêu cầu giải thích ý nghĩa, cơ chế, nguyên nhân, so sánh, diễn giải bằng lời của mình. Từ khóa: giải thích, vì sao, tóm tắt, phân biệt.
- VAN_DUNG: yêu cầu áp dụng kiến thức vào một tình huống/bài toán cụ thể để giải quyết hoặc chọn giải pháp.
- PHAN_TICH: yêu cầu chia nhỏ vấn đề, tìm mối quan hệ, đánh giá tính hợp lý, phát hiện lỗi hoặc nguyên nhân gốc trong tình huống phức tạp.

Nguyên tắc:
1. Đánh giá mức tư duy mà sinh viên PHẢI dùng để trả lời, dựa trên ngữ nghĩa cả câu, không chỉ dựa vào từ khóa.
2. Không sửa đổi, không nhận xét chuyên môn đúng sai của câu hỏi.
3. Nếu câu hỏi quá mơ hồ, thiếu thông tin hoặc không thể xác định mức, trả về KHONG_XAC_DINH.
4. ly_do: tối đa 2 câu tiếng Việt, nêu rõ vì sao chọn mức đó.
5. do_tin_cay: số thực từ 0.0 đến 1.0 thể hiện mức chắc chắn của bạn."""


def format_question(q: Question) -> str:
    dong = [f"Câu hỏi: {q.than_cau_hoi}"]
    for k in "ABCD":
        if k in q.phuong_an:
            dong.append(f"{k}. {q.phuong_an[k]}")
    if q.dap_an_dung:
        dong.append(f"Đáp án đúng: {q.dap_an_dung}")
    return "\n".join(dong)


def _build_chain():
    llm = ChatOpenAI(model=MODEL, temperature=0, max_retries=2)
    structured = llm.with_structured_output(BloomLLMOutput, include_raw=True)
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", "{noi_dung}")]
    )
    return prompt | structured


def evaluate_question(q: Question, chain=None) -> BloomResult:
    """💰 TỐN TOKEN: mỗi lần gọi hàm này = 1 lần gọi OpenAI."""
    chain = chain or _build_chain()
    try:
        out = chain.invoke({"noi_dung": format_question(q)})
        parsed = out["parsed"]
        if parsed is None:
            raise ValueError(str(out.get("parsing_error")))
        usage = out["raw"].usage_metadata or {}
        return BloomResult(
            so_cau=q.so_cau,
            **parsed.model_dump(),
            model=MODEL,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )
    except Exception as e:
        # Guardrail: lỗi thì KHÔNG đoán bừa, trả về không xác định để chuyển người duyệt
        return BloomResult(
            so_cau=q.so_cau,
            muc_do="KHONG_XAC_DINH",
            ly_do=f"Lỗi khi gọi LLM: {e}",
            do_tin_cay=0.0,
            model=MODEL,
        )


def evaluate_all(questions: List[Question], limit: Optional[int] = None) -> List[BloomResult]:
    """💰 TỐN TOKEN: gọi OpenAI 1 lần cho mỗi câu. Dùng limit để chạy thử vài câu."""
    chain = _build_chain()
    ds = questions[:limit] if limit else questions
    return [evaluate_question(q, chain) for q in ds]