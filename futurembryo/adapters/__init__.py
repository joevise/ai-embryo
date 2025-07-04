"""
FuturEmbryo 记忆适配器包

这个包包含各种外部记忆服务的适配器实现。
每个适配器都是独立的模块，可以单独开发和维护。
"""

from .base_adapter import MemoryAdapter

# 可选导入适配器（避免依赖问题）
try:
    from .fastgpt_adapter import FastGPTAdapter
    __all__ = ['MemoryAdapter', 'FastGPTAdapter']
except ImportError:
    __all__ = ['MemoryAdapter'] 