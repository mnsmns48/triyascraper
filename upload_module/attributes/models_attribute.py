from sqlalchemy import VARCHAR
from sqlalchemy.dialects.mysql import MEDIUMINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AttrBase(DeclarativeBase):
    __abstract__ = True


class OCAttrGroup(AttrBase):
    __tablename__ = 'oc_attribute_group'
    attribute_group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sort_order: Mapped[int] = mapped_column(MEDIUMINT)


class OCAttrGroupDesc(AttrBase):
    __tablename__ = 'oc_attribute_group_description'
    attribute_group_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    language_id: Mapped[int]
    name: Mapped[str] = mapped_column(VARCHAR(64))


class OCAttr(AttrBase):
    __tablename__ = 'oc_attribute'
    attribute_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attribute_group_id: Mapped[int]
    sort_order: Mapped[int] = mapped_column(MEDIUMINT)


class OCAttrDesc(AttrBase):
    __tablename__ = 'oc_attribute_description'
    attribute_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    language_id: Mapped[int]
    name: Mapped[str] = mapped_column(VARCHAR(64))
