"""
FuturEmbryo多智能体协作系统 - 核心模块

动态智能体协作框架
"""

# 导入实际存在的模块
try:
    from .base_objects import BaseObject, ObjectType
    _has_base_objects = True
except ImportError:
    _has_base_objects = False

# 导入新增的动态智能体模块
from .context_builder import ContextBuilder
from .dynamic_agent_factory import DynamicAgentFactory

__all__ = ['ContextBuilder', 'DynamicAgentFactory']

# 添加基础对象（如果存在）
if _has_base_objects:
    __all__.extend(['BaseObject', 'ObjectType'])