"""
Embryo — 胚胎发育器

唯一职责：把 Genome 变成 Organism。
无状态，纯工厂。

发育过程中会把 genome 信息注入给每个 Cell：
- _genome: 完整基因组数据（identity + blueprint）
- _model_config: 模型参数
- _identity: 身份基因
"""

from __future__ import annotations

from typing import Any

from .cell import Cell
from .genome import Genome
from .organism import Organism
from .registry import CellRegistry
from .exceptions import DevelopmentError


class Embryo:
    """胚胎 — 负责从基因组发育出生命体"""

    @staticmethod
    def develop(genome: Genome) -> Organism:
        """发育：基因组 → 生命体
        
        步骤：
        1. 验证基因组
        2. 解析 Cell 定义
        3. 注入 genome 信息并实例化每个 Cell
        4. 确定组装方式
        5. 返回可运行的 Organism
        """
        try:
            genome.validate()

            cell_defs = genome.blueprint.get("cells", [])
            if not cell_defs:
                raise DevelopmentError("基因组中没有定义任何 Cell")

            # 准备注入数据
            genome_injection = {
                "identity": genome.identity,
                "blueprint": genome.blueprint,
            }
            model_config = genome.blueprint.get("model_config", {})

            cells: list[Cell] = []
            for i, cell_def in enumerate(cell_defs):
                cell_type = cell_def["type"]
                raw_config = cell_def.get("config", {})

                # 解析变量引用
                resolved_config = genome.resolve_references(raw_config)
                
                # 注入 genome 数据（让 Cell 能访问完整信息）
                resolved_config["_genome"] = genome_injection
                resolved_config["_model_config"] = model_config
                resolved_config["_identity"] = genome.identity

                try:
                    cell_class = CellRegistry.get(cell_type)
                except Exception:
                    raise DevelopmentError(
                        f"Cell[{i}] 类型 '{cell_type}' 未注册。"
                        f"已注册: {CellRegistry.list()}"
                    )

                cell = cell_class(config=resolved_config)
                cells.append(cell)

            assembly = genome.blueprint.get("assembly", "sequential")

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
