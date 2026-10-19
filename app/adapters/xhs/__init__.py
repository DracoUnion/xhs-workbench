"""小红书 xhs-cli 适配器。

client.py/auth.py/exceptions.py 源自：
https://github.com/jackwener/xhs-cli（Apache License 2.0）。
本项目的桥接与归一化逻辑见 bridge.py。
"""
from app.adapters.xhs.bridge import (
    XhsBrowserUnavailable,
    XhsGateway,
    XhsSessionError,
    client_session,
    clear_cookies,
    cookie_file,
    cookie_status,
    current_cookie_dict,
    has_login_cookies,
    login_by_qrcode,
    normalize_note,
    set_cookie_string,
    translate_error,
)
from app.adapters.xhs.client import XhsClient

__all__ = [
    "XhsClient",
    "XhsGateway",
    "XhsBrowserUnavailable",
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