"""
ToolCell v2 - 重构后的工具Cell实现

作为纯工具提供者，暴露工具清单给LLMCell，不再进行智能选择
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from ..core.cell import Cell
from ..core.tool_registry import ToolRegistry, create_default_registry
from ..core.exceptions import CellConfigurationError


class ToolCell(Cell):
    """工具Cell v2 - 作为工具提供者角色"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 registry: Optional[ToolRegistry] = None):
        """
        初始化ToolCell
        
        Args:
            config: Cell配置，可包含：
                - tools: 工具配置列表
                - mcp_servers: MCP服务器配置
                - auto_load_defaults: 是否自动加载默认工具
            registry: 外部提供的工具注册中心（可选）
        """
        super().__init__(config)
        
        # 使用外部注册中心或创建新的
        self.registry = registry or ToolRegistry()
        
        # 配置参数
        self.auto_load_defaults = self.config.get("auto_load_defaults", True)
        self.tools_config = self.config.get("tools", [])
        self.mcp_servers_config = self.config.get("mcp_servers", [])
        
        # 初始化工具
        self._initialize_tools()
        
        self.logger.info("ToolCell v2 initialized as tool provider")
    
    def _initialize_tools(self):
        """初始化工具注册"""
        # 加载默认工具
        if self.auto_load_defaults:
            self.registry = create_default_registry()
            self.logger.info("Loaded default tools")
        
        # 注册自定义函数工具
        for tool_config in self.tools_config:
            self._register_custom_tool(tool_config)
        
        # 注册MCP服务器（异步操作，需要在第一次使用时初始化）
        if self.mcp_servers_config:
            self._mcp_servers_pending = self.mcp_servers_config
        else:
            self._mcp_servers_pending = []
    
    def _register_custom_tool(self, tool_config: Dict[str, Any]):
        """注册自定义工具"""
        try:
            name = tool_config["name"]
            description = tool_config["description"]
            parameters = tool_config["parameters"]
            
            # 创建工具函数
            if "function" in tool_config:
                # 从配置中获取函数
                func = tool_config["function"]
            else:
                # 创建基础工具函数
                func = lambda **kwargs: self._execute_basic_tool(name, kwargs)
            
            self.registry.register_function(name, description, parameters, func)
            self.logger.info(f"Registered custom tool: {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to register custom tool: {e}")
    
    def _execute_basic_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """执行基础工具"""
        return f"Tool '{tool_name}' executed with parameters: {parameters}"
    
    async def _ensure_mcp_servers_initialized(self):
        """确保MCP服务器已初始化"""
        if hasattr(self, '_mcp_servers_pending') and self._mcp_servers_pending:
            for server_config in self._mcp_servers_pending:
                try:
                    server_name = server_config["name"]
                    await self.registry.register_mcp_server(server_name, server_config)
                    self.logger.info(f"Registered MCP server: {server_name}")
                except Exception as e:
                    self.logger.error(f"Failed to register MCP server {server_config.get('name', 'unknown')}: {e}")
            
            # 清除待初始化列表
            self._mcp_servers_pending = []
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理工具相关请求
        
        Args:
            context: 包含以下字段：
                - action: 操作类型 ("get_tools", "execute_tool", "get_status")
                - tool_name: 工具名称（执行工具时使用）
                - parameters: 工具参数（执行工具时使用）
                
        Returns:
            Dict包含：
                - tools_schema: OpenAI Function Call格式的工具schema
                - execution_result: 工具执行结果
                - status: 工具中心状态
        """
        action = context.get("action", "get_tools")
        
        try:
            if action == "get_tools":
                return self._get_tools_schema()
            elif action == "execute_tool":
                return self._execute_tool(context)
            elif action == "get_status":
                return self._get_tool_status()
            else:
                raise CellConfigurationError(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"ToolCell processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tools_schema": [],
                "execution_result": None
            }
    
    def _get_tools_schema(self) -> Dict[str, Any]:
        """获取工具Schema"""
        try:
            # 使用事件循环运行异步方法
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # 如果在异步上下文中，返回空列表并记录警告
                self.logger.warning("Cannot run async operations in running event loop context")
                tools_schema = []
            else:
                # 如果不在异步上下文中，可以直接运行
                tools_schema = loop.run_until_complete(self._get_tools_schema_async())
            
            return {
                "success": True,
                "tools_schema": tools_schema,
                "tools_count": len(tools_schema)
            }
        except Exception as e:
            self.logger.error(f"Failed to get tools schema: {e}")
            return {
                "success": False,
                "error": str(e),
                "tools_schema": [],
                "tools_count": 0
            }
    
    async def _get_tools_schema_async(self) -> List[Dict[str, Any]]:
        """异步获取工具Schema"""
        await self._ensure_mcp_servers_initialized()
        return await self.registry.get_tools_schema()
    
    def _execute_tool(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        tool_name = context.get("tool_name")
        parameters = context.get("parameters", {})
        
        if not tool_name:
            return {
                "success": False,
                "error": "tool_name is required",
                "execution_result": None
            }
        
        try:
            # 使用事件循环运行异步方法
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # 在异步上下文中的处理
                execution_result = {"success": False, "error": "Async execution not supported in this context"}
            else:
                execution_result = loop.run_until_complete(
                    self._execute_tool_async(tool_name, parameters)
                )
            
            return {
                "success": execution_result.get("success", False),
                "execution_result": execution_result,
                "tool_name": tool_name
            }
        except Exception as e:
            self.logger.error(f"Failed to execute tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_result": None,
                "tool_name": tool_name
            }
    
    async def _execute_tool_async(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行工具"""
        await self._ensure_mcp_servers_initialized()
        return await self.registry.execute_tool(tool_name, parameters)
    
    def _get_tool_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        status = self.registry.get_status()
        return {
            "success": True,
            "registry_status": status,
            "config": {
                "auto_load_defaults": self.auto_load_defaults,
                "custom_tools_count": len(self.tools_config),
                "mcp_servers_count": len(self.mcp_servers_config)
            }
        }
    
    # 提供给LLMCell使用的便利方法
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表（供LLMCell调用）"""
        await self._ensure_mcp_servers_initialized()
        return await self.registry.get_tools_schema()
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具（供LLMCell调用）"""
        await self._ensure_mcp_servers_initialized()
        return await self.registry.execute_tool(tool_name, parameters)
    
    def get_tool_registry(self) -> ToolRegistry:
        """获取工具注册中心（供外部使用）"""
        return self.registry
    
    def get_status(self) -> Dict[str, Any]:
        """获取ToolCell状态"""
        status = super().get_status()
        registry_status = self.registry.get_status()
        status.update({
            "registry_status": registry_status,
            "auto_load_defaults": self.auto_load_defaults,
            "custom_tools": len(self.tools_config),
            "mcp_servers": len(self.mcp_servers_config)
        })
        return status


# 兼容性：创建工厂函数
def create_tool_cell(config: Optional[Dict[str, Any]] = None) -> ToolCell:
    """创建配置好的ToolCell实例"""
    return ToolCell(config)


# 工具配置示例
EXAMPLE_TOOL_CONFIG = {
    "auto_load_defaults": True,
    "tools": [
        {
            "name": "custom_greeter",
            "description": "A custom greeting tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"}
                },
                "required": ["name"]
            }
        }
    ],
    "mcp_servers": [
        {
            "name": "filesystem",
            "command": ["mcp-server-filesystem"],
            "args": ["--path", "/tmp"]
        }
    ]
}