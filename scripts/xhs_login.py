"""独立运行：交互式小红书扫码登录并保存 cookie。

浏览器依赖（camoufox）以额外可选组件安装，未安装时仅报错提示：
    pip install -e ".[xhs]"

用法：
    python -m scripts.xhs_login
"""
from __future__ import annotations

import sys


def main() -> int:
    from app.adapters.xhs import login_by_qrcode

    try:
        data = login_by_qrcode()
    except Exception as exc:  # noqa: BLE001
        print(f"[xhs-login] 失败: {exc}", file=sys.stderr)
        return 1
    print(f"[xhs-login] 完成，authenticated={data.get('authenticated')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())