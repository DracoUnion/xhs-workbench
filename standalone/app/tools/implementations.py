"""首批确定性工具：冒烟、时间、进度上报、评分。采集类工具在后续里程碑注册。"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.services.scoring import score_from_ranges
from app.tools.registry import tool


class HelloParams(BaseModel):
    name: str = Field(default="world", description="问候对象")


@tool("hello", "问候工具，用于冒烟测试", HelloParams)
def hello(name: str) -> dict:
    return {"greeting": f"hello, {name}"}


class NowParams(BaseModel):
    pass


@tool("now", "返回当前 UTC 时间 ISO 字符串与 Unix 时间戳", NowParams)
def now() -> dict:
    utc = datetime.now(timezone.utc)
    return {"utc": utc.isoformat(), "timestamp": int(utc.timestamp())}


class AgentLogParams(BaseModel):
    step: str = Field(..., description="进度说明文本")


@tool("agent_log", "Agent 上报当前步骤，供前端任务中心展示进度", AgentLogParams)
def agent_log(step: str) -> dict:
    return {"ack": True, "step": step}


class AccountScoreParams(BaseModel):
    amount_low: int | None = Field(default=None, description="成交金额下界（元）")
    amount_high: int | None = Field(default=None, description="成交金额上界（元）")
    pay_rate: float | None = Field(default=None, description="支付转化率（%，0-90）")
    read_low: int | None = Field(default=None, description="阅读量下界")
    read_high: int | None = Field(default=None, description="阅读量上界")
    days_on_board: int = Field(default=0, description="上榜天数")
    board_types: int = Field(default=0, description="进入的榜单类型数")
    fans: int | None = Field(default=None, description="粉丝数")


@tool("account_score", "按 PRD 4.1.3 评分模型计算账号得分", AccountScoreParams)
def account_score(
    amount_low: int | None,
    amount_high: int | None,
    pay_rate: float | None,
    read_low: int | None,
    read_high: int | None,
    days_on_board: int,
    board_types: int,
    fans: int | None,
) -> dict:
    result = score_from_ranges(
        amount_low=amount_low,
        amount_high=amount_high,
        pay_rate=pay_rate,
        read_low=read_low,
        read_high=read_high,
        days_on_board=days_on_board,
        board_types=board_types,
        fans=fans,
    )
    return result.as_dict()


class DedupCheckParams(BaseModel):
    product_id: int = Field(..., description="商品/方向 id")
    fingerprint: str = Field(..., description="指纹（链接/标题哈希）")


@tool("dedup_check", "占位：检查是否已采集过（M1 接入数据库后启用）", DedupCheckParams)
def dedup_check(product_id: int, fingerprint: str) -> dict:
    # TODO(M1): 用 app.models.Dedup 实现真实判重
    return {
        "duplicate": False,
        "note": "dedup_check 尚未接入数据库，当前恒返回不重复，请勿在生产环境依赖此结果",
        "product_id": product_id,
        "fingerprint": fingerprint,
    }