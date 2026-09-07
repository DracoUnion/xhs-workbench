"""Content 上下文：关键词、对标笔记、拆解、聚类、Skill、内容包与审查。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.mixins import PKMixin, TimestampMixin
from app.core.database import Base


class Keyword(PKMixin, TimestampMixin, Base):
    __tablename__ = "keywords"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    word: Mapped[str] = mapped_column(String(128), nullable=False)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    a_to_z: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    collect_comments: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    pages_target: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("8"))
    collected_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    __table_args__ = (
        Index("uq_keywords_product_word", "product_id", "word", unique=True),
        Index("ix_keywords_product", "product_id"),
    )


class Note(PKMixin, TimestampMixin, Base):
    """对标笔记。media_type: image|video；analyzed 标记已拆解。"""

    __tablename__ = "notes"

    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"))
    note_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    topics: Mapped[list | None] = mapped_column(JSONB)
    author: Mapped[str | None] = mapped_column(String(128))
    interactions: Mapped[dict | None] = mapped_column(JSONB)  # {likes,collects,comments}
    media_type: Mapped[str] = mapped_column(String(8), nullable=False)
    a_to_z_group: Mapped[str | None] = mapped_column(String(8))
    analyzed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    images: Mapped[list["NoteImage"]] = relationship(back_populates="note", cascade="all, delete-orphan")
    frames: Mapped[list["NoteFrame"]] = relationship(back_populates="note", cascade="all, delete-orphan")

    __table_args__ = (
        Index("uq_notes_product_note", "product_id", "note_id", unique=True),
        # 未拆解队列（Covering 查询常用）
        Index(
            "ix_notes_product_unanalyzed",
            "product_id",
            postgresql_where=text("analyzed = FALSE"),
        ),
    )


class NoteImage(PKMixin, Base):
    __tablename__ = "note_images"

    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    local_path: Mapped[str | None] = mapped_column(Text)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    note: Mapped[Note] = relationship(back_populates="images")

    __table_args__ = (Index("uq_note_images_note_seq", "note_id", "seq", unique=True),)


class NoteFrame(PKMixin, Base):
    __tablename__ = "note_frames"

    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id"), nullable=False)
    ts_sec: Mapped[int | None] = mapped_column(Integer)
    local_path: Mapped[str | None] = mapped_column(Text)

    note: Mapped[Note] = relationship(back_populates="frames")


class Transcript(PKMixin, Base):
    __tablename__ = "transcripts"

    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id"), unique=True, nullable=False)
    engine: Mapped[str] = mapped_column(String(32), nullable=False)  # whisper_local|openai
    text: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB)


class NoteAnalysis(PKMixin, Base):
    """单篇拆解：一次只拆一篇，fields 一一映射。"""

    __tablename__ = "note_analyses"

    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id"), unique=True, nullable=False)
    title_formula: Mapped[str | None] = mapped_column(Text)
    structure: Mapped[str | None] = mapped_column(Text)
    hook_type: Mapped[str | None] = mapped_column(String(16))  # 痛点|疑问|反差|数据|故事|清单
    cover_rule: Mapped[str | None] = mapped_column(Text)
    interaction_feature: Mapped[str | None] = mapped_column(String(32))  # collect_high|comment_high|none
    detail: Mapped[dict | None] = mapped_column(JSONB)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Template(PKMixin, TimestampMixin, Base):
    """模板聚类草稿：同一类 ≥3 篇支撑才可转 Skill。"""

    __tablename__ = "templates"

    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cluster_key: Mapped[str] = mapped_column(String(64), nullable=False)
    supported_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    draft_md: Mapped[str | None] = mapped_column(Text)
    # draft|to_skill|used
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'draft'"))
    note_ids: Mapped[list | None] = mapped_column(JSONB)  # 支撑对标 note 列表

    __table_args__ = (
        Index("uq_templates_product_cluster", "product_id", "cluster_key", unique=True),
    )


class Skill(PKMixin, TimestampMixin, Base):
    """SKILL.md：产品事实白名单 + 文案/图片规范，状态驱动日更。"""

    __tablename__ = "skills"

    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    md: Mapped[str] = mapped_column(Text, nullable=False)
    files_whitelist: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'"))
    # draft|testing|active
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'draft'"))
    # manual|auto
    review_policy: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("'manual'"))
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    versions: Mapped[list["SkillVersion"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("uq_skills_product_name", "product_id", "name", unique=True),)


class SkillVersion(PKMixin, Base):
    __tablename__ = "skill_versions"

    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    md: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    skill: Mapped[Skill] = relationship(back_populates="versions")

    __table_args__ = (Index("uq_skill_versions_pair", "skill_id", "version", unique=True),)


class ContentPackage(PKMixin, TimestampMixin, Base):
    """日更内容包：一次生成 1 个体，经审查流转。"""

    __tablename__ = "content_packages"

    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    topics: Mapped[list | None] = mapped_column(JSONB)
    images: Mapped[list | None] = mapped_column(JSONB)  # [{seq,type:cover|page,path}]
    # draft|reviewing|approved|rejected
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'draft'"))
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    review: Mapped["Review | None"] = relationship(back_populates="package", uselist=False)

    __table_args__ = (
        Index("uq_content_packages_skill_seq", "skill_id", "seq", unique=True),
        Index("ix_content_packages_status", "status"),
    )


class Review(PKMixin, Base):
    """审查记录：独立于生成者，记录 verdict/issues/轮次。"""

    __tablename__ = "reviews"

    content_package_id: Mapped[int] = mapped_column(
        ForeignKey("content_packages.id"), nullable=False
    )
    reviewer_agent_key: Mapped[str] = mapped_column(String(64), nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)  # passed|rejected
    issues: Mapped[list | None] = mapped_column(JSONB)  # [{type,message,ref}]
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # 人工审核记录
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    package: Mapped[ContentPackage] = relationship(back_populates="review")