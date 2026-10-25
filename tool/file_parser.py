import re
from pathlib import Path
from typing import List

import pandas as pd
from docx import Document

from models import Question

RE_CAU = re.compile(r"^C[âa]u\s*(\d+)\s*[\.\:\)]\s*(.*)", re.IGNORECASE)
RE_PA = re.compile(r"^([A-D])\s*[\.\)]\s*(.*)")
RE_DAP_AN = re.compile(r"^[ĐD][áa]p\s*[áa]n\s*[:\-]?\s*([A-D])?", re.IGNORECASE)


def parse_docx(path: str) -> List[Question]:
    doc = Document(path)
    questions: List[Question] = []
    current = None

    for para in doc.paragraphs:
        line = para.text.strip()
        if not line:
            continue

        m = RE_CAU.match(line)
        if m:
            current = Question(so_cau=int(m.group(1)), than_cau_hoi=m.group(2).strip())
            questions.append(current)
            continue

        if current is None:
            continue

        m = RE_DAP_AN.match(line)
        if m:
            current.dap_an_dung = m.group(1).upper() if m.group(1) else None
            continue

        m = RE_PA.match(line)
        if m:
            current.phuong_an[m.group(1)] = m.group(2).strip()
            continue

        # Dòng không khớp gì: coi là phần tiếp theo của thân câu hỏi
        current.than_cau_hoi += " " + line

    return questions


def parse_xlsx(path: str) -> List[Question]:
    df = pd.read_excel(path, dtype=str).fillna("")
    questions: List[Question] = []
    for i, row in df.iterrows():
        phuong_an = {}
        for k in ["A", "B", "C", "D"]:
            if k in df.columns and row[k].strip():
                phuong_an[k] = row[k].strip()
        dap_an = row.get("Đáp án", "").strip().upper() or None
        so_cau = int(row["STT"]) if "STT" in df.columns and row["STT"].strip() else i + 1
        questions.append(
            Question(
                so_cau=so_cau,
                than_cau_hoi=row.get("Câu hỏi", "").strip(),
                phuong_an=phuong_an,
                dap_an_dung=dap_an,
            )
        )
    return questions


def parse_file(path: str) -> List[Question]:
    """Tool 1: tự nhận loại file và bóc tách thành danh sách Question."""
    ext = Path(path).suffix.lower()
    if ext == ".docx":
        return parse_docx(path)
    if ext in (".xlsx", ".xls"):
        return parse_xlsx(path)
    raise ValueError(f"Định dạng file không hỗ trợ: {ext}")