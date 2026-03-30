"""
CellRegistry — 细胞注册表

管理所有可用的 Cell 类型，支持通过名称实例化。
Embryo 发育时通过 Registry 查找 Cell 类型。
"""

from __future__ import annotations
from typing import Type
from .cell import Cell
from .exceptions import CellError


class CellRegistry:
    """细胞注册表 — 全局 Cell 类型管理"""

    _registry: dict[str, Type[Cell]] = {}

    @classmethod
    def register(cls, name: str | None = None):
        """注册 Cell 类型（可用作装饰器）
        
        Examples:
            >>> @CellRegistry.register()
            ... class MyCell(Cell):
            ...     def process(self, input):
            ...         return {"response": "ok"}
            
            >>> @CellRegistry.register("custom_name")
            ... class AnotherCell(Cell):
            ...     def process(self, input):
            ...         return {"response": "ok"}
        """
        def decorator(cell_class: Type[Cell]) -> Type[Cell]:
            reg_name = name or cell_class.__name__
            cls._registry[reg_name] = cell_class
            return cell_class
        
        # 支持 @CellRegistry.register 和 @CellRegistry.register("name")
        if isinstance(name, type) and issubclass(name, Cell):
            # 直接当作 @CellRegistry.register 使用（无括号）
            cell_class = name
            cls._registry[cell_class.__name__] = cell_class
            return cell_class
        
        return decorator

    @classmethod
    def get(cls, name: str) -> Type[Cell]:
        """获取 Cell 类型
        
        Args:
            name: Cell 类型名称
            
        Returns:
            Cell 类
            
        Raises:
            CellError: 未找到 Cell 类型
        """
        if name not in cls._registry:
            available = ", ".join(sorted(cls._registry.keys()))
            raise CellError(
                f"未知 Cell 类型: '{name}'。"
                f"已注册的类型: [{available}]"
            )
        return cls._registry[name]

    @classmethod
    def list(cls) -> list[str]:
        """列出所有已注册的 Cell 类型"""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls):
        """清空注册表（主要用于测试）"""
        cls._registry.clear()
