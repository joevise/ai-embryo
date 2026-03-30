"""
AI Embryo Engine — 让 AI 系统从单细胞发育、进化、繁殖的底层引擎

核心概念（只有6个）：
    Genome    — 基因组，AI 的遗传密码
    Cell      — 细胞，最小功能单元
    Organism  — 生命体，由多个 Cell 组成的可运行实体
    Embryo    — 胚胎发育器，Genome → Organism
    Fitness   — 适应度评估
    Evolution — 进化引擎，交叉 + 变异 + 选择
"""

__version__ = "1.0.0"

from .genome import Genome
from .cell import Cell
from .registry import CellRegistry
from .organism import Organism
from .embryo import Embryo
from .evolution import EvolutionEngine
from .fitness import FitnessEvaluator, Task
from .exceptions import (
    AIEmbryoError,
    GenomeError,
    GenomeValidationError,
    CellError,
    DevelopmentError,
    EvolutionError,
)

__all__ = [
    "__version__",
    # 核心 6 概念
    "Genome",
    "Cell",
    "CellRegistry",
    "Organism",
    "Embryo",
    "EvolutionEngine",
    "FitnessEvaluator",
    "Task",
    # 异常
    "AIEmbryoError",
    "GenomeError",
    "GenomeValidationError",
    "CellError",
    "DevelopmentError",
    "EvolutionError",
]
