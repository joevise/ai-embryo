"""
RouterCell — 路由决策细胞

职责：根据输入内容决定路由方向。
用于条件分支场景。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from ..cell import Cell
from ..registry import CellRegistry

logger = logging.getLogger("ai_embryo.cells.router")


@CellRegistry.register()
class RouterCell(Cell):
    """路由细胞
    
    配置项：
        routes: 路由规则字典
            {route_name: {"keywords": [...], "description": "..."}}
        default_route: 默认路由名称
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        
        self.routes = self.config.get("routes", {})
        self.default_route = self.config.get("default_route", "default")

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        """路由决策
        
        Args:
            input: 包含以下键：
                - input: 用户输入文本
                
        Returns:
            - route: 选择的路由名称
            - response: 路由决策说明
        """
        text = str(input.get("input", "")).lower()
        
        if not text:
            return {
                "route": self.default_route,
                "response": f"空输入，使用默认路由: {self.default_route}",
            }

        # 关键词匹配
        for route_name, route_def in self.routes.items():
            keywords = route_def.get("keywords", [])
            for kw in keywords:
                if kw.lower() in text:
                    return {
                        "route": route_name,
                        "response": f"匹配到路由: {route_name} (关键词: {kw})",
                    }

        return {
            "route": self.default_route,
            "response": f"无匹配，使用默认路由: {self.default_route}",
        }
