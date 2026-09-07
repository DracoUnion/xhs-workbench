"""评分服务：按 PRD 4.1.3 手算校验。"""
from app.services.scoring import score_from_ranges


def test_prd_example_boosted_low_fans():
    # 成交 1000-5000→0.30；转化 15-25%→0.55；阅读 1w-10w→0.30
    # evidence = 0.30*0.5 + 0.55*0.35 + 0.30*0.15 = 0.3875
    # trust = 1 + (5/10)*0.25 + (2/4)*0.25 = 1.25
    # low = 1 + (1000-800)/1000*0.6 = 1.12
    # total = 0.3875 * 1.25 * 1.12 = 0.5425
    r = score_from_ranges(
        amount_low=None, amount_high=3000, pay_rate=20,
        read_low=None, read_high=20_000,
        days_on_board=5, board_types=2, fans=800,
    )
    assert r.evidence_score == 0.3875
    assert r.trust_bonus == 1.25
    assert r.low_fans_bonus == 1.12
    assert r.total == 0.5425


def test_max_buckets_no_low_fans():
    # 三高桶 + 10 天 4 类榜 + 5k 粉（无低粉加成）
    # evidence = 1.0；trust = 1 + 0.25 + 0.25 = 1.5；low = 1.0 → total = 1.5
    r = score_from_ranges(
        amount_low=60_000, amount_high=None, pay_rate=80,
        read_low=1_000_000, read_high=None,
        days_on_board=10, board_types=4, fans=5000,
    )
    assert r.total == 1.5


def test_weak_evidence():
    # 100 元→0.10；转化 2%→0.10；阅读 5k→0.10
    # evidence = 0.10；trust = 1；low = 1 + 100/1000*0.6 = 1.06 → total = 0.106
    r = score_from_ranges(
        amount_low=100, amount_high=None, pay_rate=2,
        read_low=None, read_high=5000,
        days_on_board=0, board_types=0, fans=900,
    )
    assert r.evidence_score == 0.10
    assert round(r.total, 4) == 0.106


def test_fans_none_means_no_bonus():
    r = score_from_ranges(
        amount_low=None, amount_high=3000, pay_rate=20,
        read_low=None, read_high=20_000,
        days_on_board=5, board_types=2, fans=None,
    )
    assert r.low_fans_bonus == 1.0