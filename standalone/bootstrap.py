"""桌面版启动前的环境准备。

必须在导入任何 app.* 模块之前执行：app.core.config.get_settings() 被缓存，
app.core.database.engine 也在导入时创建。桌面版使用自己的 SQLite 数据文件，
避免与仓库根目录的 Web 版数据库互相锁定。

路径约定：后端已整体移入 standalone/app/，保持 `import app` 命名不变——
通过把 standalone/ 插入 sys.path 的前部实现（app 包现在位于 standalone/app）。
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

# 让 `import app` 解析到 standalone/app/（后端包），同时仍允许 `import standalone`。
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# 桌面版始终使用 standalone/data 下的数据库；业务配置仍可由环境变量提供。
os.environ["DATABASE_URL"] = f"sqlite:///{(DATA_DIR / 'xhs_workbench.db').as_posix()}"
os.environ["RUN_EXECUTOR"] = "inline"
os.environ.setdefault("LOG_DIR", str(LOG_DIR))
os.environ.setdefault("DATA_DIR", str(DATA_DIR))

__all__ = ["APP_DIR", "DATA_DIR", "LOG_DIR"]
