"""工具注册表：Pydantic 参数模型 → JSON Schema，白名单过滤，统一调用。"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from app.core.exceptions import AppError, FatalError, ReviewRequired


class ToolSpec:
    def __init__(self, name: str, description: str, param_model: type[BaseModel], fn: Callable) -> None:
        self.name = name
        self.description = description
        self.param_model = param_model
        self.fn = fn

    @property
    def schema(self) -> dict[str, Any]:
        """OpenAI tools 数组中的单个 function schema。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.param_model.model_json_schema(),
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._specs[spec.name] = spec

    def __contains__(self, name: str) -> bool:
        return name in self._specs

    def schema_for(self, name: str) -> dict[str, Any]:
        return self._specs[name].schema

    def tools_for(self, keys: list[str]) -> list[dict[str, Any]]:
        """按白名单过滤工具 schema；未知 key 静默忽略（Agent 定义可先于实现存在）。"""
        return [self._specs[k].schema for k in keys if k in self._specs]

    def invoke(self, name: str, arguments: dict[str, Any]) -> tuple[bool, Any]:
        """返回 (ok, result)。ReviewRequired / FatalError 原样上抛，由 runtime 处理。"""
        spec = self._specs.get(name)
        if spec is None:
            return False, {"error": f"unknown tool: {name}"}
        try:
            params = spec.param_model.model_validate(arguments)
            result = spec.fn(**params.model_dump())
            return True, result
        except ReviewRequired:
            raise
        except FatalError:
            raise
        except AppError as exc:
            return False, {"error": exc.message, "code": exc.code}
        except Exception as exc:  # noqa: BLE001
            return False, {"error": f"{type(exc).__name__}: {exc}"}


registry = ToolRegistry()


def tool(name: str, description: str, parameters: type[BaseModel]) -> Callable[[Callable], Callable]:
    """装饰器：把处理函数注册进全局 registry。"""

    def deco(fn: Callable) -> Callable:
        registry.register(ToolSpec(name, description, parameters, fn))
        return fn

    return deco