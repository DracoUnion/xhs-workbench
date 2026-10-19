"""桌面版启动前的环境准备。

必须在导入任何后端模块之前执行：core.config.get_settings() 被缓存，
core.database.engine 也在导入时创建。桌面版使用自己的 SQLite 数据文件，
避免与仓库根目录的 Web 版数据库互相锁定。

路径约定：工作台包（core/services/models/adapters/...）位于 src/ 下，
运行 `python -m src` 或 `python src/main.py` 时 src/ 已在前部。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 运行入口可能不在 src/ 下（如 pytest/alembic/scripts），确保 src/ 在 sys.path 前部。
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# 桌面版始终使用 src/data 下的数据库；业务配置仍可由环境变量提供。
os.environ["DATABASE_URL"] = f"sqlite:///{(DATA_DIR / 'xhs_workbench.db').as_posix()}"
os.environ["RUN_EXECUTOR"] = "inline"
os.environ.setdefault("LOG_DIR", str(LOG_DIR))
os.environ.setdefault("DATA_DIR", str(DATA_DIR))

__all__ = ["APP_DIR", "DATA_DIR", "LOG_DIR"]
