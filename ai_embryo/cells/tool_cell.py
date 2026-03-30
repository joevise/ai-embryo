"""
ToolCell — 工具执行细胞

职责：执行工具调用，返回结果。
支持自定义 Python 函数和 MCP 协议。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from ..cell import Cell
from ..registry import CellRegistry
from ..exceptions import CellError

logger = logging.getLogger("ai_embryo.cells.tool")


@CellRegistry.register()
class ToolCell(Cell):
    """工具执行细胞
    
    配置项：
        tools: 工具定义字典 {name: callable}
    """

    # 全局工具注册表
    _global_tools: dict[str, Callable] = {}

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        
        # 实例级工具（从配置注入）
        self._local_tools: dict[str, Callable] = {}
        
        tools = self.config.get("tools", {})
        if isinstance(tools, dict):
            self._local_tools = tools

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        """执行工具调用
        
        Args:
            input: 包含以下键：
                - tool_name: 要调用的工具名称
                - arguments: 工具参数字典
                - tool_calls: LLMCell 返回的工具调用列表（批量执行）
                
        Returns:
            - result: 工具执行结果
            - tool_results: 批量执行结果列表
            - response: 结果摘要
        """
        # 批量执行（从 LLMCell 的 tool_calls 来）
        tool_calls = input.get("tool_calls", [])
        if tool_calls:
            return self._execute_batch(tool_calls)

        # 单次执行
        tool_name = input.get("tool_name", "")
        arguments = input.get("arguments", {})
        
        if not tool_name:
            return {"response": "没有指定工具名称", "result": None}

        result = self._execute_one(tool_name, arguments)
        return {
            "result": result,
            "response": str(result),
        }

    def _execute_batch(self, tool_calls: list[dict]) -> dict[str, Any]:
        """批量执行工具调用"""
        results = []
        for call in tool_calls:
            name = call.get("name", "")
            args = call.get("arguments", {})
            try:
                result = self._execute_one(name, args)
                results.append({
                    "tool_call_id": call.get("id", ""),
                    "name": name,
                    "result": result,
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "tool_call_id": call.get("id", ""),
                    "name": name,
                    "error": str(e),
                    "success": False,
                })

        return {
            "tool_results": results,
            "response": f"执行了 {len(results)} 个工具调用",
        }

    def _execute_one(self, name: str, arguments: dict) -> Any:
        """执行单个工具"""
        # 优先查找本地工具，再查全局
        tool_fn = self._local_tools.get(name) or self._global_tools.get(name)
        
        if tool_fn is None:
            raise CellError(f"未知工具: '{name}'")

        try:
            return tool_fn(**arguments)
        except Exception as e:
            raise CellError(f"工具 '{name}' 执行失败: {e}") from e

    # ── 工具注册（类方法）──────────────────────────────────

    @classmethod
    def register_tool(cls, name: str, fn: Callable) -> None:
        """注册全局工具"""
        cls._global_tools[name] = fn

    @classmethod
    def register_tools(cls, tools: dict[str, Callable]) -> None:
        """批量注册全局工具"""
        cls._global_tools.update(tools)

    @classmethod
    def list_tools(cls) -> list[str]:
        """列出所有已注册的全局工具"""
        return sorted(cls._global_tools.keys())
