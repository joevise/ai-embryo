"""
工具配置管理模块

提供配置化的工具注册和管理机制
"""
import yaml
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
from .tool_registry import ToolRegistry, create_default_registry


class FunctionToolConfig(BaseModel):
    """函数工具配置"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: Dict[str, Any] = Field(..., description="工具参数schema")
    module: Optional[str] = Field(None, description="工具所在模块")
    function: Optional[str] = Field(None, description="工具函数名")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Tool name must be a non-empty string")
        return v


class MCPServerConfig(BaseModel):
    """MCP服务器配置"""
    name: str = Field(..., description="服务器名称")
    command: List[str] = Field(..., description="启动命令")
    args: List[str] = Field(default_factory=list, description="启动参数")
    env: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    timeout: int = Field(30, description="连接超时时间（秒）")
    auto_retry: bool = Field(True, description="是否自动重试连接")
    
    @validator('command')
    def validate_command(cls, v):
        if not v or not isinstance(v, list):
            raise ValueError("Command must be a non-empty list")
        return v


class ToolsConfig(BaseModel):
    """工具配置总配置"""
    load_defaults: bool = Field(True, description="是否加载默认工具")
    function_tools: List[FunctionToolConfig] = Field(default_factory=list, description="函数工具配置")
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP服务器配置")
    
    class Config:
        extra = "allow"


class ToolConfigManager:
    """工具配置管理器"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化工具配置管理器
        
        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = Path(config_path) if config_path else None
        self.config: Optional[ToolsConfig] = None
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> ToolsConfig:
        """
        加载工具配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            ToolsConfig: 工具配置对象
        """
        if config_path:
            self.config_path = Path(config_path)
        
        if not self.config_path or not self.config_path.exists():
            self.logger.info("No config file found, using default configuration")
            self.config = ToolsConfig()
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif self.config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_path.suffix}")
            
            self.config = ToolsConfig(**config_data)
            self.logger.info(f"Loaded tool configuration from {self.config_path}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {e}")
            self.config = ToolsConfig()
            return self.config
    
    def save_config(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        保存工具配置
        
        Args:
            config_path: 配置文件路径
        """
        if not self.config:
            raise ValueError("No configuration to save")
        
        save_path = Path(config_path) if config_path else self.config_path
        if not save_path:
            raise ValueError("No save path specified")
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = self.config.dict()
            
            with open(save_path, 'w', encoding='utf-8') as f:
                if save_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                elif save_path.suffix.lower() == '.json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Unsupported config file format: {save_path.suffix}")
            
            self.logger.info(f"Saved tool configuration to {save_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config to {save_path}: {e}")
            raise
    
    async def create_registry_from_config(self, config: Optional[ToolsConfig] = None) -> ToolRegistry:
        """
        根据配置创建工具注册中心
        
        Args:
            config: 工具配置对象
            
        Returns:
            ToolRegistry: 配置好的工具注册中心
        """
        if not config:
            config = self.config or ToolsConfig()
        
        # 创建注册中心
        if config.load_defaults:
            registry = create_default_registry()
        else:
            registry = ToolRegistry()
        
        # 注册自定义函数工具
        for tool_config in config.function_tools:
            await self._register_function_tool(registry, tool_config)
        
        # 注册MCP服务器
        for server_config in config.mcp_servers:
            await self._register_mcp_server(registry, server_config)
        
        return registry
    
    async def _register_function_tool(self, registry: ToolRegistry, tool_config: FunctionToolConfig):
        """注册函数工具"""
        try:
            # 如果指定了模块和函数名，动态导入
            if tool_config.module and tool_config.function:
                func = self._import_function(tool_config.module, tool_config.function)
            else:
                # 创建基础工具函数
                func = lambda **kwargs: f"Tool '{tool_config.name}' executed with: {kwargs}"
            
            registry.register_function(
                name=tool_config.name,
                description=tool_config.description,
                parameters=tool_config.parameters,
                function=func
            )
            
            self.logger.info(f"Registered function tool: {tool_config.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to register function tool {tool_config.name}: {e}")
    
    async def _register_mcp_server(self, registry: ToolRegistry, server_config: MCPServerConfig):
        """注册MCP服务器"""
        try:
            await registry.register_mcp_server(
                server_name=server_config.name,
                server_command=server_config.command,
                server_args=server_config.args
            )
            
            self.logger.info(f"Registered MCP server: {server_config.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP server {server_config.name}: {e}")
    
    def _import_function(self, module_name: str, function_name: str):
        """动态导入函数"""
        try:
            import importlib
            module = importlib.import_module(module_name)
            return getattr(module, function_name)
        except Exception as e:
            self.logger.error(f"Failed to import function {function_name} from {module_name}: {e}")
            raise
    
    def get_config(self) -> Optional[ToolsConfig]:
        """获取当前配置"""
        return self.config
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        验证配置数据
        
        Args:
            config_data: 配置数据
            
        Returns:
            bool: 是否有效
        """
        try:
            ToolsConfig(**config_data)
            return True
        except Exception as e:
            self.logger.error(f"Config validation failed: {e}")
            return False


# 默认配置模板
DEFAULT_CONFIG_TEMPLATE = {
    "load_defaults": True,
    "function_tools": [
        {
            "name": "echo",
            "description": "Echo the input text",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to echo"}
                },
                "required": ["text"]
            }
        }
    ],
    "mcp_servers": [
        {
            "name": "filesystem",
            "command": ["mcp-server-filesystem"],
            "args": ["--root", "/tmp"],
            "timeout": 30,
            "auto_retry": True
        }
    ]
}


def create_default_config_file(config_path: Union[str, Path]) -> None:
    """
    创建默认配置文件
    
    Args:
        config_path: 配置文件路径
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            yaml.dump(DEFAULT_CONFIG_TEMPLATE, f, default_flow_style=False, allow_unicode=True)
        else:
            json.dump(DEFAULT_CONFIG_TEMPLATE, f, indent=2, ensure_ascii=False)


async def load_registry_from_file(config_path: Union[str, Path]) -> ToolRegistry:
    """
    从配置文件加载工具注册中心
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ToolRegistry: 配置好的工具注册中心
    """
    manager = ToolConfigManager(config_path)
    config = manager.load_config()
    return await manager.create_registry_from_config(config)


# 便利函数
def create_config_manager(config_path: Optional[Union[str, Path]] = None) -> ToolConfigManager:
    """创建工具配置管理器"""
    return ToolConfigManager(config_path)