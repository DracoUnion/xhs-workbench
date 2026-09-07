"""初始化数据种子：管理员、风控默认、8 个榜单入口。幂等，可反复执行。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import RankingSource, RiskConfig, User

# 风控 scope 默认延迟区间（秒）：与详细设计 8.3 对齐
RISK_DEFAULTS: dict[str, tuple[int, int]] = {
    "common": (30, 45),
    "ranking": (60, 90),
    "store": (60, 90),
    "search": (60, 90),
    "note": (60, 90),
}

RANKING_SOURCES: list[tuple[str, str]] = [
    ("read_excellent_content", "阅读榜·优秀内容"),
    ("read_excellent_account", "阅读榜·优秀账号"),
    ("drain_excellent_content", "引流榜·优秀内容"),
    ("drain_excellent_account", "引流榜·优秀账号"),
    ("hot_sale_excellent_content", "热卖榜·优秀内容"),
    ("hot_sale_excellent_account", "热卖榜·优秀账号"),
    ("deal_excellent_content", "成交榜·优秀内容"),
    ("deal_excellent_account", "成交榜·优秀账号"),
]


def ensure_admin(db: Session) -> None:
    s = get_settings()
    exists = db.scalar(select(User).where(User.username == s.admin_username))
    if exists:
        return
    db.add(
        User(
            username=s.admin_username,
            password_hash=hash_password(s.admin_password),
            role="admin",
            is_active=True,
        )
    )


def seed_risk_config(db: Session) -> None:
    for scope, (lo, hi) in RISK_DEFAULTS.items():
        exists = db.scalar(select(RiskConfig).where(RiskConfig.scope == scope))
        if exists:
            continue
        db.add(RiskConfig(scope=scope, min_delay_s=lo, max_delay_s=hi, enabled=True))


def seed_ranking_sources(db: Session) -> None:
    for key, name in RANKING_SOURCES:
        exists = db.scalar(select(RankingSource).where(RankingSource.key == key))
        if exists:
            continue
        db.add(RankingSource(key=key, name=name, page_max=20, delay_scope="ranking", enabled=True))


def init_db(db: Session) -> None:
    """幂等初始化：所有子函数都以「不存在才插入」为前提。"""
    seed_risk_config(db)
    seed_ranking_sources(db)
    ensure_admin(db)
    db.commit()