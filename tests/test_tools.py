"""工具注册表：schema 生成、白名单过滤、统一调用。"""
from app.tools import registry


def test_account_score_schema_is_valid_function():
    schema = registry.schema_for("account_score")
    assert schema["type"] == "function"
    fn = schema["function"]
    assert fn["name"] == "account_score"
    assert "properties" in fn["parameters"]
    assert "amount_high" in fn["parameters"]["properties"]


def test_tools_for_filters_unknown_keys():
    specs = registry.tools_for(["account_score", "definitely_not_a_tool", "hello"])
    names = [s["function"]["name"] for s in specs]
    assert names == ["account_score", "hello"]


def test_invoke_account_score_returns_total():
    ok, out = registry.invoke(
        "account_score",
        {"amount_high": 3000, "pay_rate": 20, "read_high": 20000,
         "days_on_board": 5, "board_types": 2, "fans": 800},
    )
    assert ok is True
    assert out["total"] == 0.5425


def test_invoke_unknown_tool_returns_error_flag():
    ok, out = registry.invoke("ghost", {})
    assert ok is False
    assert "error" in out