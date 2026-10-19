"""xhs-cli HTTP API 适配层。

XhsClient 使用 xiaohongshu-cli 的签名 HTTP API，不再启动 Camoufox 或导航浏览器页面。
本模块负责接入工作台配置、错误体系、Cookie 生命周期和业务数据归一化。
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from core.config import get_settings
from core.exceptions import AppError, RecoverableError, ReviewRequired

from .auth import (
    COOKIE_FILE,
    REQUIRED_COOKIES,
    _has_required_cookies,
    clear_cookies,
    cookie_str_to_dict,
    get_cookie_string,
    get_saved_cookie_string,
    qrcode_login,
    save_cookies,
)
from .client import XhsClient
from .exceptions import (
    CookieError,
    DataFetchError,
    IpBlockedError,
    LoginError,
    NeedVerifyError,
    SessionExpiredError,
    SignatureError,
    UnsupportedOperationError,
    XhsApiError,
    XhsError,
)


class XhsBrowserUnavailable(AppError):
    """兼容旧调用方的错误类型；HTTP 客户端不再触发该错误。"""

    default_message = "已切换为 HTTP API 客户端，不需要浏览器依赖"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message=message or self.default_message,
            code="XHS_BROWSER_UNAVAILABLE",
        )


class XhsSessionError(AppError):
    default_message = "小红书登录态不可用"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message=message or self.default_message, code="XHS_AUTH_REQUIRED")


def cookie_file() -> Path:
    """返回当前 cookie 文件路径：优先 XHS_COOKIE_FILE 覆盖，否则用工作台默认路径。"""
    s = get_settings()
    configured = (s.xhs_cookie_file or os.getenv("XHS_COOKIE_FILE", "")).strip()
    return Path(configured).expanduser() if configured else COOKIE_FILE


def load_cookie_string(*, allow_browser: bool = False) -> str | None:
    """读取 cookie；allow_browser 仅控制可选的本机浏览器 Cookie 提取。"""
    s = get_settings()
    configured = (s.xhs_cookies or os.getenv("XHS_COOKIES", "")).strip()
    if configured:
        return configured
    if allow_browser:
        cookie = get_cookie_string()
    else:
        cookie = get_saved_cookie_string()
    return cookie


def current_cookie_dict(*, allow_browser: bool = False) -> dict[str, str]:
    cookie = load_cookie_string(allow_browser=allow_browser)
    if not cookie:
        return {}
    return cookie_str_to_dict(cookie)


def has_login_cookies(cookies: dict[str, str] | None = None) -> bool:
    resolved = current_cookie_dict() if cookies is None else cookies
    return _has_required_cookies(resolved)


def cookie_status() -> dict[str, Any]:
    cookies = current_cookie_dict()
    path = cookie_file()
    return {
        "authenticated": _has_required_cookies(cookies),
        "required": sorted(REQUIRED_COOKIES),
        "present": sorted(cookies.keys()),
        "cookie_file": str(path),
        "source": "XHS_COOKIES" if os.getenv("XHS_COOKIES", "").strip() else "file",
    }


def set_cookie_string(cookie: str) -> dict[str, Any]:
    """校验并保存 cookie header，缺少必需登录字段时拒绝。"""
    cookies = cookie_str_to_dict(cookie)
    if not _has_required_cookies(cookies):
        missing = sorted(REQUIRED_COOKIES - cookies.keys())
        raise XhsSessionError(f"cookie 缺少必需字段: {', '.join(missing)}")
    save_cookies(cookie)
    return cookie_status()


def translate_error(exc: Exception) -> AppError:
    """将旧版与 HTTP API 异常统一转换为工作台领域错误。"""
    if isinstance(exc, SessionExpiredError):
        return XhsSessionError(str(exc))
    if isinstance(exc, NeedVerifyError):
        return RecoverableError(
            message=str(exc), code="XHS_NEED_VERIFY", details={"verify_uuid": exc.verify_uuid}
        )
    if isinstance(exc, IpBlockedError):
        return RecoverableError(message=str(exc), code="XHS_IP_BLOCKED")
    if isinstance(exc, SignatureError):
        return RecoverableError(message=str(exc), code="XHS_SIGNATURE_ERROR")
    if isinstance(exc, UnsupportedOperationError):
        return RecoverableError(message=str(exc), code="XHS_UNSUPPORTED_OPERATION")
    if isinstance(exc, XhsApiError):
        return RecoverableError(
            message=str(exc), code="XHS_OPERATION_FAILED", details={"api_code": exc.code}
        )
    if isinstance(exc, LoginError):
        return XhsSessionError(str(exc))
    if isinstance(exc, CookieError):
        return XhsSessionError(str(exc))
    if isinstance(exc, DataFetchError):
        return RecoverableError(
            message=str(exc), code="XHS_DATA_FETCH_FAILED", details={"source": "xhs-cli"}
        )
    if isinstance(exc, XhsError):
        return RecoverableError(message=str(exc), code="XHS_OPERATION_FAILED")
    return RecoverableError(message=str(exc), code="XHS_OPERATION_FAILED")


@contextmanager
def client_session(
    *, cookies: dict[str, str] | None = None, allow_browser_cookie_extraction: bool = False
) -> Iterator[XhsClient]:
    """创建一个独占的 HTTP XhsClient 会话。

    ``allow_browser_cookie_extraction`` 仅允许读取本机已有 Cookie，
    不会启动浏览器页面；数据请求、签名和重试全部走 HTTP API。
    """
    resolved = cookies or current_cookie_dict(allow_browser=allow_browser_cookie_extraction)
    if not _has_required_cookies(resolved):
        raise XhsSessionError("未找到有效登录 cookie，请先设置 cookie 或执行 xhs login")
    client = XhsClient(resolved)
    try:
        with client:
            yield client
    except (AppError, ReviewRequired):
        raise
    except Exception as exc:  # 上游异常统一转换
        raise translate_error(exc) from exc


def _first(mapping: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return default


def _unwrap_note_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract a note object from feed/search/API/HTML response variants."""
    if not isinstance(raw, dict):
        return {}
    items = raw.get("items")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            return _unwrap_note_payload(first)
    note_card = raw.get("note_card")
    if isinstance(note_card, dict):
        return note_card
    note = raw.get("note")
    if isinstance(note, dict):
        return note
    return raw


def normalize_note(raw: dict[str, Any], *, keyword: str | None = None) -> dict[str, Any]:
    """将 HTTP API/HTML 的多版本字段归一为 notes 表可消费的结构。"""
    note = _unwrap_note_payload(raw)
    user = _first(note, "user", "author", default={}) or {}
    interact = _first(note, "interactInfo", "interact_info", default={}) or {}
    images = _first(note, "imageList", "image_list", "images", default=[]) or []
    normalized_images: list[dict[str, Any]] = []
    for seq, image in enumerate(images):
        if isinstance(image, str):
            normalized_images.append({"url": image, "seq": seq})
        elif isinstance(image, dict):
            url = _first(
                image,
                "url",
                "urlDefault",
                "url_default",
                "originUrl",
                "origin_url",
            )
            if url:
                normalized_images.append({"url": url, "seq": seq})
    note_id = _first(note, "noteId", "note_id", "id", default="")
    media_type = _first(note, "type", "mediaType", "media_type", default="image")
    media_type = "video" if str(media_type).lower() in {"video", "视频"} else "image"
    topics = _first(note, "tagList", "tag_list", "topics", default=[]) or []
    normalized_topics = [
        (item.get("name", "") if isinstance(item, dict) else str(item))
        for item in topics
    ]
    return {
        "note_id": str(note_id),
        "keyword": keyword,
        "title": _first(note, "title", "displayTitle", "display_title", default=""),
        "body": _first(note, "desc", "description", "body", default=""),
        "topics": normalized_topics,
        "author": _first(user, "nickname", "name", default=""),
        "author_id": _first(user, "userId", "user_id", "id", default=""),
        "interactions": {
            "likes": _first(interact, "likedCount", "liked_count", "likes", default=0),
            "collects": _first(interact, "collectedCount", "collected_count", "collects", default=0),
            "comments": _first(interact, "commentCount", "comment_count", "comments", default=0),
            "shares": _first(interact, "shareCount", "share_count", "shares", default=0),
        },
        "media_type": media_type,
        "images": normalized_images,
        "source": "xhs-cli",
    }


class XhsGateway:
    """面向业务服务的同步 HTTP 网关，封装 XhsClient 生命周期。"""

    def __init__(self, cookies: dict[str, str] | None = None) -> None:
        self.cookies = cookies

    def search_notes(self, keyword: str) -> list[dict[str, Any]]:
        try:
            with client_session(cookies=self.cookies) as client:
                data = client.search_notes(keyword)
                items = data.get("items", []) if isinstance(data, dict) else data
                return [normalize_note(item, keyword=keyword) for item in items if isinstance(item, dict)]
        except AppError:
            raise
        except Exception as exc:
            raise translate_error(exc) from exc

    def get_note_detail(self, note_id: str, xsec_token: str = "") -> dict[str, Any]:
        try:
            with client_session(cookies=self.cookies) as client:
                return normalize_note(client.get_note_detail(note_id, xsec_token), keyword=None)
        except AppError:
            raise
        except Exception as exc:
            raise translate_error(exc) from exc

    def get_user_info(self, user_id: str) -> dict[str, Any]:
        try:
            with client_session(cookies=self.cookies) as client:
                return client.get_user_info(user_id)
        except AppError:
            raise
        except Exception as exc:
            raise translate_error(exc) from exc

    def get_user_posts(self, user_id: str) -> list[dict[str, Any]]:
        try:
            with client_session(cookies=self.cookies) as client:
                data = client.get_user_notes(user_id)
                notes = data.get("notes", data.get("items", [])) if isinstance(data, dict) else data
                return [normalize_note(item) for item in notes if isinstance(item, dict)]
        except AppError:
            raise
        except Exception as exc:
            raise translate_error(exc) from exc

    def get_note_comments(
        self, note_id: str, xsec_token: str = "", max_comments: int = 50
    ) -> list[dict[str, Any]]:
        try:
            with client_session(cookies=self.cookies) as client:
                data = client.get_all_comments(note_id, xsec_token=xsec_token)
                comments = data.get("comments", []) if isinstance(data, dict) else []
                return comments[:max_comments]
        except AppError:
            raise
        except Exception as exc:
            raise translate_error(exc) from exc


def login_by_qrcode() -> dict[str, Any]:
    """交互式 HTTP QR 登录；不启动 Camoufox。"""
    try:
        cookie = qrcode_login()
    except AppError:
        raise
    except Exception as exc:
        raise translate_error(exc) from exc
    return set_cookie_string(cookie)


__all__ = [
    "XhsBrowserUnavailable",
    "XhsGateway",
    "XhsSessionError",
    "client_session",
    "clear_cookies",
    "cookie_file",
    "cookie_status",
    "current_cookie_dict",
    "has_login_cookies",
    "login_by_qrcode",
    "normalize_note",
    "set_cookie_string",
    "translate_error",
]
