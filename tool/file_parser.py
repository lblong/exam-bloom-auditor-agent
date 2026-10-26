import re
from pathlib import Path
from typing import List

import pandas as pd
from docx import Document

from models import Question

RE_CAU = re.compile(r"^C[âa]u\s*(\d+)\s*[\.\:\)]\s*(.*)", re.IGNORECASE)
RE_PA = re.compile(r"^([A-J])\s*[\.\)]\s*(.*)")
RE_DAP_AN = re.compile(r"^[ĐD][áa]p\s*[áa]n\s*[:\-]?\s*(.*)", re.IGNORECASE)


def doc_dap_an(phan_sau):
    """'A' -> 'A'; 'A, C' / 'A và C' / 'AC' -> 'A,C'; không đọc được -> None"""
    doan = re.split(r"[.(]", phan_sau)[0].upper()
    cac_chu = []
    for p in re.split(r"[^A-ZÀ-Ỹ]+", doan):
        if not p or p in ("VÀ", "AND"):
            continue
        if re.fullmatch(r"[A-Z]{1,6}", p):
            cac_chu.extend(p)
        else:
            break
    return ",".join(sorted(set(cac_chu))) or None


def parse_lines(lines):
    questions, current = [], None
    dang_o = "than"   # than (thân câu hỏi) -> pa (đang đọc phương án) -> xong (đã gặp Đáp án)
    chu_cuoi = ""
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        m = RE_CAU.match(line)
        if m:
            current = Question(so_cau=int(m.group(1)), than_cau_hoi=m.group(2).strip())
            questions.append(current)
            dang_o, chu_cuoi = "than", ""
            continue
        if current is None or dang_o == "xong":
            continue   # chưa vào câu nào, hoặc đang là phần giải thích sau Đáp án

        m = RE_DAP_AN.match(line)
        if m:
            current.dap_an_dung = doc_dap_an(m.group(1))
            dang_o = "xong"
            continue

        m = RE_PA.match(line)
        if m and m.group(1) > chu_cuoi:   # chỉ nhận chữ cái tăng dần: A, B, C...
            current.phuong_an[m.group(1)] = m.group(2).strip()
            chu_cuoi = m.group(1)
            dang_o = "pa"
            continue

        # Dòng không khớp gì: nối vào phương án cuối (nếu đang đọc phương án) hoặc thân câu hỏi
        if dang_o == "pa":
            current.phuong_an[chu_cuoi] = (current.phuong_an[chu_cuoi] + " " + line).strip()
        else:
            current.than_cau_hoi += " " + line
    return questions


def parse_docx(path):
    return parse_lines([p.text for p in Document(path).paragraphs])


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