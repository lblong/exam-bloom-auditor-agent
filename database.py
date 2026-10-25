from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine("sqlite:///data/exam_bank.db")
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class QuestionRecord(Base):
    __tablename__ = "question_bank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    so_cau: Mapped[int] = mapped_column(Integer)
    than_cau_hoi: Mapped[str] = mapped_column(Text, default="")
    phuong_an: Mapped[str] = mapped_column(Text, default="{}")      # JSON dạng chuỗi
    dap_an_dung: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    trang_thai: Mapped[str] = mapped_column(String(32))
    loi: Mapped[str] = mapped_column(Text, default="[]")            # JSON dạng chuỗi
    muc_bloom: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ly_do_bloom: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    do_tin_cay: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


def init_db():
    Base.metadata.create_all(engine)