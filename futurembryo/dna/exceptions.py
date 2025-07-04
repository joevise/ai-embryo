"""
DNA模块异常类
"""

from ..core.exceptions import FuturEmbryoError


class DNAError(FuturEmbryoError):
    """DNA相关异常基类"""
    pass


class DNAValidationError(DNAError):
    """DNA配置验证异常"""
    pass


class DNALoadError(DNAError):
    """DNA配置加载异常"""
    pass


class DNAParseError(DNAError):
    """DNA配置解析异常"""
    pass


class GeneError(DNAError):
    """基因配置异常"""
    pass


class LifeGrowthError(DNAError):
    """生命体培养异常"""
    pass 