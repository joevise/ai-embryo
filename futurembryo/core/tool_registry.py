"""
ToolRegistry - 工具注册中心

统一管理Function Call工具和MCP工具，提供标准化的工具发现、注册和执行接口
"""
import json
import asyncio
import logging
import aiohttp
from typing import Dict, Any, List, Optional, Callable, Union, AsyncGenerator
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# MCP相关导入（可选）
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    try:
        # 尝试alternative import path
        from mcp.client import ClientSession, StdioServerParameters, stdio_client
        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False
        # 不显示警告，只在真正需要时提示

# 导入新的标准MCP客户端
try:
    from .mcp_client import StandardMCPClient, get_mcp_client
    STANDARD_MCP_AVAILABLE = True
except ImportError:
    STANDARD_MCP_AVAILABLE = False
    StandardMCPClient = None


@dataclass
class ToolSchema:
    """工具Schema定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Optional[Callable] = None
    tool_type: str = "function"  # "function" or "mcp"
    mcp_server: Optional[str] = None
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """转换为OpenAI Function Calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolProvider(ABC):
    """工具提供者基类"""
    
    @abstractmethod
    async def get_tools(self) -> List[ToolSchema]:
        """获取提供的工具列表"""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        pass


class FunctionToolProvider(ToolProvider):
    """Function Call工具提供者"""
    
    def __init__(self):
        self.tools: Dict[str, ToolSchema] = {}
    
    def register_function(self, name: str, description: str, parameters: Dict[str, Any], 
                         function: Callable) -> None:
        """注册函数工具"""
        schema = ToolSchema(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
            tool_type="function"
        )
        self.tools[name] = schema
    
    async def get_tools(self) -> List[ToolSchema]:
        """获取所有函数工具"""
        return list(self.tools.values())
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行函数工具"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        if not tool.function:
            raise ValueError(f"Tool '{tool_name}' has no function")
        
        try:
            # 执行函数
            if asyncio.iscoroutinefunction(tool.function):
                result = await tool.function(**parameters)
            else:
                result = tool.function(**parameters)
            
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name,
                "tool_type": "function"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_type": "function"
            }


class SSETransport:
    """SSE传输层实现 - 支持双端点MCP over SSE连接"""
    
    def __init__(self, url: str, headers: Dict[str, str] = None):
        self.url = url
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # 双端点模式
        self.sse_response = None  # SSE连接
        self.message_endpoint = None  # 消息发送端点
        self.session_id = None  # 会话ID
        self._pending_responses = {}  # 等待响应的请求
    
    async def __aenter__(self):
        """异步上下文管理器入口 - 建立SSE连接"""
        self.session = aiohttp.ClientSession()
        
        # 建立SSE连接
        self.sse_response = await self.session.get(
            self.url,
            headers={
                **self.headers,
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
        )
        
        # 等待获取消息端点
        await self._wait_for_endpoint()
        
        return self, self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.sse_response:
            self.sse_response.close()
        if self.session:
            await self.session.close()
    
    async def _wait_for_endpoint(self):
        """等待SSE推送消息端点信息"""
        try:
            event_type = None
            async for line in self.sse_response.content:
                line = line.decode('utf-8').strip()
                
                if line.startswith('event: '):
                    event_type = line[7:]
                elif line.startswith('data: ') and event_type == 'endpoint':
                    endpoint_path = line[6:]
                    # 构建完整的消息端点URL
                    base_url = self.url.rsplit('/', 1)[0]  # 移除/sse部分
                    self.message_endpoint = f"{base_url}{endpoint_path}"
                    
                    # 提取session_id
                    if 'session_id=' in endpoint_path:
                        self.session_id = endpoint_path.split('session_id=')[1].split('&')[0]
                    
                    self.logger.info(f"获得消息端点: {self.message_endpoint}")
                    self.logger.info(f"会话ID: {self.session_id}")
                    break
                        
        except Exception as e:
            self.logger.error(f"等待端点信息失败: {e}")
            raise
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息到SSE服务器 - 双端点模式（修复版）"""
        if not self.session or not self.message_endpoint:
            raise RuntimeError("SSE transport not properly initialized")
        
        try:
            message_id = message.get('id', 1)
            self.logger.info(f"📤 发送消息 ID {message_id} 到端点: {self.message_endpoint}")
            
            # 重要：使用同一个session发送POST请求
            async with self.session.post(
                self.message_endpoint,
                json=message,
                headers={
                    **self.headers,
                    'Content-Type': 'application/json'
                }
            ) as post_response:
                
                if post_response.status not in [200, 202]:  # 200 OK, 202 Accepted
                    error_text = await post_response.text()
                    self.logger.error(f"❌ 消息发送失败: {post_response.status} - {error_text}")
                    return {"error": f"Message send failed: {post_response.status} - {error_text}"}
                
                self.logger.info(f"✅ 消息发送成功: {post_response.status}")
            
            # 监听SSE连接以获取响应（添加超时）
            self.logger.info(f"📡 开始监听SSE响应（消息ID: {message_id}）...")
            try:
                # 设置30秒超时
                result = await asyncio.wait_for(
                    self._wait_for_response(message_id), 
                    timeout=30.0
                )
                return result
            except asyncio.TimeoutError:
                self.logger.error(f"⏰ SSE响应超时 (30秒)")
                return {"error": "SSE response timeout"}
                
        except Exception as e:
            self.logger.error(f"❌ SSE传输错误: {e}")
            return {"error": str(e)}
    
    async def _wait_for_response(self, message_id: int) -> Dict[str, Any]:
        """等待SSE响应"""
        try:
            event_count = 0
            max_events = 50  # 增加最大事件数
            
            self.logger.info(f"🎧 开始监听SSE响应（消息ID: {message_id}）...")
            
            # 监听SSE流以获取响应
            async for line in self.sse_response.content:
                line = line.decode('utf-8').strip()
                
                if line:
                    event_count += 1
                    self.logger.debug(f"📨 SSE事件 {event_count}: {line}")
                    
                    if line.startswith('data: '):
                        try:
                            data_str = line[6:]
                            if data_str in ['', '[DONE]']:
                                continue
                                
                            data = json.loads(data_str)
                            self.logger.info(f"📊 收到SSE数据: {data}")
                            
                            # 放宽匹配条件 - 接受任何有效的JSON响应
                            if isinstance(data, dict):
                                # 优先匹配ID，但也接受任何jsonrpc响应或带有result/error的响应
                                if (data.get('id') == message_id or 
                                    'jsonrpc' in data or 
                                    'result' in data or 
                                    'error' in data or
                                    'response' in data):
                                    self.logger.info(f"✅ 找到匹配的响应: {data}")
                                    return data
                                else:
                                    self.logger.debug(f"⚠️ 不匹配的响应，继续等待: {data}")
                                
                        except json.JSONDecodeError as e:
                            self.logger.debug(f"❌ JSON解析失败: {e}, 原始数据: {repr(data_str)}")
                            continue
                            
                    elif line.startswith('event: '):
                        event_type = line[7:]
                        self.logger.debug(f"📅 SSE事件类型: {event_type}")
                
                # 防止无限等待
                if event_count >= max_events:
                    self.logger.warning(f"⏹️ 达到最大事件数量 ({max_events})，停止等待")
                    break
            
            self.logger.warning(f"⚠️ 监听结束，总共收到 {event_count} 个事件，未找到匹配响应")
            return {"error": "No response received"}
            
        except Exception as e:
            self.logger.error(f"等待SSE响应失败: {e}")
            return {"error": str(e)}


class SSEMCPSession:
    """SSE MCP会话模拟器 - 适配MCP ClientSession接口"""
    
    def __init__(self, sse_transport: SSETransport):
        self.transport = sse_transport
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def initialize(self):
        """初始化MCP会话"""
        try:
            # 发送MCP初始化请求
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "FuturEmbryo",
                        "version": "1.0.0"
                    }
                }
            }
            
            result = await self.transport.send_message(init_message)
            self._initialized = True
            self.logger.info("SSE MCP会话初始化成功")
            return result
            
        except Exception as e:
            self.logger.error(f"SSE MCP会话初始化失败: {e}")
            raise
    
    async def list_tools(self):
        """获取工具列表"""
        if not self._initialized:
            await self.initialize()
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            result = await self.transport.send_message(message)
            
            # 构建工具对象
            class Tool:
                def __init__(self, name: str, description: str, input_schema: Dict = None):
                    self.name = name
                    self.description = description
                    self.inputSchema = input_schema or {}
            
            class ToolsResult:
                def __init__(self, tools: List[Tool]):
                    self.tools = tools
            
            tools = []
            if "result" in result and "tools" in result["result"]:
                for tool_data in result["result"]["tools"]:
                    tool = Tool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        input_schema=tool_data.get("inputSchema", {})
                    )
                    tools.append(tool)
            
            return ToolsResult(tools)
            
        except Exception as e:
            self.logger.error(f"获取SSE工具列表失败: {e}")
            raise
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        """调用工具"""
        if not self._initialized:
            await self.initialize()
        
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }
            
            result = await self.transport.send_message(message)
            
            # 构建结果对象
            class Content:
                def __init__(self, text: str):
                    self.text = text
            
            class ToolResult:
                def __init__(self, content: List[Content]):
                    self.content = content
            
            # 处理结果
            if "result" in result:
                if "content" in result["result"]:
                    # 标准MCP格式
                    content_items = []
                    for item in result["result"]["content"]:
                        if isinstance(item, dict) and "text" in item:
                            content_items.append(Content(item["text"]))
                        else:
                            content_items.append(Content(str(item)))
                    return ToolResult(content_items)
                else:
                    # 简化格式
                    content_text = str(result["result"])
                    return ToolResult([Content(content_text)])
            else:
                # 错误处理
                error_text = result.get("error", "Unknown error")
                return ToolResult([Content(f"Error: {error_text}")])
                
        except Exception as e:
            self.logger.error(f"SSE工具调用失败: {e}")
            raise


class StandardMCPToolProvider(ToolProvider):
    """标准MCP工具提供者 - 使用官方MCP Python SDK"""    
    
    def __init__(self):
        if not STANDARD_MCP_AVAILABLE:
            raise ImportError("标准MCP客户端不可用")
        
        self.mcp_client = get_mcp_client()
        self.tools: Dict[str, ToolSchema] = {}
        self.logger = logging.getLogger(__name__)
    
    async def register_sse_server(self, server_name: str, url: str, headers: Dict[str, str] = None, 
                                 description: str = None) -> None:
        """注册SSE MCP服务器"""
        try:
            # 注册服务器
            self.mcp_client.register_sse_server(server_name, url, headers, description)
            
            # 获取工具列表
            tools_list = await self.mcp_client.list_tools(server_name)
            
            # 注册工具
            for tool_info in tools_list:
                tool_full_name = f"{server_name}_{tool_info['name']}"
                schema = ToolSchema(
                    name=tool_full_name,
                    description=tool_info['description'],
                    parameters=tool_info.get('inputSchema', {}),
                    tool_type="mcp",
                    mcp_server=server_name
                )
                self.tools[tool_full_name] = schema
                self.logger.info(f"已注册标准MCP工具: {tool_full_name}")
            
            self.logger.info(f"✅ 成功注册SSE MCP服务器: {server_name}, 共 {len(tools_list)} 个工具")
            
        except Exception as e:
            self.logger.error(f"❌ 注册SSE MCP服务器失败: {server_name} - {e}")
            # 为不兼容的服务器创建默认查询工具
            await self._create_fallback_tool(server_name, description or "查询服务")
    
    async def register_stdio_server(self, server_name: str, command: List[str], args: List[str] = None,
                                   description: str = None) -> None:
        """注册stdio MCP服务器"""
        try:
            # 注册服务器
            self.mcp_client.register_stdio_server(server_name, command, args, description)
            
            # 获取工具列表
            tools_list = await self.mcp_client.list_tools(server_name)
            
            # 注册工具
            for tool_info in tools_list:
                tool_full_name = f"{server_name}_{tool_info['name']}"
                schema = ToolSchema(
                    name=tool_full_name,
                    description=tool_info['description'],
                    parameters=tool_info.get('inputSchema', {}),
                    tool_type="mcp",
                    mcp_server=server_name
                )
                self.tools[tool_full_name] = schema
                self.logger.info(f"已注册标准MCP工具: {tool_full_name}")
            
            self.logger.info(f"✅ 成功注册stdio MCP服务器: {server_name}, 共 {len(tools_list)} 个工具")
            
        except Exception as e:
            self.logger.error(f"❌ 注册stdio MCP服务器失败: {server_name} - {e}")
            raise
    
    async def _create_fallback_tool(self, server_name: str, description: str):
        """为不兼容的服务器创建默认查询工具"""
        tool_name = f"{server_name}_query"
        
        # 基于描述生成参数schema
        if "知识库" in description or "knowledge" in description.lower():
            parameters = {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "查询内容"
                    },
                    "similarity": {
                        "type": "number",
                        "description": "相似度阈值",
                        "default": 0.6
                    },
                    "search_mode": {
                        "type": "string",
                        "description": "搜索模式",
                        "default": "mixedRecall",
                        "enum": ["mixedRecall", "embedding", "fullText"]
                    }
                },
                "required": ["message"]
            }
        else:
            parameters = {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询内容"
                    }
                },
                "required": ["query"]
            }
        
        schema = ToolSchema(
            name=tool_name,
            description=f"{description} - 查询工具",
            parameters=parameters,
            tool_type="mcp",
            mcp_server=server_name
        )
        self.tools[tool_name] = schema
        self.logger.info(f"已创建备用MCP工具: {tool_name}")
    
    async def get_tools(self) -> List[ToolSchema]:
        """获取所有MCP工具"""
        return list(self.tools.values())
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行MCP工具"""
        self.logger.info(f"🔧 StandardMCPToolProvider执行工具: {tool_name}")
        
        if tool_name not in self.tools:
            raise ValueError(f"MCP工具 '{tool_name}' 未找到")
        
        tool = self.tools[tool_name]
        server_name = tool.mcp_server
        
        # 从工具全名中提取原始工具名称
        original_tool_name = tool.name.replace(f"{server_name}_", "", 1)
        
        try:
            result = await self.mcp_client.call_tool(server_name, original_tool_name, parameters)
            
            if result.get("success", False):
                return {
                    "success": True,
                    "result": result.get("result", ""),
                    "tool_name": tool_name,
                    "tool_type": "mcp",
                    "server": server_name
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "tool_name": tool_name,
                    "tool_type": "mcp",
                    "server": server_name
                }
        
        except Exception as e:
            self.logger.error(f"❌ MCP工具调用失败: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_type": "mcp",
                "server": server_name
            }


class MCPToolProvider(ToolProvider):
    """MCP工具提供者 - 支持连接池"""
    
    def __init__(self):
        self.servers: Dict[str, Any] = {}  # server_name -> client_session
        self.tools: Dict[str, ToolSchema] = {}
        self.logger = logging.getLogger(__name__)
        
        # 连接池：保持活跃的MCP连接
        self.active_sessions = {}  # {server_name: (session, transport)}
        self._cleanup_registered = False
        
        # 注册程序退出时的清理处理器
        self._register_cleanup_handler()
    
    def _register_cleanup_handler(self):
        """注册程序退出时的清理处理器"""
        if not self._cleanup_registered:
            import atexit
            atexit.register(self._cleanup_all_sessions)
            self._cleanup_registered = True
    
    def _cleanup_all_sessions(self):
        """清理所有活跃的MCP连接"""
        if self.active_sessions:
            self.logger.info(f"正在清理 {len(self.active_sessions)} 个MCP连接...")
            for server_name in list(self.active_sessions.keys()):
                try:
                    self._cleanup_session_sync(server_name)
                except Exception as e:
                    self.logger.error(f"清理MCP连接 {server_name} 失败: {e}")
    
    def _cleanup_session_sync(self, server_name: str):
        """同步方式清理单个连接（用于程序退出时）"""
        if server_name in self.active_sessions:
            session, transport = self.active_sessions[server_name]
            try:
                # 同步清理，不使用async
                del self.active_sessions[server_name]
                self.logger.info(f"已清理MCP连接: {server_name}")
            except Exception as e:
                self.logger.error(f"清理连接失败 {server_name}: {e}")
    
    async def get_or_create_session(self, server_name: str):
        """获取或创建MCP会话 - 连接池核心方法"""
        # 检查是否已有活跃连接
        if server_name in self.active_sessions:
            session, transport = self.active_sessions[server_name]
            try:
                # 简单检查连接是否还活跃（可以尝试ping或其他轻量级操作）
                # 这里先假设连接还活跃，真实环境中可能需要更复杂的健康检查
                return session
            except Exception as e:
                self.logger.warning(f"现有MCP连接 {server_name} 无响应，准备重新连接: {e}")
                # 清理失效连接
                await self._cleanup_session(server_name)
        
        # 创建新连接
        return await self._create_new_session(server_name)
    
    async def _create_new_session(self, server_name: str):
        """创建新的MCP会话 - 支持stdio和SSE"""
        if server_name not in self.servers:
            raise ValueError(f"MCP服务器 '{server_name}' 配置不存在")
        
        server_config = self.servers[server_name]
        transport_type = server_config.get("type", "stdio")
        
        if transport_type == "sse":
            # SSE连接（每次调用时创建新连接）
            return await self._create_sse_session(server_name)
        else:
            # stdio连接（传统持久连接）
            return await self._create_stdio_session(server_name)
    
    async def _create_stdio_session(self, server_name: str):
        """创建stdio MCP会话"""
        server_config = self.servers[server_name]
        server_params = StdioServerParameters(
            command=server_config["command"][0],
            args=server_config["command"][1:] + server_config["args"]
        )
        
        self.logger.info(f"🔗 创建新的stdio MCP连接: {server_name}")
        
        # 创建持久连接
        transport = stdio_client(server_params)
        read, write = await transport.__aenter__()
        session = ClientSession(read, write)
        await session.__aenter__()
        
        # 初始化会话
        await session.initialize()
        
        # 保存到连接池
        self.active_sessions[server_name] = (session, transport)
        
        self.logger.info(f"✅ stdio MCP连接已建立并保存到连接池: {server_name}")
        return session
    
    async def _create_sse_session(self, server_name: str):
        """创建SSE MCP会话"""
        server_config = self.servers[server_name]
        url = server_config["url"]
        headers = server_config.get("headers", {})
        
        self.logger.info(f"🔗 创建新的SSE MCP连接: {server_name}")
        
        # SSE连接不需要持久化，每次调用创建新连接
        sse_transport = SSETransport(url, headers)
        session = SSEMCPSession(sse_transport)
        
        # 注意：SSE会话的初始化在使用时进行，不保存到连接池
        self.logger.info(f"✅ SSE MCP会话已创建: {server_name}")
        return session
    
    async def _execute_sse_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any]):
        """执行SSE工具调用"""
        self.logger.info(f"🎯 开始执行SSE工具: {tool_name}")
        self.logger.info(f"   - 服务器: {server_name}")
        self.logger.info(f"   - 工具名: {tool_name}")
        self.logger.info(f"   - 参数: {parameters}")
        
        server_config = self.servers[server_name]
        self.logger.info(f"   - 服务器配置: {server_config}")
        
        url = server_config["url"]
        headers = server_config.get("headers", {})
        query_mode = server_config.get("query_mode", False)
        
        self.logger.info(f"🔗 创建SSE传输连接: {url}")
        self.logger.info(f"   - 查询模式: {query_mode}")
        self.logger.info(f"   - Headers: {headers}")
        
        if query_mode:
            # 直接查询模式：直接发送POST请求
            self.logger.info(f"📡 使用直接查询模式")
            self.logger.info(f"   - 服务器: {server_name}")
            self.logger.info(f"   - URL: {url}")
            self.logger.info(f"   - 参数: {parameters}")
            self.logger.info(f"   - 查询模式标志: {query_mode}")
            
            # 对于直接查询模式，优先使用服务器返回的消息端点
            query_url = server_config.get("message_endpoint")
            
            if not query_url:
                # 如果没有消息端点，尝试通过SSE连接获取
                self.logger.info("未找到消息端点，尝试通过SSE连接获取...")
                try:
                    sse_transport = SSETransport(url, headers)
                    async with sse_transport as (transport, _):
                        if hasattr(transport, 'message_endpoint') and transport.message_endpoint:
                            query_url = transport.message_endpoint
                            # 保存端点供后续使用
                            self.servers[server_name]["message_endpoint"] = query_url
                            self.logger.info(f"✅ 获得消息端点: {query_url}")
                        else:
                            # 如果还是没有，则使用基础URL
                            if url.endswith('/sse'):
                                query_url = url[:-4]  # 去掉 '/sse'
                                self.logger.info(f"   - 查询URL: {query_url} (从SSE URL推断)")
                            else:
                                query_url = url
                except Exception as e:
                    self.logger.warning(f"获取消息端点失败: {e}")
                    # 降级到基础URL
                    if url.endswith('/sse'):
                        query_url = url[:-4]
                    else:
                        query_url = url
            else:
                self.logger.info(f"   - 使用已保存的消息端点: {query_url}")
            
            try:
                # 构建MCP格式的请求
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "query",
                        "arguments": parameters
                    }
                }
                
                self.logger.info(f"   - 发送MCP请求: {mcp_request}")
                
                # 使用SSE传输发送请求并等待响应 - 重要：必须使用同一个连接
                sse_transport = SSETransport(url, headers)
                async with sse_transport as (transport, _):
                    self.logger.info(f"🔗 SSE连接已建立，消息端点: {transport.message_endpoint}")
                    
                    # 发送MCP请求 - 使用SSE传输的内置方法
                    result = await transport.send_message(mcp_request)
                    
                    self.logger.info(f"✅ 直接查询成功")
                    self.logger.info(f"   - 结果类型: {type(result).__name__}")
                    self.logger.info(f"   - 结果长度: {len(str(result))} 字符")
                    
                    # 显示详细结果
                    if len(str(result)) < 1000:
                        self.logger.info(f"   - 完整结果: {result}")
                    else:
                        result_str = str(result)
                        self.logger.info(f"   - 结果预览: {result_str[:300]}...{result_str[-300:]}")
                    
                    # 构建标准结果格式
                    class Content:
                        def __init__(self, text: str):
                            self.text = text
                    
                    class ToolResult:
                        def __init__(self, content: List[Content]):
                            self.content = content
                    
                    # 处理MCP响应结果
                    if isinstance(result, dict):
                        if "result" in result:
                            # 标准MCP成功响应
                            text_content = json.dumps(result["result"], ensure_ascii=False, indent=2)
                        elif "error" in result:
                            # MCP错误响应
                            text_content = f"查询错误: {result['error']}"
                        else:
                            # 其他格式
                            text_content = json.dumps(result, ensure_ascii=False, indent=2)
                    else:
                        text_content = str(result)
                    
                    return ToolResult([Content(text_content)])
                            
            except Exception as e:
                self.logger.error(f"❌ 直接查询异常: {e}")
                
                class Content:
                    def __init__(self, text: str):
                        self.text = text
                
                class ToolResult:
                    def __init__(self, content: List[Content]):
                        self.content = content
                        
                return ToolResult([Content(f"查询异常: {str(e)}")])
        else:
            # 标准MCP模式：使用MCP协议
            # 创建新的SSE传输和会话
            sse_transport = SSETransport(url, headers)
            async with sse_transport as (transport, _):
                session = SSEMCPSession(transport)
                
                # 调用工具
                self.logger.info(f"📞 正在调用SSE MCP工具...")
                result = await session.call_tool(name=tool_name, arguments=parameters)
                
                return result
    
    async def _cleanup_session(self, server_name: str):
        """清理单个MCP会话"""
        if server_name in self.active_sessions:
            session, transport = self.active_sessions[server_name]
            try:
                await session.__aexit__(None, None, None)
                await transport.__aexit__(None, None, None)
            except Exception as e:
                self.logger.warning(f"清理MCP会话异常 {server_name}: {e}")
            finally:
                del self.active_sessions[server_name]
                self.logger.info(f"MCP会话已清理: {server_name}")

    async def connect_server(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """连接MCP服务器 - 支持stdio和SSE传输方式"""
        
        # 解析服务器配置
        transport_type = server_config.get("type", "stdio")  # 默认stdio
        
        if transport_type == "sse":
            # SSE传输方式
            await self._connect_sse_server(server_name, server_config)
        else:
            # stdio传输方式（默认）
            await self._connect_stdio_server(server_name, server_config)
    
    async def _connect_stdio_server(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """连接stdio MCP服务器"""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP SDK not available")
        
        try:
            # 兼容旧的配置格式
            server_command = server_config.get("command", [])
            server_args = server_config.get("args", [])
            
            # 保存服务器配置供连接池使用
            self.servers[server_name] = {
                "type": "stdio",
                "command": server_command,
                "args": server_args,
                "connected": False
            }
            
            self.logger.info(f"正在连接stdio MCP服务器 '{server_name}': {server_command}")
            
            # 使用连接池创建初始连接
            session = await self._create_new_session(server_name)
            
            # 获取服务器工具
            tools_result = await session.list_tools()
            self.logger.info(f"发现 {len(tools_result.tools)} 个工具从服务器 '{server_name}'")
            
            # 注册工具
            for tool in tools_result.tools:
                # 转换工具参数schema
                parameters = {}
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    parameters = tool.inputSchema.model_dump() if hasattr(tool.inputSchema, 'model_dump') else tool.inputSchema
                
                tool_full_name = f"{server_name}_{tool.name}"
                schema = ToolSchema(
                    name=tool_full_name,  # 使用一致的命名格式
                    description=tool.description,
                    parameters=parameters,
                    tool_type="mcp",
                    mcp_server=server_name
                )
                self.tools[tool_full_name] = schema  # 存储键与工具名称一致
                self.logger.info(f"已注册MCP工具: {schema.name}")
            
            # 标记为已连接
            self.servers[server_name]["connected"] = True
            
            self.logger.info(f"✅ 成功连接到MCP服务器 '{server_name}'，共 {len(tools_result.tools)} 个工具")
            
        except Exception as e:
            self.logger.error(f"❌ 连接MCP服务器失败 '{server_name}': {e}")
            # 清理失败的配置
            if server_name in self.servers:
                del self.servers[server_name]
            # 不抛出异常，让程序继续运行
    
    async def _connect_sse_server(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """连接SSE MCP服务器"""
        try:
            # 解析SSE配置
            url = server_config.get("url")
            headers = server_config.get("headers", {})
            description = server_config.get("description", "SSE查询服务")
            
            if not url:
                raise ValueError(f"SSE服务器 '{server_name}' 缺少url配置")
            
            # 保存服务器配置供连接池使用
            self.servers[server_name] = {
                "type": "sse",
                "url": url,
                "headers": headers,
                "connected": False,
                "query_mode": False,  # 初始假设为标准模式
                "message_endpoint": None  # 存储消息端点
            }
            
            self.logger.info(f"正在连接SSE MCP服务器 '{server_name}': {url}")
            
            # 首先尝试标准MCP模式
            try:
                # 创建SSE传输和会话
                sse_transport = SSETransport(url, headers)
                async with sse_transport as (transport, _):
                    # 保存消息端点（如果有）
                    if hasattr(transport, 'message_endpoint') and transport.message_endpoint:
                        self.servers[server_name]["message_endpoint"] = transport.message_endpoint
                        self.logger.info(f"发现消息端点: {transport.message_endpoint}")
                    
                    session = SSEMCPSession(transport)
                    
                    # 初始化会话
                    await session.initialize()
                    
                    # 获取服务器工具
                    tools_result = await session.list_tools()
                    self.logger.info(f"发现 {len(tools_result.tools)} 个工具从SSE服务器 '{server_name}'")
                    
                    if tools_result.tools:
                        # 有工具列表，使用标准模式
                        for tool in tools_result.tools:
                            # 转换工具参数schema
                            parameters = {}
                            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                                parameters = tool.inputSchema.model_dump() if hasattr(tool.inputSchema, 'model_dump') else tool.inputSchema
                            
                            tool_full_name = f"{server_name}_{tool.name}"
                            schema = ToolSchema(
                                name=tool_full_name,
                                description=tool.description,
                                parameters=parameters,
                                tool_type="mcp",
                                mcp_server=server_name
                            )
                            self.tools[tool_full_name] = schema
                            self.logger.info(f"已注册SSE MCP工具: {schema.name}")
                        
                        # 标记为已连接
                        self.servers[server_name]["connected"] = True
                        self.logger.info(f"✅ 成功连接到SSE MCP服务器 '{server_name}'，共 {len(tools_result.tools)} 个工具")
                    else:
                        # 没有工具列表，可能是直接查询模式
                        self.logger.warning(f"SSE服务器 '{server_name}' 未返回工具列表，可能不是标准MCP服务器")
                        raise Exception("No tools found, might be a direct query server")
                        
            except Exception as e:
                self.logger.warning(f"无法通过标准MCP协议获取工具列表: {e}")
                self.logger.info(f"尝试将 '{server_name}' 作为直接查询服务器")
                
                # 降级为直接查询模式
                self.servers[server_name]["query_mode"] = True
                
                # 创建虚拟工具 - 从服务器描述推断工具名
                tool_name = f"{server_name}_query"
                
                # 基于服务器描述生成合适的参数schema
                if "知识库" in description or "knowledge" in description.lower():
                    # 知识库类查询
                    parameters = {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "查询内容"
                            },
                            "similarity": {
                                "type": "number",
                                "description": "相似度阈值",
                                "default": 0.6
                            },
                            "search_mode": {
                                "type": "string",
                                "description": "搜索模式",
                                "default": "mixedRecall",
                                "enum": ["mixedRecall", "embedding", "fullText"]
                            }
                        },
                        "required": ["message"]
                    }
                else:
                    # 通用查询
                    parameters = {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "查询内容"
                            }
                        },
                        "required": ["query"]
                    }
                
                schema = ToolSchema(
                    name=tool_name,
                    description=description,
                    parameters=parameters,
                    tool_type="mcp",
                    mcp_server=server_name
                )
                self.tools[tool_name] = schema
                self.logger.info(f"已为SSE服务器创建虚拟工具: {tool_name}")
                
                # 标记为已连接
                self.servers[server_name]["connected"] = True
                self.logger.info(f"✅ 以直接查询模式连接到SSE服务器 '{server_name}'")
                
        except Exception as e:
            self.logger.error(f"❌ 连接SSE MCP服务器失败 '{server_name}': {e}")
            # 清理失败的配置
            if server_name in self.servers:
                del self.servers[server_name]
            # 不抛出异常，让程序继续运行
    
    async def get_tools(self) -> List[ToolSchema]:
        """获取所有MCP工具"""
        return list(self.tools.values())
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行MCP工具 - 使用连接池"""
        self.logger.info(f"🔧 MCPToolProvider执行工具: {tool_name}")
        self.logger.info(f"   - 可用工具列表: {list(self.tools.keys())}")
        
        if tool_name not in self.tools:
            self.logger.error(f"❌ MCP工具 '{tool_name}' 未在工具列表中找到")
            raise ValueError(f"MCP tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        server_name = tool.mcp_server
        
        self.logger.info(f"   - 找到工具: {tool_name}")
        self.logger.info(f"   - 服务器: {server_name}")
        self.logger.info(f"   - 工具类型: {tool.tool_type}")
        
        if server_name not in self.servers:
            self.logger.error(f"❌ MCP服务器 '{server_name}' 未连接")
            raise ValueError(f"MCP server '{server_name}' not connected")
        
        try:
            # 从工具全名中提取原始工具名称
            original_tool_name = tool.name.replace(f"{server_name}_", "", 1)
            server_config = self.servers[server_name]
            transport_type = server_config.get("type", "stdio")
            
            self.logger.info(f"🔧 MCP工具调用开始: {tool_name}")
            self.logger.info(f"   - 服务器: {server_name}")
            self.logger.info(f"   - 传输类型: {transport_type}")
            self.logger.info(f"   - 原始工具名: {original_tool_name}")
            self.logger.info(f"   - 参数: {parameters}")
            
            # 根据传输类型选择不同的调用方式
            if transport_type == "sse":
                # SSE工具调用 - 每次创建新连接
                result = await self._execute_sse_tool(server_name, original_tool_name, parameters)
            else:
                # stdio工具调用 - 使用连接池
                self.logger.info(f"🔗 从连接池获取stdio MCP会话...")
                session = await self.get_or_create_session(server_name)
                
                # 调用MCP工具
                self.logger.info(f"📞 正在调用stdio MCP工具...")
                result = await session.call_tool(
                    name=original_tool_name,  # 使用原始工具名称
                    arguments=parameters
                )
            
            self.logger.info(f"✅ MCP工具调用成功: {tool_name}")
            
            # 处理MCP返回结果，提取文本内容
            result_content = []
            if hasattr(result, 'content') and result.content:
                for item in result.content:
                    if hasattr(item, 'text'):
                        result_content.append(item.text)
                    else:
                        result_content.append(str(item))
            
            result_text = '\n'.join(result_content) if result_content else str(result.content)
            self.logger.info(f"   - 结果长度: {len(result_text)} 字符")
            
            # 如果结果很长，显示摘要
            if len(result_text) > 1000:
                preview = result_text[:200] + "..." + result_text[-200:]
                self.logger.info(f"   - 结果预览: {preview}")
            
            return {
                "success": True,
                "result": result_text,  # 使用处理后的文本结果
                "tool_name": tool_name,
                "tool_type": "mcp",
                "server": server_name
            }
        
        except Exception as e:
            self.logger.error(f"❌ MCP工具调用失败: {tool_name}")
            self.logger.error(f"   - 错误: {str(e)}")
            self.logger.error(f"   - 错误类型: {type(e).__name__}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_type": "mcp",
                "server": server_name
            }


class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self, use_standard_mcp: bool = True):
        self.function_provider = FunctionToolProvider()
        
        # 选择MCP提供者
        if use_standard_mcp and STANDARD_MCP_AVAILABLE:
            self.mcp_provider = StandardMCPToolProvider()
            self.logger = logging.getLogger(__name__)
            self.logger.info("使用标准MCP工具提供者")
        else:
            self.mcp_provider = MCPToolProvider()
            self.logger = logging.getLogger(__name__)
            self.logger.info("使用旧版MCP工具提供者")
        
        self._use_standard_mcp = use_standard_mcp and STANDARD_MCP_AVAILABLE
    
    def register_function(self, name: str, description: str, parameters: Dict[str, Any], 
                         function: Callable) -> None:
        """注册函数工具"""
        self.function_provider.register_function(name, description, parameters, function)
        self.logger.info(f"Registered function tool: {name}")
    
    async def register_mcp_server(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """注册MCP服务器 - 支持stdio和SSE传输方式"""
        transport_type = server_config.get("type", "stdio")
        
        if self._use_standard_mcp:
            # 使用标准MCP客户端
            if transport_type == "sse":
                url = server_config.get("url")
                headers = server_config.get("headers", {})
                description = server_config.get("description")
                await self.mcp_provider.register_sse_server(server_name, url, headers, description)
            else:
                command = server_config.get("command", [])
                args = server_config.get("args", [])
                description = server_config.get("description")
                await self.mcp_provider.register_stdio_server(server_name, command, args, description)
        else:
            # 使用旧版MCP提供者
            if transport_type == "sse":
                self.logger.info(f"Registering SSE MCP server: {server_name}")
            elif not MCP_AVAILABLE:
                self.logger.warning(f"Cannot register stdio MCP server '{server_name}': MCP SDK not available")
                return
            
            await self.mcp_provider.connect_server(server_name, server_config)
        
        self.logger.info(f"Registered MCP server: {server_name} (type: {transport_type})")
    
    async def get_all_tools(self) -> List[ToolSchema]:
        """获取所有可用工具"""
        tools = []
        
        # 获取函数工具
        function_tools = await self.function_provider.get_tools()
        tools.extend(function_tools)
        
        # 获取MCP工具
        mcp_tools = await self.mcp_provider.get_tools()
        tools.extend(mcp_tools)
        
        return tools
    
    async def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的OpenAI Function Call格式schema"""
        tools = await self.get_all_tools()
        return [tool.to_openai_schema() for tool in tools]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定工具"""
        self.logger.info(f"🎯 ToolRegistry执行工具: {tool_name}")
        self.logger.info(f"   - 参数: {parameters}")
        
        # 先尝试函数工具
        try:
            self.logger.info(f"   - 尝试函数工具...")
            result = await self.function_provider.execute_tool(tool_name, parameters)
            self.logger.info(f"   - ✅ 函数工具执行成功")
            return result
        except ValueError as e:
            self.logger.info(f"   - ❌ 函数工具未找到: {e}")
            pass
        
        # 再尝试MCP工具
        try:
            self.logger.info(f"   - 尝试MCP工具...")
            result = await self.mcp_provider.execute_tool(tool_name, parameters)
            self.logger.info(f"   - ✅ MCP工具执行成功")
            return result
        except ValueError as e:
            self.logger.info(f"   - ❌ MCP工具未找到: {e}")
            pass
        
        # 工具未找到
        self.logger.error(f"❌ 工具未在任何提供者中找到: {tool_name}")
        raise ValueError(f"Tool '{tool_name}' not found in any provider")
    
    async def get_tool_info(self, tool_name: str) -> Optional[ToolSchema]:
        """获取工具信息"""
        tools = await self.get_all_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取注册中心状态"""
        return {
            "function_tools_count": len(self.function_provider.tools),
            "mcp_servers_count": len(self.mcp_provider.servers),
            "mcp_tools_count": len(self.mcp_provider.tools),
            "mcp_available": MCP_AVAILABLE
        }


# 内置工具函数示例
def calculator_add(a: float, b: float) -> float:
    """加法计算器"""
    return a + b

def calculator_multiply(a: float, b: float) -> float:
    """乘法计算器"""
    return a * b

def text_length(text: str) -> int:
    """计算文本长度"""
    return len(text)

def text_upper(text: str) -> str:
    """转换为大写"""
    return text.upper()


def create_default_registry() -> ToolRegistry:
    """创建默认的工具注册中心，包含基础工具"""
    registry = ToolRegistry()
    
    # 注册基础数学工具
    registry.register_function(
        name="add",
        description="Add two numbers",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        },
        function=calculator_add
    )
    
    registry.register_function(
        name="multiply",
        description="Multiply two numbers",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        },
        function=calculator_multiply
    )
    
    # 注册文本工具
    registry.register_function(
        name="text_length",
        description="Get the length of a text string",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Input text"}
            },
            "required": ["text"]
        },
        function=text_length
    )
    
    registry.register_function(
        name="text_upper",
        description="Convert text to uppercase",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Input text"}
            },
            "required": ["text"]
        },
        function=text_upper
    )
    
    return registry