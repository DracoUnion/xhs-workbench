"""xhs-cli 适配层。

上游实现通过真实 Camoufox 页面读取 __INITIAL_STATE__，本模块只负责把它
接入本项目的配置、错误体系和领域数据格式，不改变上游采集行为。
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import AppError, RecoverableError, ReviewRequired

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
from .exceptions import CookieError, DataFetchError, LoginError, XhsError


class XhsBrowserUnavailable(AppError):
    default_message = "小红书浏览器依赖未安装，请安装 camoufox 后再使用采集功能"

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
    """返回当前 cookie 文件路径：优先 XHS_COOKIE_FILE 覆盖，否则用上游默认路径。"""
    s = get_settings()
    configured = (s.xhs_cookie_file or os.getenv("XHS_COOKIE_FILE", "")).strip()
    return Path(configured).expanduser() if configured else COOKIE_FILE


def load_cookie_string(*, allow_browser: bool = False) -> str | None:
    """读取 cookie，不默认触发浏览器 cookie 扫描，避免 API 请求产生隐式副作用。"""
    s = get_settings()
    configured = (s.xhs_cookies or os.getenv("XHS_COOKIES", "")).strip()
    if configured:
        return configured
    if allow_browser:
        return get_cookie_string()
    return get_saved_cookie_string()


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
    """将上游异常转换为本项目错误；保留原始异常作为 cause 由调用方记录。"""
    if isinstance(exc, LoginError):
        return XhsSessionError(str(exc))
    if isinstance(exc, CookieError):
        return XhsSessionError(str(exc))
    if isinstance(exc, DataFetchError):
        return RecoverableError(
            message=str(exc), code="XHS_DATA_FETCH_FAILED", details={"source": "xhs-cli"}
        )
    if isinstance(exc, XhsError):
        return RecoverableError(
            message=str(exc), code="XHS_OPERATION_FAILED", details={"source": "xhs-cli"}
        )
    if isinstance(exc, ImportError) and "camoufox" in str(exc).lower():
        return XhsBrowserUnavailable()
    return RecoverableError(message=str(exc), code="XHS_OPERATION_FAILED")


def _ensure_browser_dependency() -> None:
    try:
        import camoufox  # noqa: F401
    except ImportError as exc:
        raise XhsBrowserUnavailable() from exc


@contextmanager
def client_session(
    *, cookies: dict[str, str] | None = None, allow_browser_cookie_extraction: bool = False
) -> Iterator[XhsClient]:
    """创建一个独占的 XhsClient 会话。

    调用者负责通过设备锁/任务锁保证同一时刻只有一个浏览器采集任务。
    """
    _ensure_browser_dependency()
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


def normalize_note(raw: dict[str, Any], *, keyword: str | None = None) -> dict[str, Any]:
    """将 xhs-cli 的多版本字段归一为 notes 表可消费的结构。"""
    note = raw.get("note") if isinstance(raw.get("note"), dict) else raw
    user = _first(note, "user", "author", default={}) or {}
    interact = _first(note, "interactInfo", "interact_info", default={}) or {}
    images = _first(note, "imageList", "image_list", "images", default=[]) or []
    normalized_images: list[dict[str, Any]] = []
    for seq, image in enumerate(images):
        if isinstance(image, str):
            normalized_images.append({"url": image, "seq": seq})
        elif isinstance(image, dict):
            url = _first(image, "url", "urlDefault", "url_default", "originUrl", "origin_url")
            if url:
                normalized_images.append({"url": url, "seq": seq})
    note_id = _first(note, "noteId", "note_id", "id", default="")
    media_type = _first(note, "type", "mediaType", "media_type", default="image")
    if str(media_type).lower() in {"video", "视频"}:
        media_type = "video"
    else:
        media_type = "image"
    return {
        "note_id": str(note_id),
        "keyword": keyword,
        "title": _first(note, "title", "displayTitle", "display_title", default=""),
        "body": _first(note, "desc", "description", "body", default=""),
        "topics": _first(note, "tagList", "tag_list", "topics", default=[]),
        "author": _first(user, "nickname", "name", default=""),
        "author_id": _first(user, "userId", "user_id", "id", default=""),
        "interactions": {
            "likes": _first(interact, "likedCount", "liked_count", "likes", default=0),
            "collects": _first(interact, "collectedCount", "collected_count", "collects", default=0),
            "comments": _first(interact, "commentCount", "comment_count", "comments", default=0),
        },
        "media_type": media_type,
        "images": normalized_images,
        "source": "xhs-cli",
    }


class XhsGateway:
    """面向业务服务的同步网关，封装 XhsClient 生命周期。"""

    def __init__(self, cookies: dict[str, str] | None = None) -> None:
        self.cookies = cookies

    def search_notes(self, keyword: str) -> list[dict[str, Any]]:
        try:
            with client_session(cookies=self.cookies) as client:
                return [normalize_note(item, keyword=keyword) for item in client.search_notes(keyword)]
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
                return [normalize_note(item) for item in client.get_user_posts(user_id)]
        except AppError:
            raise
        except Exception as exc:
            raise translate_error(exc) from exc

    def get_note_comments(
        self, note_id: str, xsec_token: str = "", max_comments: int = 50
    ) -> list[dict[str, Any]]:
        try:
            with client_session(cookies=self.cookies) as client:
                return client.get_note_comments(note_id, xsec_token, max_comments)
        except AppError:
            raise
        except Exception as exc:
            raise translate_error(exc) from exc


def login_by_qrcode() -> dict[str, Any]:
    """交互式登录入口；QR 扫码必须在服务端宿主终端执行。"""
    _ensure_browser_dependency()
    try:
        cookie = qrcode_login()
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