"""初始化数据种子：管理员、风控默认、8 个榜单入口。幂等，可反复执行。"""
from __future__ import annotations

__all__ = ["init_db", "ensure_admin", "seed_risk_config", "seed_ranking_sources", "seed_agent_defs"]

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.prompts import AGENT_PROMPTS
from app.core.config import get_settings
from app.core.security import hash_password
from app.models import AgentDef, RankingSource, RiskConfig, User
from app.models import init_tables
from app.core import SessionLocal

# 各 Agent 的工具白名单（工具实现随里程碑陆续注册；未注册的 key 会被 tools_for 安全忽略）
AGENT_TOOL_KEYS: dict[str, list[str]] = {
    "qianfan_collector": [],  # 浏览器采集工具在 M0 采集里程碑接入
    "account_analyzer": ["account_score", "agent_log", "now"],
    "note_analyzer": ["agent_log"],
    "content_generator": ["agent_log"],
    "content_reviewer": ["agent_log"],
}

AGENT_MODEL = "gpt-4o"

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


def seed_agent_defs(db: Session) -> None:
    """幂等播种子 Agent 定义：提示词在 emits 模块，模型与工具白名单此处配置。"""
    descriptions = {
        "qianfan_collector": "千帆榜单采集",
        "account_analyzer": "账号分析（评分）",
        "note_analyzer": "单篇笔记拆解",
        "content_generator": "日更内容生成",
        "content_reviewer": "内容审查",
    }
    for key, prompt in AGENT_PROMPTS.items():
        exists = db.scalar(select(AgentDef).where(AgentDef.key == key))
        if exists:
            continue
        db.add(
            AgentDef(
                key=key,
                name=descriptions.get(key, key),
                system_prompt=prompt,
                tool_keys=AGENT_TOOL_KEYS.get(key, []),
                model=AGENT_MODEL,
                temperature=0.2,
                is_enabled=True,
            )
        )


def init_db() -> None:
    """幂等初始化：所有子函数都以「不存在才插入」为前提。"""
    db = SessionLocal()
    init_tables()
    # seed_risk_config(db)
    # seed_ranking_sources(db)
    # seed_agent_defs(db)
    ensure_admin(db)
    db.commit()