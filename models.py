from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Question(BaseModel):
    so_cau: int
    than_cau_hoi: str = ""
    phuong_an: Dict[str, str] = Field(default_factory=dict)  # {"A": "...", "B": "..."}
    dap_an_dung: Optional[str] = None  # "A" / "B" / "C" / "D" hoặc None nếu thiếu

class Issue(BaseModel):
    ma_loi: str
    mo_ta: str


class ValidationResult(BaseModel):
    so_cau: int
    passed: bool
    loi: List[Issue] = Field(default_factory=list)

class BloomLLMOutput(BaseModel):
    """Đây là cấu trúc mà GPT-4o bắt buộc phải trả về."""
    muc_do: Literal["NHO", "HIEU", "VAN_DUNG", "PHAN_TICH", "KHONG_XAC_DINH"]
    ly_do: str
    do_tin_cay: float  # từ 0.0 đến 1.0


class BloomResult(BloomLLMOutput):
    so_cau: int
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0

class VerifyReport(BaseModel):
    ok: bool
    so_ky_vong: int
    so_doc_duoc: int
    sai_lech: List[str] = Field(default_factory=list)