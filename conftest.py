"""pytest 启动钩子：后端已移入 src/app/，保持 `import app` 可解析。

pytest 收集 tests/ 时会从仓库根导入本文件，这里把 src/ 加入 sys.path，
使测试中的 `from app.* import ...` 解析到 src/app/。
"""
from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent / "src"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
