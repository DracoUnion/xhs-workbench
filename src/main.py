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


def run() -> None:
    # 桌面版不再启动 HTTP 服务：PyQt 直接调用 services 层。
    setup_logging()
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001 - 数据库不可用时不阻断启动
        logger.warning("database unavailable at startup; continue booting", error=str(exc))

    from PySide6.QtWidgets import QApplication

    from main_window import MainWindow
    from styles import apply_styles

    app = QApplication(sys.argv)
    app.setApplicationName("自媒体 AI 工作台")
    apply_styles(app)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()