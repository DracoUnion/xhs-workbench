"""ORM 模型注册表：导入所有模型使 Base.metadata 完整，供 Alembic 与查询使用。"""
from app.core.database import Base, engine
from app.models.platform import AppSetting, RiskConfig, User
from app.models.orchestration import AgentDef, AgentRun, Dedup, ReviewPoint
from app.models.discovery import (
    DIRECTION_STATUSES,
    Account,
    AccountMetric,
    Direction,
    DirectionAccount,
    Product,
    ProductImage,
    Ranking,
    RankingSource,
)
from app.models.production import DesignDoc, Material
from app.models.content import (
    ContentPackage,
    Keyword,
    Note,
    NoteAnalysis,
    NoteFrame,
    NoteImage,
    Review,
    Skill,
    SkillVersion,
    Template,
    Transcript,
)

__all__ = [
    "Base",
    "AppSetting",
    "RiskConfig",
    "User",
    "AgentDef",
    "AgentRun",
    "Dedup",
    "ReviewPoint",
    "DIRECTION_STATUSES",
    "Account",
    "AccountMetric",
    "Direction",
    "DirectionAccount",
    "Product",
    "ProductImage",
    "Ranking",
    "RankingSource",
    "DesignDoc",
    "Material",
    "ContentPackage",
    "Keyword",
    "Note",
    "NoteAnalysis",
    "NoteFrame",
    "NoteImage",
    "Review",
    "Skill",
    "SkillVersion",
    "Template",
    "Transcript",
    "init_tables",
]

def init_tables():
    Base.metadata.create_all(engine)