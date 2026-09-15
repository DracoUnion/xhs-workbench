"""Production 上下文：对标资料、网站/工具开发资产。"""
from __future__ import annotations

from sqlalchemy import Integer, Index, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import TimestampMixin
from app.core.database import Base


class Material(TimestampMixin, Base):
    """对标资料原文件 + 解析后的全文。"""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    filename: Mapped[str | None] = mapped_column(String(255), server_default=text("''"))
    mime: Mapped[str | None] = mapped_column(String(64), server_default=text("''"))
    local_path: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    size_bytes: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))
    parsed_text: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    # pending|done|failed
    ingest_status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'pending'"))

    __table_args__ = (Index("ix_materials_product", "product_id"),)


class DesignDoc(TimestampMixin, Base):
    """网站/小程序/工具开发路径：阶段推进 + 验收。"""

    __tablename__ = "design_docs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    # requirements|prototype|ui|logic|accept
    stage: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'requirements'"))
    page_list: Mapped[list | None] = mapped_column(JSON, server_default=text("'[]'"))
    proto_images: Mapped[list | None] = mapped_column(JSON, server_default=text("'[]'"))
    repo_url: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    build_path: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    accept_report: Mapped[dict | None] = mapped_column(JSON, server_default=text("'{}'"))

    __table_args__ = (Index("ix_design_docs_product", "product_id"),)