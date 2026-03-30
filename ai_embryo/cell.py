"""
Cell — AI Embryo 的最小功能单元

设计原则：
    - 极简：只有 process() 一个核心方法
    - 无状态：Cell 不持有进化历史、生命名片等
    - 可组合：多个 Cell 组装成 Organism
"""

from __future__ import annotations
from typing import Any


class Cell:
    """细胞 — 最小功能单元
    
    所有 Cell 只需实现一个方法：process(input) -> output
    
    Examples:
        >>> class EchoCell(Cell):
        ...     def process(self, input: dict) -> dict:
        ...         return {"response": input.get("input", "")}
        >>> cell = EchoCell()
        >>> cell.process({"input": "hello"})
        {'response': 'hello'}
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        """核心处理方法 — 子类必须实现
        
        Args:
            input: 输入字典，至少包含 "input" 键
            
        Returns:
            输出字典，通常包含 "response" 键
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} 必须实现 process() 方法"
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"
