"""Discovery 上下文：榜单、账号、商品、方向。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import TimestampMixin
from app.core.database import Base


class RankingSource(Base):
    """千帆数据中心 8 个榜单入口配置。"""

    __tablename__ = "ranking_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    page_max: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("20"))
    delay_scope: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'ranking'"))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class Account(TimestampMixin, Base):
    """小红书账号：评分归一到总分，明细存 account_metrics。"""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    xhs_user_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(128))
    fans: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Numeric(10, 4))
    first_seen_board: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    board_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    board_types: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class AccountMetric(Base):
    """评分分项明细，便于看板追溯与调参验证。"""

    __tablename__ = "account_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    trade_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    conv_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    read_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    evidence_score: Mapped[float | None] = mapped_column(Numeric(10, 4))
    trust_bonus: Mapped[float | None] = mapped_column(Numeric(10, 4))
    low_fans_bonus: Mapped[float | None] = mapped_column(Numeric(10, 4))
    total: Mapped[float | None] = mapped_column(Numeric(10, 4))
    breakdown: Mapped[dict | None] = mapped_column(JSON)  # {amount_bucket, conv_bucket,...}


class Ranking(Base):
    """榜单行快照：区间字段存上下界（元/百分比），供评分映射。"""

    __tablename__ = "rankings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(48), nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    note_title: Mapped[str | None] = mapped_column(String(255))
    account_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    read_low: Mapped[int | None] = mapped_column(Integer)
    read_high: Mapped[int | None] = mapped_column(Integer)
    click_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    pay_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    amount_low: Mapped[int | None] = mapped_column(Integer)
    amount_high: Mapped[int | None] = mapped_column(Integer)
    raw: Mapped[dict | None] = mapped_column(JSON)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("uq_rankings_source_page_rank", "source", "page", "rank", unique=True),
        Index("ix_rankings_account", "account_id"),
    )


class Product(TimestampMixin, Base):
    """商品实体。role: candidate=需求发现采集 / self-made=选定自产。"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    xhs_id: Mapped[str | None] = mapped_column(String(64))
    account_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    direction_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255))
    price_cents: Mapped[int | None] = mapped_column(Integer)
    sales: Mapped[int | None] = mapped_column(Integer)
    spec: Mapped[str | None] = mapped_column(Text)
    desc: Mapped[str | None] = mapped_column(Text)
    share_link: Mapped[str | None] = mapped_column(String(255))
    # 产品形态：materials|template|quiz|tutorial|other
    form: Mapped[str | None] = mapped_column(String(32))
    # candidate|self-made
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'candidate'"))
    # collected|detail_done|validated|analyzed|dropped
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'collected'"))

    __table_args__ = (
        Index("uq_products_account_xhs", "account_id", "xhs_id", unique=True),
        Index("ix_products_direction", "direction_id"),
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    local_path: Mapped[str | None] = mapped_column(Text)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    __table_args__ = (
        Index("uq_product_images_product_seq", "product_id", "seq", unique=True),
    )


# DirectionStatus 文案常量（与 PRD/DESIGN 对齐）
DIRECTION_STATUSES = ("观察中", "升温", "已验证", "降温", "放弃")


class Direction(Base):
    """产品方向：品类×形态聚类结果，状态机流转。"""

    __tablename__ = "directions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    form: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'观察中'"))
    evidence: Mapped[str | None] = mapped_column(Text)
    picked_product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class DirectionAccount(Base):
    """方向↔支撑账号的多对多，附带价格区间与最高销量证据。"""

    __tablename__ = "direction_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    direction_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_low: Mapped[int | None] = mapped_column(Integer)
    price_high: Mapped[int | None] = mapped_column(Integer)
    max_sales: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        Index("uq_direction_accounts_pair", "direction_id", "account_id", unique=True),
    )