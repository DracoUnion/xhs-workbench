"""Content 上下文：关键词、对标笔记、拆解、聚类、Skill、内容包与审查。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import TimestampMixin
from app.core.database import Base


class Keyword(TimestampMixin, Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    word: Mapped[str] = mapped_column(String(128), nullable=False, server_default=text("''"))
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    a_to_z: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    collect_comments: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    pages_target: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("8"))
    collected_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    __table_args__ = (
        Index("uq_keywords_product_word", "product_id", "word", unique=True),
        Index("ix_keywords_product", "product_id"),
    )


class Note(TimestampMixin, Base):
    """对标笔记。media_type: image|video；analyzed 标记已拆解。"""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    keyword_id: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))
    note_id: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("''"))
    title: Mapped[str | None] = mapped_column(String(255), server_default=text("''"))
    body: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    topics: Mapped[list | None] = mapped_column(JSON, server_default=text("'[]'"))
    author: Mapped[str | None] = mapped_column(String(128), server_default=text("''"))
    interactions: Mapped[dict | None] = mapped_column(JSON, server_default=text("'{}'"))  # {likes,collects,comments}
    media_type: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("''"))
    a_to_z_group: Mapped[str | None] = mapped_column(String(8), server_default=text("''"))
    analyzed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("uq_notes_product_note", "product_id", "note_id", unique=True),
        # 未拆解队列（Covering 查询常用）
        Index(
            "ix_notes_product_unanalyzed",
            "product_id",
            postgresql_where=text("analyzed = FALSE"),
        ),
    )


class NoteImage(Base):
    __tablename__ = "note_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    url: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    local_path: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    seq: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    __table_args__ = (Index("uq_note_images_note_seq", "note_id", "seq", unique=True),)


class NoteFrame(Base):
    __tablename__ = "note_frames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    ts_sec: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))
    local_path: Mapped[str | None] = mapped_column(Text, server_default=text("''"))


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, server_default=text("0"))
    engine: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("''"))
    content_text: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    meta_data: Mapped[dict | None] = mapped_column(JSON, server_default=text("'{}'"))


class NoteAnalysis(Base):
    """单篇拆解：一次只拆一篇，fields 一一映射。"""

    __tablename__ = "note_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, server_default=text("0"))
    title_formula: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    structure: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    hook_type: Mapped[str | None] = mapped_column(String(16), server_default=text("''"))
    cover_rule: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    interaction_feature: Mapped[str | None] = mapped_column(String(32), server_default=text("''"))
    detail: Mapped[dict | None] = mapped_column(JSON, server_default=text("'{}'"))
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Template(TimestampMixin, Base):
    """模板聚类草稿：同一类 ≥3 篇支撑才可转 Skill。"""

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    cluster_key: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("''"))
    supported_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    draft_md: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    # draft|to_skill|used
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'draft'"))
    note_ids: Mapped[list | None] = mapped_column(JSON, server_default=text("'[]'"))  # 支撑对标 note 列表

    __table_args__ = (
        Index("uq_templates_product_cluster", "product_id", "cluster_key", unique=True),
    )


class Skill(TimestampMixin, Base):
    """SKILL.md：产品事实白名单 + 文案/图片规范，状态驱动日更。"""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    name: Mapped[str] = mapped_column(String(128), nullable=False, server_default=text("''"))
    md: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    files_whitelist: Mapped[list] = mapped_column(JSON, nullable=False, server_default=text("'[]'"))
    rules: Mapped[dict] = mapped_column(JSON, nullable=False, server_default=text("'{}'"))
    # draft|testing|active
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'draft'"))
    # manual|auto
    review_policy: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("'manual'"))
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    __table_args__ = (Index("uq_skills_product_name", "product_id", "name", unique=True),)


class SkillVersion(Base):
    __tablename__ = "skill_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    md: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))
    note: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("uq_skill_versions_pair", "skill_id", "version", unique=True),)


class ContentPackage(TimestampMixin, Base):
    """日更内容包：一次生成 1 个体，经审查流转。"""

    __tablename__ = "content_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    seq: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    title: Mapped[str | None] = mapped_column(String(255), server_default=text("''"))
    body: Mapped[str | None] = mapped_column(Text, server_default=text("''"))
    topics: Mapped[list | None] = mapped_column(JSON, server_default=text("'[]'"))
    images: Mapped[list | None] = mapped_column(JSON, server_default=text("'[]'"))  # [{seq,type:cover|page,path}]
    # draft|reviewing|approved|rejected
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'draft'"))
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    __table_args__ = (
        Index("uq_content_packages_skill_seq", "skill_id", "seq", unique=True),
        Index("ix_content_packages_status", "status"),
    )


class Review(Base):
    """审查记录：独立于生成者，记录 verdict/issues/轮次。"""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_package_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    reviewer_agent_key: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("''"))
    verdict: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("''"))
    issues: Mapped[list | None] = mapped_column(JSON, server_default=text("'[]'"))  # [{type,message,ref}]
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))  # 人工审核记录
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )