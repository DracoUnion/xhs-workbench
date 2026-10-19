"""pytest 启动钩子：后端子包位于 src/ 下，以顶层包名导入。

pytest 收集 tests/ 时会从仓库根导入本文件，这里把 src/ 加入 sys.path，
使测试中的 `from core.* / services.* / tools.* / adapters.* import ...` 直接解析。
"""
from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent / "src"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
