"""Authentication for Xiaohongshu (HTTP API).

Cookie 持久化与浏览器导入沿用原有逻辑；QR 登录改为纯 HTTP 流程
（复用 XhsClient 的 AuthEndpointsMixin），不再启动 Camoufox 浏览器。
"""

from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path
from typing import Any

from .client import XhsClient
from .exceptions import LoginError

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".xhs-cli"
COOKIE_FILE = CONFIG_DIR / "cookies.json"
# Cache file for xsec_token: maps note_id -> xsec_token so users don't
# need to copy-paste tokens manually after search.
TOKEN_CACHE_FILE = CONFIG_DIR / "token_cache.json"

# a1 is required for signing; web_session is required for a stable logged-in session.
REQUIRED_COOKIES = {"a1", "web_session"}
BROWSER_EXPORT_COOKIE_NAMES = (
    "a1",
    "webId",
    "web_session",
    "web_session_sec",
    "id_token",
    "websectiga",
    "sec_poison_id",
    "xsecappid",
    "gid",
    "abRequestId",
    "webBuild",
    "loadts",
)

QR_SCANNED = 1   # 已扫码，等待确认
QR_CONFIRMED = 2  # 登录确认
QR_POLL_INTERVAL_S = 2.0
QR_POLL_TIMEOUT_S = 240  # 4 分钟


# ---------- Cookie 读取 ----------


def get_saved_cookie_string() -> str | None:
    """Load only saved cookies from local config file.

    This helper never triggers browser extraction and has no write side effects.
    """
    return _load_saved_cookies()


def get_cookie_string() -> str | None:
    """Try all auth methods in order. Returns cookie string or None."""
    # 1. Saved cookies
    cookie = _load_saved_cookies()
    if cookie:
        logger.info("Loaded saved cookies from %s", COOKIE_FILE)
        return cookie

    # 2. 本机浏览器 Cookie 导入（浏览器 cookie3，仅读取，不启动页面）
    cookie = _extract_browser_cookies()
    if cookie:
        logger.info("Extracted cookies from local browser")
        save_cookies(cookie)
        return cookie

    return None


def _load_saved_cookies() -> str | None:
    """Load cookies from saved file."""
    if not COOKIE_FILE.exists():
        return None

    try:
        data = json.loads(COOKIE_FILE.read_text())
        cookies = data.get("cookies", {})
        if _has_required_cookies(cookies):
            return _dict_to_cookie_str(cookies)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to load saved cookies: %s", e)

    return None


def _extract_browser_cookies() -> str | None:
    """从本机浏览器读取小红书 cookie（browser-cookie3 子进程，仅导入不改数据）。"""
    import subprocess
    import sys

    extract_script = '''
import json, sys
try:
    import browser_cookie3 as bc3
except ImportError:
    print(json.dumps({"error": "not_installed"}))
    sys.exit(0)

browsers = [
    ("Chrome", bc3.chrome),
    ("Firefox", bc3.firefox),
    ("Edge", bc3.edge),
    ("Brave", bc3.brave),
]

for name, loader in browsers:
    try:
        cj = loader(domain_name=".xiaohongshu.com")
        cookies = {c.name: c.value for c in cj if "xiaohongshu" in (c.domain or "")}
        if "a1" in cookies and "web_session" in cookies:
            print(json.dumps({"browser": name, "cookies": cookies}))
            sys.exit(0)
    except Exception:
        pass

print(json.dumps({"error": "no_cookies"}))
'''

    try:
        result = subprocess.run(
            [sys.executable, "-c", extract_script],
            capture_output=True, text=True, timeout=15,
        )

        if result.returncode != 0:
            logger.debug("Cookie extraction subprocess failed: %s", result.stderr)
            return None

        data = json.loads(result.stdout.strip())

        if "error" in data:
            if data["error"] == "not_installed":
                logger.warning("browser-cookie3 not installed")
            else:
                logger.debug("No valid cookies found in any browser")
            return None

        cookies = data["cookies"]
        browser = data["browser"]
        logger.info("Found valid cookies in %s (%d cookies)", browser, len(cookies))
        return _dict_to_cookie_str(cookies)

    except subprocess.TimeoutExpired:
        logger.warning("Cookie extraction timed out (browser may be running). "
                       "Try closing your browser or use `xhs login --cookie <string>`")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Cookie extraction parse error: %s", e)
        return None


# ---------- HTTP QR 登录 ----------


def _generate_a1() -> str:
    """Generate a fresh a1 cookie value (24 hex chars + ms timestamp + 15 hex)."""
    prefix = "".join(random.choices("0123456789abcdef", k=24))
    ts = str(int(time.time() * 1000))
    suffix = "".join(random.choices("0123456789abcdef", k=15))
    return prefix + ts + suffix


def _generate_webid() -> str:
    """Generate a webId cookie value (32 hex chars)."""
    return "".join(random.choices("0123456789abcdef", k=32))


def _apply_session_cookies(client: XhsClient, payload: dict[str, Any]) -> None:
    """Persist any session cookies returned by the QR login endpoints."""
    login_info = payload.get("login_info", {})
    if not isinstance(login_info, dict):
        login_info = {}
    session = payload.get("session") or login_info.get("session", "")
    secure_session = payload.get("secure_session") or login_info.get("secure_session", "")
    if session:
        client.cookies["web_session"] = str(session)
    if secure_session:
        client.cookies["web_session_sec"] = str(secure_session)


def _build_saved_cookies(a1: str, webid: str, payload: dict[str, Any]) -> dict[str, str]:
    """Build the cookie payload persisted after QR login succeeds."""
    login_info = payload.get("login_info", {})
    if not isinstance(login_info, dict):
        login_info = {}
    session = payload.get("session") or login_info.get("session") or payload.get("web_session", "")
    secure_session = (
        payload.get("secure_session")
        or login_info.get("secure_session")
        or payload.get("web_session_sec", "")
    )
    cookies = {
        "a1": a1,
        "webId": webid,
    }
    if session:
        cookies["web_session"] = str(session)
    if secure_session:
        cookies["web_session_sec"] = str(secure_session)
    return cookies


def _resolved_user_id(info: dict[str, Any]) -> str:
    """Extract the current user ID from activate/self payloads."""
    if not isinstance(info, dict):
        return ""
    login_info = info.get("login_info")
    if isinstance(login_info, dict) and login_info.get("user_id"):
        return str(login_info["user_id"])
    basic = info.get("basic_info", info)
    if isinstance(basic, dict) and basic.get("user_id"):
        return str(basic["user_id"])
    if info.get("user_id"):
        return str(info["user_id"])
    if info.get("userid"):
        return str(info["userid"])
    return ""


def _complete_confirmed_session(
    client: XhsClient,
    qr_id: str,
    code: str,
    confirmed_user_id: str,
    *,
    retries: int = 5,
    wait_s: float = 1.0,
) -> dict[str, Any]:
    """Finalize QR login after confirmation until the session switches users."""
    last_data: dict[str, Any] = {}
    for attempt in range(retries):
        completion_data = client.complete_qr_login(qr_id, code)
        _apply_session_cookies(client, completion_data)
        last_data = completion_data
        completed_user_id = _resolved_user_id(completion_data)
        self_info_user_id = ""
        try:
            self_info_user_id = _resolved_user_id(client.get_self_info())
        except Exception as exc:
            logger.debug("QR post-confirm self info check failed attempt=%d: %s", attempt + 1, exc)
        if completed_user_id and completed_user_id == confirmed_user_id:
            return last_data
        if self_info_user_id and self_info_user_id == confirmed_user_id:
            return last_data
        if attempt + 1 < retries:
            time.sleep(wait_s)

    raise LoginError(
        "QR 登录已确认，但未获得确认用户会话。"
        f"expected={confirmed_user_id} last={last_data}"
    )


def _render_qr_half_blocks(matrix: list[list[bool]]) -> str:
    """Render QR matrix using half-block characters (▀▄█)."""
    if not matrix:
        return ""

    border = 2
    width = len(matrix[0]) + border * 2
    padded = [[False] * width for _ in range(border)]
    for row in matrix:
        padded.append(([False] * border) + row + ([False] * border))
    padded.extend([[False] * width for _ in range(border)])

    chars = {
        (False, False): " ",
        (True, False): "▀",
        (False, True): "▄",
        (True, True): "█",
    }

    lines = []
    for y in range(0, len(padded), 2):
        top = padded[y]
        bottom = padded[y + 1] if y + 1 < len(padded) else [False] * width
        line = "".join(chars[(top[x], bottom[x])] for x in range(width))
        lines.append(line)
    return "\n".join(lines)


def _display_qr_text_in_terminal(qr_text: str) -> bool:
    """Render QR text as terminal half-block art."""
    try:
        import qrcode
    except ImportError:
        return False

    try:
        qr = qrcode.QRCode(border=0)
        qr.add_data(qr_text)
        qr.make(fit=True)
        print(_render_qr_half_blocks(qr.get_matrix()))
        return True
    except Exception:
        return False


def qrcode_login() -> str:
    """纯 HTTP QR 扫码登录，返回保存的 cookie 字符串。"""
    a1 = _generate_a1()
    webid = _generate_webid()
    tmp_cookies = {"a1": a1, "webId": webid}

    print("🔑 正在启动 QR 扫码登录（HTTP API）...")

    with XhsClient(tmp_cookies, request_delay=0) as client:
        try:
            activate_data = client.login_activate()
            _apply_session_cookies(client, activate_data)
        except Exception as exc:
            logger.debug("Initial activate failed (non-fatal): %s", exc)

        qr_data = client.create_qr_login()
        qr_id = qr_data["qr_id"]
        code = qr_data["code"]
        qr_url = qr_data["url"]

        print("\n📱 请用小红书 App 扫描下方二维码：\n")
        if not _display_qr_text_in_terminal(qr_url):
            print(f"QR URL: {qr_url}")
        print("\n⏳ 等待扫码...")

        start = time.time()
        last_status = -1
        consecutive_errors = 0

        while (time.time() - start) < QR_POLL_TIMEOUT_S:
            time.sleep(QR_POLL_INTERVAL_S)

            try:
                status_data = client.check_qr_status(qr_id, code)
            except Exception as exc:
                logger.debug("QR status check error: %s", exc)
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    raise LoginError(f"QR 状态轮询重复失败: {exc}") from exc
                continue
            consecutive_errors = 0

            code_status = status_data.get("codeStatus", -1)
            if code_status != last_status:
                last_status = code_status
                if code_status == QR_SCANNED:
                    print("📲 已扫码！等待确认...")
                elif code_status == QR_CONFIRMED:
                    print("✅ 登录确认！")

            if code_status == QR_CONFIRMED:
                confirmed_user_id = status_data.get("userId", "")
                if not confirmed_user_id:
                    raise LoginError("QR 登录已确认，但未返回 userId")
                completion_data = _complete_confirmed_session(client, qr_id, code, confirmed_user_id)
                user_id = _resolved_user_id(completion_data) or confirmed_user_id
                cookies = _build_saved_cookies(a1, webid, client.cookies)
                cookie_str = _dict_to_cookie_str(cookies)
                save_cookies(cookie_str)
                if user_id:
                    print(f"👤 当前用户 ID: {user_id}")
                return cookie_str

            elapsed = time.time() - start
            if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                print("  仍在等待...")

    raise LoginError("QR 扫码登录超时（4 分钟）")


# ---------- Cookie 持久化 ----------


def save_cookies(cookie_str: str):
    """Save cookies to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    cookies = cookie_str_to_dict(cookie_str)
    data = {"cookies": cookies}

    COOKIE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    try:
        COOKIE_FILE.chmod(0o600)  # Owner-only read/write
    except OSError:
        logger.debug("Failed to set permissions on %s", COOKIE_FILE)
    logger.info("Cookies saved to %s", COOKIE_FILE)


def clear_cookies():
    """Remove saved cookies and token cache (for logout)."""
    removed = []
    for f in (COOKIE_FILE, TOKEN_CACHE_FILE):
        if f.exists():
            f.unlink()
            removed.append(f.name)
    if removed:
        logger.info("Removed: %s", ", ".join(removed))
    return removed


def _has_required_cookies(cookies: dict) -> bool:
    return REQUIRED_COOKIES.issubset(cookies.keys())


def _dict_to_cookie_str(cookies: dict) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def cookie_str_to_dict(cookie_str: str) -> dict:
    """Parse a cookie header string into a dict.

    Example: "a1=xxx; web_session=yyy" -> {"a1": "xxx", "web_session": "yyy"}
    """
    result = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            result[k.strip()] = v.strip()
    return result


# ===== xsec_token cache =====
# After a search, we cache the note_id -> xsec_token mapping so that
# subsequent commands (note, like, favorite, comment) can automatically
# resolve the token without requiring the user to pass --xsec-token.


def save_token_cache(token_map: dict[str, str]):
    """Save note_id -> xsec_token mapping from search results."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    existing = {}
    if TOKEN_CACHE_FILE.exists():
        try:
            existing = json.loads(TOKEN_CACHE_FILE.read_text())
        except (OSError, json.JSONDecodeError):
            pass

    existing.update(token_map)
    TOKEN_CACHE_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    try:
        TOKEN_CACHE_FILE.chmod(0o600)
    except OSError:
        logger.debug("Failed to set permissions on %s", TOKEN_CACHE_FILE)
    logger.info("Cached %d xsec_token(s) to %s", len(token_map), TOKEN_CACHE_FILE)


def load_xsec_token(note_id: str) -> str:
    """Look up cached xsec_token for a given note_id."""
    if not TOKEN_CACHE_FILE.exists():
        return ""

    try:
        cache = json.loads(TOKEN_CACHE_FILE.read_text())
        token = cache.get(note_id, "")
        if token:
            logger.info("Auto-resolved xsec_token for %s from cache", note_id)
        return token
    except (OSError, json.JSONDecodeError):
        return ""