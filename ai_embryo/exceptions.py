"""
AI Embryo Engine — 异常定义
"""


class AIEmbryoError(Exception):
    """AI Embryo 基础异常"""
    pass


class GenomeError(AIEmbryoError):
    """基因组相关错误"""
    pass


class GenomeValidationError(GenomeError):
    """基因组验证失败"""
    pass


class CellError(AIEmbryoError):
    """细胞执行错误"""
    pass


class DevelopmentError(AIEmbryoError):
    """发育过程错误（Genome → Organism 失败）"""
    pass


class EvolutionError(AIEmbryoError):
    """进化过程错误"""
    pass
