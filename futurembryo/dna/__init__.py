"""
FuturEmbryo DNA模块 - AI生命体的遗传密码

EmbryoDNA配置系统，支持通过配置文件一键生成AI智能体
"""

from .embryo_dna import EmbryoDNA
from .genes import (
    PurposeGene,
    CapabilityGene,
    StructureGene,
    BehaviorGene,
    EvolutionGene
)
from .exceptions import DNAError, DNAValidationError, DNALoadError, DNAParseError, GeneError

# 暂时注释掉未完全实现的组件
# from .life_grower import LifeGrower
# from .cell_factory import DNACellFactory

__all__ = [
    # 核心DNA类
    "EmbryoDNA",
    
    # 基因类型
    "PurposeGene",
    "CapabilityGene", 
    "StructureGene",
    "BehaviorGene",
    "EvolutionGene",
    
    # 异常
    "DNAError",
    "DNAValidationError",
    "DNALoadError", 
    "DNAParseError",
    "GeneError"
    
    # 生命管理 - 下一阶段开发
    # "LifeGrower",
    # "DNACellFactory",
] 