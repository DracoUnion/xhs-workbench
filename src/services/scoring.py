"""账号评分：严格实现 PRD 4.1.3，纯函数、无数据库/网络副作用。"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence


# 区间采用 [low, high)，high=None 表示无上限。
TRADE_BUCKETS: tuple[tuple[tuple[float, float | None], float], ...] = (
    ((0, 1_000), 0.10),
    ((1_000, 5_000), 0.30),
    ((5_000, 10_000), 0.60),
    ((10_000, 50_000), 1.00),
    ((50_000, None), 1.00),
)
CONV_BUCKETS: tuple[tuple[tuple[float, float | None], float], ...] = (
    ((0, 5), 0.10),
    ((5, 15), 0.30),
    ((15, 25), 0.55),
    ((25, 50), 0.80),
    ((50, 70), 0.95),
    ((70, 90), 1.00),
    ((90, None), 1.00),
)
# PRD 未给出阅读分桶；这是可调的默认映射，实际参数可由配置中心覆盖。
READ_BUCKETS: tuple[tuple[tuple[float, float | None], float], ...] = (
    ((0, 10_000), 0.10),
    ((10_000, 100_000), 0.30),
    ((100_000, 500_000), 0.60),
    ((500_000, None), 1.00),
)


@dataclass(frozen=True)
class ScoreResult:
    trade_score: float
    conv_score: float
    read_score: float
    evidence_score: float
    trust_bonus: float
    low_fans_bonus: float
    total: float
    breakdown: dict

    def as_dict(self) -> dict:
        return asdict(self)


def _bucket_value(
    buckets: Sequence[tuple[tuple[float, float | None], float]], value: float | None
) -> float:
    if value is None:
        return 0.0
    for (low, high), score_value in buckets:
        if value >= low and (high is None or value < high):
            return score_value
    # 负数/异常值不贡献证据分，不抛异常影响整批采集。
    return 0.0


def _representative(low: float | None, high: float | None) -> float | None:
    """把平台返回的区间转为代表值；优先用上界避免低估成交/阅读证据。"""
    return high if high is not None else low


def score(
    trade_score: float,
    conv_score: float,
    read_score: float,
    days_on_board: int,
    board_types: int,
    fans: int | None,
    *,
    breakdown: dict | None = None,
) -> ScoreResult:
    """计算总分：evidence × trust × low-fans，所有输入均做下限保护。"""
    days = max(0, days_on_board)
    types = max(0, board_types)
    evidence = trade_score * 0.50 + conv_score * 0.35 + read_score * 0.15
    trust = 1 + (days / 10) * 0.25 + (types / 4) * 0.25
    low_fans = (
        1 + ((1_000 - fans) / 1_000) * 0.6
        if fans is not None and fans < 1_000
        else 1.0
    )
    result_breakdown = {
        "days_on_board": days,
        "board_types": types,
        "fans": fans,
        **(breakdown or {}),
    }
    return ScoreResult(
        trade_score=round(trade_score, 4),
        conv_score=round(conv_score, 4),
        read_score=round(read_score, 4),
        evidence_score=round(evidence, 4),
        trust_bonus=round(trust, 4),
        low_fans_bonus=round(low_fans, 4),
        total=round(evidence * trust * low_fans, 4),
        breakdown=result_breakdown,
    )


def score_from_ranges(
    amount_low: float | None,
    amount_high: float | None,
    pay_rate: float | None,
    read_low: float | None,
    read_high: float | None,
    days_on_board: int,
    board_types: int,
    fans: int | None,
) -> ScoreResult:
    """把榜单的成交/阅读区间与转化率转换为 PRD 评分。pay_rate 单位为百分比。"""
    amount_value = _representative(amount_low, amount_high)
    read_value = _representative(read_low, read_high)
    return score(
        trade_score=_bucket_value(TRADE_BUCKETS, amount_value),
        conv_score=_bucket_value(CONV_BUCKETS, pay_rate),
        read_score=_bucket_value(READ_BUCKETS, read_value),
        days_on_board=days_on_board,
        board_types=board_types,
        fans=fans,
        breakdown={
            "amount_value": amount_value,
            "pay_rate": pay_rate,
            "read_value": read_value,
        },
    )