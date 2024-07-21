from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.mssql import TINYINT
from sqlalchemy.dialects.mysql import VARCHAR, TEXT
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column


class OCBase(DeclarativeBase):
    __abstract__ = True

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return cls.__name__.lower()


class OCCategory(OCBase):
    __tablename__ = 'oc_category'
    category_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    image: Mapped[None | str] = mapped_column(VARCHAR(255))
    parent_id: Mapped[int]
    top: Mapped[int] = mapped_column(TINYINT)
    column: Mapped[int]
    sort_order: Mapped[int]
    status: Mapped[int] = mapped_column(TINYINT)
    date_added: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    date_modified: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())


class OCCategoryDescription(OCBase):
    __tablename__ = 'oc_category_description'
    category_id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    description: Mapped[str] = mapped_column(TEXT)
    meta_title: Mapped[str] = mapped_column(VARCHAR(255))
    meta_h1: Mapped[str] = mapped_column(VARCHAR(255))
    meta_description: Mapped[str] = mapped_column(VARCHAR(255))
    meta_keyword: Mapped[str] = mapped_column(VARCHAR(255))


class OCCategoryPath(OCBase):
    __tablename__ = 'oc_category_path'
    category_id: Mapped[int] = mapped_column(primary_key=True)
    path_id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[int]


class OCCategoryLayout(OCBase):
    __tablename__ = 'oc_category_to_layout'
    category_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(primary_key=True)
    layout_id: Mapped[int]


class OCCategoryStore(OCBase):
    __tablename__ = 'oc_category_to_store'
    category_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(primary_key=True)
