"""Production 上下文：对标资料、网站/工具开发资产。"""
from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import PKMixin, TimestampMixin
from app.core.database import Base


class Material(PKMixin, TimestampMixin, Base):
    """对标资料原文件 + 解析后的全文。"""

    __tablename__ = "materials"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255))
    mime: Mapped[str | None] = mapped_column(String(64))
    local_path: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    parsed_text: Mapped[str | None] = mapped_column(Text)
    # pending|done|failed
    ingest_status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'pending'"))

    __table_args__ = (Index("ix_materials_product", "product_id"),)


class DesignDoc(PKMixin, TimestampMixin, Base):
    """网站/小程序/工具开发路径：阶段推进 + 验收。"""

    __tablename__ = "design_docs"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    # requirements|prototype|ui|logic|accept
    stage: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'requirements'"))
    page_list: Mapped[list | None] = mapped_column(JSON)
    proto_images: Mapped[list | None] = mapped_column(JSON)
    repo_url: Mapped[str | None] = mapped_column(Text)
    build_path: Mapped[str | None] = mapped_column(Text)
    accept_report: Mapped[dict | None] = mapped_column(JSON)

    __table_args__ = (Index("ix_design_docs_product", "product_id"),)