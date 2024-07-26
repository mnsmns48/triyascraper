from datetime import datetime
from typing import Optional, Any

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.parent = None
        self.id = None

    __abstract__ = True


class TriyaData(Base):
    __tablename__ = 'triyadata_2'
    parsing_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    parent: Mapped[int]
    products: Mapped[Optional[bool]]
    title: Mapped[Optional[str]] = mapped_column(String(length=150))
    title_full: Mapped[Optional[str]] = mapped_column(String(length=200))
    code: Mapped[Optional[int]]
    link: Mapped[Optional[str]] = mapped_column(String(length=200))
    price: Mapped[Optional[int]]
    properties: Mapped[Optional[dict]] = mapped_column(type_=JSON)
    description_text: Mapped[Optional[str]] = mapped_column(type_=MEDIUMTEXT)
    description_props: Mapped[Optional[dict]] = mapped_column(type_=JSON)
    images: Mapped[Optional[dict]] = mapped_column(type_=JSON)
