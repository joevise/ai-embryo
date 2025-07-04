"""
基于MCP Python SDK的标准客户端实现
用于替换自制的SSE传输层，提供更可靠的MCP协议支持
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    from mcp import types
    MCP_AVAILABLE = True
    
    # SSE客户端尝试多种导入方式
    try:
        from mcp.client.sse import sse_client
        SSE_AVAILABLE = True
    except ImportError:
        try:
            from mcp.client.streamable_http import streamablehttp_client as sse_client
            SSE_AVAILABLE = True
        except ImportError:
            SSE_AVAILABLE = False
            
except ImportError:
    MCP_AVAILABLE = False
    SSE_AVAILABLE = False
    # 提供兼容性类型
    class ClientSession:
        pass
    
    class StdioServerParameters:
        pass


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    transport_type: str  # "sse" 或 "stdio"
    url: Optional[str] = None  # SSE服务器URL
    command: Optional[List[str]] = None  # stdio命令
    args: Optional[List[str]] = None  # 命令参数
    headers: Optional[Dict[str, str]] = None  # SSE请求头
    description: Optional[str] = None


class StandardMCPClient:
    """标准MCP客户端 - 使用官方MCP Python SDK"""
    
    def __init__(self):
        if not MCP_AVAILABLE:
            raise ImportError("MCP Python SDK not available. Please install with: pip install mcp")
        
        self.logger = logging.getLogger(__name__)
        self.servers: Dict[str, MCPServerConfig] = {}
        self.active_sessions: Dict[str, ClientSession] = {}
    
    def register_server(self, config: MCPServerConfig):
        """注册MCP服务器"""
        self.servers[config.name] = config
        self.logger.info(f"已注册MCP服务器: {config.name} ({config.transport_type})")
    
    def register_sse_server(self, name: str, url: str, headers: Dict[str, str] = None, description: str = None):
        """注册SSE类型的MCP服务器"""
        config = MCPServerConfig(
            name=name,
            transport_type="sse",
            url=url,
            headers=headers or {},
            description=description
        )
        self.register_server(config)
    
    def register_stdio_server(self, name: str, command: List[str], args: List[str] = None, description: str = None):
        """注册stdio类型的MCP服务器"""
        config = MCPServerConfig(
            name=name,
            transport_type="stdio",
            command=command,
            args=args or [],
            description=description
        )
        self.register_server(config)
    
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """获取服务器工具列表"""
        if server_name not in self.servers:
            raise ValueError(f"未知的MCP服务器: {server_name}")
        
        config = self.servers[server_name]
        
        if config.transport_type == "sse":
            # SSE连接 - 每次创建新连接
            return await self._list_tools_sse(config)
        else:
            # stdio连接 - 每次创建新连接以避免生命周期问题
            return await self._list_tools_stdio(config)
    
    async def _list_tools_sse(self, config: MCPServerConfig) -> List[Dict[str, Any]]:
        """SSE方式获取工具列表"""
        try:
            async with sse_client(config.url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await self._list_tools_session(session, config.name)
        except Exception as e:
            self.logger.error(f"❌ SSE获取工具列表失败: {config.name} - {e}")
            raise
    
    async def _list_tools_stdio(self, config: MCPServerConfig) -> List[Dict[str, Any]]:
        """stdio方式获取工具列表"""
        try:
            # 创建stdio服务器参数
            server_params = StdioServerParameters(
                command=config.command[0],
                args=config.command[1:] + (config.args or [])
            )
            
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await self._list_tools_session(session, config.name)
        except Exception as e:
            self.logger.error(f"❌ stdio获取工具列表失败: {config.name} - {e}")
            raise
    
    async def _list_tools_session(self, session: ClientSession, server_name: str) -> List[Dict[str, Any]]:
        """从会话获取工具列表"""
        try:
            # 使用标准MCP协议获取工具列表
            tools_response = await session.list_tools()
            
            tools_list = []
            for tool in tools_response.tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": getattr(tool, 'inputSchema', {})
                }
                tools_list.append(tool_info)
            
            self.logger.info(f"📋 获取到 {len(tools_list)} 个工具 from {server_name}")
            return tools_list
            
        except Exception as e:
            self.logger.error(f"❌ 获取工具列表失败: {server_name} - {e}")
            raise
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具"""
        self.logger.info(f"🎯 调用MCP工具: {server_name}.{tool_name}")
        self.logger.info(f"   参数: {arguments}")
        
        if server_name not in self.servers:
            raise ValueError(f"未知的MCP服务器: {server_name}")
        
        config = self.servers[server_name]
        
        if config.transport_type == "sse":
            # SSE连接 - 每次创建新连接
            return await self._call_tool_sse(config, tool_name, arguments)
        else:
            # stdio连接 - 每次创建新连接以避免生命周期问题
            return await self._call_tool_stdio(config, tool_name, arguments)
    
    async def _call_tool_sse(self, config: MCPServerConfig, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """SSE方式调用工具"""
        try:
            async with sse_client(config.url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await self._call_tool_session(session, config.name, tool_name, arguments)
        except Exception as e:
            self.logger.error(f"❌ SSE工具调用失败: {config.name}.{tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "server_name": config.name
            }
    
    async def _call_tool_stdio(self, config: MCPServerConfig, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """stdio方式调用工具"""
        try:
            # 创建stdio服务器参数
            server_params = StdioServerParameters(
                command=config.command[0],
                args=config.command[1:] + (config.args or [])
            )
            
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await self._call_tool_session(session, config.name, tool_name, arguments)
        except Exception as e:
            self.logger.error(f"❌ stdio工具调用失败: {config.name}.{tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "server_name": config.name
            }
    
    async def _call_tool_session(self, session: ClientSession, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """从会话调用工具"""
        try:
            # 使用标准MCP协议调用工具
            result = await session.call_tool(tool_name, arguments)
            
            # 处理结果
            if hasattr(result, 'content') and result.content:
                # 标准MCP工具结果格式
                content_items = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        content_items.append(item.text)
                    else:
                        content_items.append(str(item))
                
                response = {
                    "success": True,
                    "result": "\n".join(content_items),
                    "tool_name": tool_name,
                    "server_name": server_name
                }
            else:
                # 其他格式
                response = {
                    "success": True,
                    "result": str(result),
                    "tool_name": tool_name,
                    "server_name": server_name
                }
            
            self.logger.info(f"✅ MCP工具调用成功: {tool_name}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ MCP工具调用失败: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "server_name": server_name
            }
    
    async def close_all_connections(self):
        """关闭所有连接"""
        for session in self.active_sessions.values():
            try:
                await session.__aexit__(None, None, None)
            except:
                pass
        self.active_sessions.clear()
        self.logger.info("🔐 所有MCP连接已关闭")


# 全局MCP客户端实例
_global_mcp_client = None

def get_mcp_client() -> StandardMCPClient:
    """获取全局MCP客户端实例"""
    global _global_mcp_client
    if _global_mcp_client is None:
        _global_mcp_client = StandardMCPClient()
    return _global_mcp_client


def register_sse_mcp_server(name: str, url: str, headers: Dict[str, str] = None, description: str = None):
    """便捷函数：注册SSE MCP服务器"""
    client = get_mcp_client()
    client.register_sse_server(name, url, headers, description)


def register_stdio_mcp_server(name: str, command: List[str], args: List[str] = None, description: str = None):
    """便捷函数：注册stdio MCP服务器"""
    client = get_mcp_client()
    client.register_stdio_server(name, command, args, description)


async def call_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：调用MCP工具"""
    client = get_mcp_client()
    return await client.call_tool(server_name, tool_name, arguments)