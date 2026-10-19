"""独立运行：交互式小红书 HTTP QR 扫码登录并保存 cookie。

用法：
    python -m scripts.xhs_login
"""
from __future__ import annotations

import sys
from pathlib import Path

# 工作台包位于 src/ 下，把 src/ 加入 sys.path 以顶层导入。
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main() -> int:
    from adapters.xhs import login_by_qrcode

    try:
        data = login_by_qrcode()
    except Exception as exc:  # noqa: BLE001
        print(f"[xhs-login] 失败: {exc}", file=sys.stderr)
        return 1
    print(f"[xhs-login] 完成，authenticated={data.get('authenticated')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())