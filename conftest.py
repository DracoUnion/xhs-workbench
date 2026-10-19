"""pytest 启动钩子：工作台包位于仓库根。

pytest 收集 tests/ 时从仓库根导入本文件；把根目录加入 sys.path，
使测试中的 `from core.* / services.* / tools.* / adapters.* import ...` 直接解析。
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
