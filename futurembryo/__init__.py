"""
FuturEmbryo - AI智能体框架

受生物学启发的智能体组合框架
"""

__version__ = "0.1.0"

# 核心组件
from .core import (
    Cell,
    CellState,
    Pipeline,
    PipelineStep,
    PipelineBuilder,
    GlobalConfig,
    setup_futurx_api,
    set_api_key,
    get_api_key,
    set_api_base_url,
    get_api_base_url,
    get_config,
    set_config
)

# Cell实现
from .cells import LLMCell, StateMemoryCell, MemoryEntry, ToolCell, MindCell

# 异常
from .core.exceptions import (
    FuturEmbryoError,
    CellError,
    CellExecutionError,
    CellConfigurationError,
    CellTimeoutError,
    ConfigurationError,
    APIKeyError,
    ModelNotSupportedError
)

__all__ = [
    # 版本信息
    "__version__",
    
    # 核心类
    "Cell",
    "CellState",
    "Pipeline",
    "PipelineStep", 
    "PipelineBuilder",
    "GlobalConfig",
    
    # 配置函数
    "setup_futurx_api",
    "set_api_key",
    "get_api_key",
    "set_api_base_url", 
    "get_api_base_url",
    "get_config",
    "set_config",
    
    # Cell实现
    "LLMCell",
    "StateMemoryCell",
    "MemoryEntry",
    "ToolCell",
    "Tool",
    
    # 异常类
    "FuturEmbryoError",
    "CellError",
    "CellExecutionError",
    "CellConfigurationError",
    "CellTimeoutError",
    "ConfigurationError",
    "APIKeyError",
    "ModelNotSupportedError"
] 