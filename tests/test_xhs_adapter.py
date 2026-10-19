"""xhs-cli 适配器离线测试：不安装 camoufox、不访问网络。"""
from __future__ import annotations

import pytest

from core.exceptions import AppError
from adapters.xhs.auth import cookie_str_to_dict
from adapters.xhs.bridge import (
    XhsSessionError,
    client_session,
    has_login_cookies,
    normalize_note,
    translate_error,
    current_cookie_dict,
    cookie_status,
)
from adapters.xhs.client import XhsClient
from adapters.xhs.exceptions import DataFetchError, LoginError


def test_vendored_modules_import_without_browser_deps():
    # 顶部无浏览器依赖；能走到这里即证明 client/auth 模块可脱离 camoufox 导入。
    from adapters.xhs import client as _c  # noqa: F401
    from adapters.xhs import auth as _a  # noqa: F401


def test_client_session_requires_login_cookies():
    # 显式缺 web_session → 直接拒绝；不依赖本机是否已有保存的 cookie。
    with pytest.raises(XhsSessionError):
        with client_session(cookies={"a1": "a"}):
            pass


def test_client_session_with_valid_cookies_creates_http_client():
    with client_session(cookies={"a1": "a", "web_session": "b"}) as client:
        assert isinstance(client, XhsClient)


def test_cookie_str_to_dict():
    raw = "a1=alpha; b = 1 ; web_session=x_y"
    assert cookie_str_to_dict(raw) == {"a1": "alpha", "b": "1", "web_session": "x_y"}


def test_required_cookies():
    assert has_login_cookies({"a1": "a", "web_session": "b"}) is True
    assert has_login_cookies({"a1": "a"}) is False
    assert has_login_cookies({}) is False  # 显式空登录态


def test_translate_login_error_to_session_error():
    err = translate_error(LoginError("bad cookie"))
    assert isinstance(err, AppError)
    assert err.code == "XHS_AUTH_REQUIRED"


def test_translate_fetch_error_to_recoverable():
    err = translate_error(DataFetchError("page lacked data"))
    assert isinstance(err, AppError)
    assert getattr(err, "code", "XHS_OPERATION_FAILED") == "XHS_DATA_FETCH_FAILED"


def test_normalize_note_camel_and_snake():
    camel = {
        "noteId": "n1",
        "title": "标题",
        "desc": "正文",
        "type": "normal",
        "user": {"nickname": "作者", "userId": "u1"},
        "interactInfo": {"likedCount": 10, "collectedCount": 5, "commentCount": 2},
        "imageList": [{"urlDefault": "https://a/b.jpg"}, "https://c/d.jpg"],
    }
    out = normalize_note(camel, keyword="考研")
    assert out["note_id"] == "n1"
    assert out["author"] == "作者"
    assert out["media_type"] == "image"
    assert len(out["images"]) == 2
    assert out["images"][1]["seq"] == 1
    assert out["interactions"]["likes"] == 10

    snake = {
        "note_id": "n2",
        "title": "t",
        "type": "video",
        "user_id": "u2",
        "interact_info": {"liked_count": 7},
        "image_list": [{"url": "https://x/y.jpg"}],
    }
    out2 = normalize_note(snake)
    assert out2["note_id"] == "n2"
    assert out2["media_type"] == "video"


def test_normalize_note_api_note_card_shape():
    # 新 HTTP API 列表项形状：items[].note_card 嵌套。
    api_item = {
        "id": "n3",
        "xsec_token": "tok",
        "note_card": {
            "note_id": "n3",
            "display_title": "API 标题",
            "desc": "API 正文",
            "type": "video",
            "user": {"nickname": "API 作者", "user_id": "u3"},
            "interact_info": {"liked_count": "3", "collected_count": "4", "comment_count": "5"},
            "image_list": [{"url_default": "https://api/a.jpg"}],
        },
    }
    out = normalize_note(api_item, keyword="设计")
    assert out["note_id"] == "n3"
    assert out["title"] == "API 标题"
    assert out["author"] == "API 作者"
    assert out["media_type"] == "video"
    assert out["interactions"]["likes"] == "3"
    assert len(out["images"]) == 1
    # feed API 详情：{"items": [{ "note_card": {...} }]}
    detail = {
        "items": [
            {
                "id": "n4",
                "note_card": {
                    "note_id": "n4",
                    "title": "详情",
                    "type": "normal",
                    "interact_info": {"liked_count": 9},
                },
            }
        ]
    }
    out2 = normalize_note(detail)
    assert out2["note_id"] == "n4"
    assert out2["media_type"] == "image"


def test_cookie_status_reflects_empty_config():
    status = cookie_status()
    assert isinstance(status["authenticated"], bool)
    assert set(status["required"]) == {"a1", "web_session"}