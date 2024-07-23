from datetime import datetime

from sqlalchemy import VARCHAR, SMALLINT, DateTime, func
from sqlalchemy.dialects.mysql import TINYINT, TEXT
from sqlalchemy.dialects.mysql import DECIMAL, MEDIUMINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ProductBase(DeclarativeBase):
    __abstract__ = True


class OCProduct(ProductBase):
    __tablename__ = 'oc_product'
    product_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(VARCHAR(64))
    sku: Mapped[str] = mapped_column(VARCHAR(64))
    upc: Mapped[str] = mapped_column(VARCHAR(12))
    ean: Mapped[str] = mapped_column(VARCHAR(14))
    jan: Mapped[str] = mapped_column(VARCHAR(13))
    isbn: Mapped[str] = mapped_column(VARCHAR(17))
    mpn: Mapped[str] = mapped_column(VARCHAR(64))
    location: Mapped[str] = mapped_column(VARCHAR(128))
    quantity: Mapped[int] = mapped_column(SMALLINT, default=0)
    stock_status_id: Mapped[int]
    image: Mapped[str] = mapped_column(VARCHAR(128))
    manufacturer_id: Mapped[int]
    shipping: Mapped[int] = mapped_column(TINYINT, default=1)
    price: Mapped[float] = mapped_column(DECIMAL(15, 4), default=0.0000)
    points: Mapped[int] = mapped_column(MEDIUMINT, default=0)
    tax_class_id: Mapped[int]
    date_available: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    weight: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0.00)
    weight_class_id: Mapped[int] = mapped_column(default=0)
    length: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0.00)
    width: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0.00)
    height: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0.00)
    length_class_id: Mapped[int] = mapped_column(default=0)
    subtract: Mapped[int] = mapped_column(TINYINT, default=1)
    minimum: Mapped[int] = mapped_column(default=1)
    sort_order: Mapped[int] = mapped_column(default=0)
    status: Mapped[int] = mapped_column(TINYINT, default=0)
    viewed: Mapped[int] = mapped_column(MEDIUMINT, default=0)
    date_added: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    date_modified: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())


class OCProductAttr(ProductBase):
    __tablename__ = 'oc_product_attribute'
    product_id: Mapped[int] = mapped_column(primary_key=True)
    attribute_id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(TEXT)


class OCProductDesc(ProductBase):
    __tablename__ = 'oc_product_description'
    product_id: Mapped[int] = mapped_column(primary_key=True)
    language_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    description: Mapped[str] = mapped_column(TEXT)
    tag: Mapped[str] = mapped_column(TEXT)
    meta_title: Mapped[str] = mapped_column(VARCHAR(255))
    meta_h1: Mapped[str] = mapped_column(VARCHAR(255))
    meta_description: Mapped[str] = mapped_column(VARCHAR(255))
    meta_keyword: Mapped[str] = mapped_column(VARCHAR(255))


class OCProductCategory(ProductBase):
    __tablename__ = 'oc_product_attribute'
    product_id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(primary_key=True)
    main_category: Mapped[int] = mapped_column(TINYINT, default=0)


class OCProductLayout(ProductBase):
    __tablename__ = 'oc_product_to_layout'
    product_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(primary_key=True)
    layout_id: Mapped[int]


class OCProductStore(ProductBase):
    __tablename__ = 'oc_product_to_store'
    product_id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(primary_key=True, default=0)
