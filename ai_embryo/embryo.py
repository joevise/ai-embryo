"""
Embryo — 胚胎发育器

唯一职责：把 Genome 变成 Organism。
无状态，纯工厂。
"""

from __future__ import annotations

from typing import Any

from .cell import Cell
from .genome import Genome
from .organism import Organism
from .registry import CellRegistry
from .exceptions import DevelopmentError


class Embryo:
    """胚胎 — 负责从基因组发育出生命体
    
    这是一个无状态工厂类，只做一件事：
    Genome → Organism
    """

    @staticmethod
    def develop(genome: Genome) -> Organism:
        """发育：基因组 → 生命体
        
        步骤：
        1. 验证基因组
        2. 解析 Cell 定义
        3. 实例化每个 Cell
        4. 确定组装方式
        5. 返回可运行的 Organism
        
        Args:
            genome: 基因组
            
        Returns:
            发育完成的生命体
            
        Raises:
            DevelopmentError: 发育失败
        """
        try:
            # 1. 验证
            genome.validate()

            # 2-3. 实例化 Cells
            cell_defs = genome.blueprint.get("cells", [])
            if not cell_defs:
                raise DevelopmentError("基因组中没有定义任何 Cell")

            cells: list[Cell] = []
            for i, cell_def in enumerate(cell_defs):
                cell_type = cell_def["type"]
                raw_config = cell_def.get("config", {})

                # 解析变量引用
                resolved_config = genome.resolve_references(raw_config)
                
                # 注入全局能力配置（让每个 Cell 都能访问）
                resolved_config["_capabilities"] = genome.blueprint.get("capabilities", {})
                resolved_config["_identity"] = genome.identity

                # 从注册表获取 Cell 类并实例化
                try:
                    cell_class = CellRegistry.get(cell_type)
                except Exception:
                    raise DevelopmentError(
                        f"Cell[{i}] 类型 '{cell_type}' 未注册。"
                        f"已注册: {CellRegistry.list()}"
                    )

                cell = cell_class(config=resolved_config)
                cells.append(cell)

            # 4. 确定组装方式
            assembly = genome.blueprint.get("assembly", "sequential")

            # 5. 构建 Organism
            organism = Organism(
                genome=genome,
                cells=cells,
                assembly=assembly,
            )

            return organism

        except DevelopmentError:
            raise
        except Exception as e:
            raise DevelopmentError(f"发育失败: {e}") from e
