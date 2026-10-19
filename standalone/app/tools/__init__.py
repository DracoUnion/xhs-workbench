"""工具包聚合：导入即注册全部实现，并导出 registry 便捷入口。"""
from app.tools.registry import ToolRegistry, ToolSpec, registry, tool
from app.tools import implementations as _implementations  # noqa: F401  触发 @tool 注册
from app.tools import xhs_tools as _xhs_tools  # noqa: F401  小红书采集工具（惰性，无需 camoufox 即可注册）

__all__ = ["ToolRegistry", "ToolSpec", "registry", "tool"]