"""
FuturEmbryo核心模块

导出核心类和配置函数
"""

from .cell import Cell
from .state import CellState
from .pipeline import Pipeline, PipelineStep, PipelineBuilder
from .config import (
    GlobalConfig,
    setup_futurx_api,
    set_api_key,
    get_api_key,
    set_api_base_url,
    get_api_base_url,
    get_config,
    set_config
)
from .exceptions import (
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