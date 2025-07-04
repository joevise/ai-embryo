"""
FuturEmbryo框架自定义异常
"""


class FuturEmbryoError(Exception):
    """FuturEmbryo框架基础异常"""
    pass


class CellError(FuturEmbryoError):
    """Cell相关异常"""
    pass


class CellExecutionError(CellError):
    """Cell执行异常"""
    def __init__(self, cell_name: str, message: str, original_error: Exception = None):
        self.cell_name = cell_name
        self.original_error = original_error
        super().__init__(f"Cell '{cell_name}' execution failed: {message}")


class CellConfigurationError(CellError):
    """Cell配置异常"""
    pass


class CellTimeoutError(CellError):
    """Cell执行超时异常"""
    def __init__(self, cell_name: str, timeout: float):
        self.cell_name = cell_name
        self.timeout = timeout
        super().__init__(f"Cell '{cell_name}' timed out after {timeout} seconds")


class ConfigurationError(FuturEmbryoError):
    """配置相关异常"""
    pass


class APIKeyError(ConfigurationError):
    """API密钥异常"""
    pass


class ModelNotSupportedError(FuturEmbryoError):
    """不支持的模型异常"""
    pass 