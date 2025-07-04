"""
全局配置管理系统

提供统一的配置管理，支持环境变量、代码设置和局部覆盖
"""
import os
import threading
from typing import Dict, Any, Optional
from .exceptions import ConfigurationError, APIKeyError


class GlobalConfig:
    """全局配置管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._config = {}
            self._load_defaults()
            self._load_from_env()
            self._initialized = True
    
    def _load_defaults(self):
        """加载默认配置"""
        self._config = {
            # API配置
            "api_keys": {},
            "api_base_urls": {},
            
            # 默认设置
            "default_model": "gpt-3.5-turbo",
            "default_timeout": 30.0,
            "default_max_retries": 3,
            "default_temperature": 0.7,
            
            # 日志配置
            "log_level": "INFO",
            "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            
            # 性能配置
            "max_memory_mb": 512,
            "enable_profiling": False,
        }
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # API密钥
        openai_key = os.getenv("FUTUREMBRYO_OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.set_api_key("openai", openai_key)
        
        anthropic_key = os.getenv("FUTUREMBRYO_ANTHROPIC_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.set_api_key("anthropic", anthropic_key)
        
        # Base URL
        openai_base = os.getenv("FUTUREMBRYO_OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        if openai_base:
            self.set_api_base_url("openai", openai_base)
        
        # 其他配置
        if os.getenv("FUTUREMBRYO_DEFAULT_MODEL"):
            self._config["default_model"] = os.getenv("FUTUREMBRYO_DEFAULT_MODEL")
        
        if os.getenv("FUTUREMBRYO_TIMEOUT"):
            try:
                self._config["default_timeout"] = float(os.getenv("FUTUREMBRYO_TIMEOUT"))
            except ValueError:
                pass
    
    def set_api_key(self, provider: str, api_key: str):
        """设置API密钥"""
        if not api_key:
            raise APIKeyError(f"API key for {provider} cannot be empty")
        self._config["api_keys"][provider] = api_key
    
    def get_api_key(self, provider: str) -> str:
        """获取API密钥"""
        api_key = self._config["api_keys"].get(provider)
        if not api_key:
            raise APIKeyError(f"API key for {provider} not found. Please set it using GlobalConfig.set_api_key()")
        return api_key
    
    def set_api_base_url(self, provider: str, base_url: str):
        """设置API Base URL"""
        self._config["api_base_urls"][provider] = base_url
    
    def get_api_base_url(self, provider: str) -> Optional[str]:
        """获取API Base URL"""
        return self._config["api_base_urls"].get(provider)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)
    
    def update(self, config_dict: Dict[str, Any]):
        """批量更新配置"""
        self._config.update(config_dict)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置（去除敏感信息）"""
        safe_config = self._config.copy()
        # 隐藏API密钥
        if "api_keys" in safe_config:
            safe_config["api_keys"] = {k: f"***{v[-4:]}" if v else "Not Set" 
                                     for k, v in safe_config["api_keys"].items()}
        return safe_config
    
    @classmethod
    def setup_futurx_api(cls, api_key: str, base_url: str = "https://litellm.futurx.cc"):
        """快速设置FuturX API配置"""
        instance = cls()
        instance.set_api_key("openai", api_key)  # 使用openai兼容接口
        instance.set_api_base_url("openai", base_url)
        return instance


# 创建全局实例
_global_config = GlobalConfig()

# 便捷函数
def set_api_key(provider: str, api_key: str):
    """设置API密钥的便捷函数"""
    _global_config.set_api_key(provider, api_key)

def get_api_key(provider: str) -> str:
    """获取API密钥的便捷函数"""
    return _global_config.get_api_key(provider)

def set_api_base_url(provider: str, base_url: str):
    """设置API Base URL的便捷函数"""
    _global_config.set_api_base_url(provider, base_url)

def get_api_base_url(provider: str) -> Optional[str]:
    """获取API Base URL的便捷函数"""
    return _global_config.get_api_base_url(provider)

def setup_futurx_api(api_key: str, base_url: str = "https://litellm.futurx.cc"):
    """快速设置FuturX API配置的便捷函数"""
    return GlobalConfig.setup_futurx_api(api_key, base_url)

def get_config(key: str, default: Any = None) -> Any:
    """获取配置项的便捷函数"""
    return _global_config.get(key, default)

def set_config(key: str, value: Any):
    """设置配置项的便捷函数"""
    _global_config.set(key, value) 