"""桌面版入口：初始化环境 → 初始化后端 → 显示主窗口。"""
from __future__ import annotations

import sys
from pathlib import Path

# 工作台包位于 src/ 下：确保任意入口（python -m src / console script）都能解析。
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# 必须先设置环境再导入任何后端模块（见 bootstrap 文档说明）。
import bootstrap  # noqa: F401
from core.logging import get_logger, setup_logging
from services.seed import init_db

logger = get_logger("main")


def _auto_login() -> None:
    """无登录窗口：启动时自动以默认管理员建立内存会话，保证服务鉴权可用。"""
    from client import get_client
    from core.config import get_settings

    s = get_settings()
    try:
        get_client().login(s.admin_username, s.admin_password)
        logger.info("auto-login as %s", s.admin_username)
    except Exception as exc:  # noqa: BLE001 - 会话建立失败不阻断启动
        logger.warning("auto-login failed; 保护操作将提示未登录", error=str(exc))


def run() -> None:
    # 桌面版不再启动 HTTP 服务：PyQt 直接调用 services 层。
    setup_logging()
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001 - 数据库不可用时不阻断启动
        logger.warning("database unavailable at startup; continue booting", error=str(exc))

    _auto_login()

    from PySide6.QtWidgets import QApplication

    from bootstrap import build_context
    from main_window import MainWindow
    from styles import apply_styles

    ctx = build_context()
    app = QApplication(sys.argv)
    app.setApplicationName("自媒体 AI 工作台")
    apply_styles(app)

    win = MainWindow()
    win.ctx = ctx  # 暴露 AppContext（tasks/events）给页面
    win.show()
    exit_code = app.exec()
    ctx.tasks.shutdown(wait=False)
    sys.exit(exit_code)


if __name__ == "__main__":
    run()