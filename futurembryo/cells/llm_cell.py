"""
LLMCell - 语言模型Cell实现

支持OpenAI兼容的API调用，自动使用全局配置
新增Function Calling支持，保持向后兼容
"""
import openai
import time
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from ..core.cell import Cell
from ..core.config import get_api_key, get_api_base_url, get_config
from ..core.exceptions import CellConfigurationError, APIKeyError


class LLMCell(Cell):
    """语言模型Cell - 调用LLM生成文本响应"""
    
    def __init__(self, model_name: Optional[str] = None, config: Optional[Dict[str, Any]] = None,
                 tool_cell: Optional['ToolCell'] = None):
        """
        初始化LLMCell
        
        Args:
            model_name: 模型名称，如果为None则使用全局默认模型
            config: Cell配置，可包含以下参数：
                - api_key: API密钥（覆盖全局配置）
                - base_url: API基础URL（覆盖全局配置）
                - timeout: 执行超时时间（秒）
                - temperature: 温度参数（覆盖全局配置）
                - max_tokens: 最大token数
                - system_prompt: 系统提示词
                - max_retries: 最大重试次数（默认3）
                - retry_delay: 重试延迟秒数（默认1）
                - timeout: 请求超时时间（默认30秒）
                
                # 新增Function Calling配置
                - tool_choice: 工具选择策略 ("auto", "none", "required")
                - max_tool_calls: 最大工具调用次数（防止循环调用）
                - enable_tools: 是否启用工具功能（默认根据tool_cell判断）
                
            tool_cell: 工具Cell实例（可选，用于Function Calling）
        """
        super().__init__(config)
        
        # 基础模型配置（保持向后兼容）
        self.model_name = model_name or get_config("default_model", "gpt-3.5-turbo")
        self.temperature = self.config.get("temperature", get_config("default_temperature", 0.7))
        self.max_tokens = self.config.get("max_tokens", 1000)
        self.system_prompt = self.config.get("system_prompt", "You are a helpful AI assistant.")
        
        # 容错配置（保持向后兼容）
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1)
        # LLM请求超时（与Cell执行超时分开）
        self.request_timeout = self.config.get("request_timeout", 30)
        
        # 新增：Function Calling配置
        self.tool_choice = self.config.get("tool_choice", "auto")
        self.max_tool_calls = self.config.get("max_tool_calls", 5)
        self.enable_tools = self.config.get("enable_tools", tool_cell is not None)
        
        # API配置（支持局部覆盖）
        try:
            self.api_key = self.config.get("api_key") or get_api_key("openai")
        except APIKeyError as e:
            raise CellConfigurationError(f"No API key found for LLMCell. {str(e)}")
        
        self.base_url = self.config.get("base_url") or get_api_base_url("openai")
        
        # 初始化OpenAI客户端
        client_kwargs = {"api_key": self.api_key, "timeout": self.timeout}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = openai.OpenAI(**client_kwargs)
        
        # 新增：工具Cell
        self.tool_cell = tool_cell
        
        # 日志信息
        self.logger.info(f"Initialized LLMCell with model: {self.model_name}")
        if self.tool_cell and self.enable_tools:
            self.logger.info("Function Calling support enabled with ToolCell")
        if self.base_url:
            self.logger.info(f"Using custom base URL: {self.base_url}")
        self.logger.info(f"Fault tolerance: max_retries={self.max_retries}, timeout={self.timeout}s")
    
    def set_tool_cell(self, tool_cell: 'ToolCell'):
        """设置工具Cell（可在初始化后设置）"""
        self.tool_cell = tool_cell
        if not self.config.get("enable_tools_explicit", False):
            self.enable_tools = True
        self.logger.info("ToolCell attached to LLMCell")
    
    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具（新增功能）"""
        if not self.tool_cell or not self.enable_tools:
            return []
        return await self.tool_cell.get_available_tools()
    
    async def _call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具（新增功能）"""
        if not self.tool_cell:
            raise ValueError("No ToolCell available for tool calling")
        return await self.tool_cell.call_tool(tool_name, parameters)
    
    def _make_llm_request_with_retry(self, final_messages: List[Dict], temperature: float, max_tokens: int,
                                   tools: Optional[List[Dict]] = None,
                                   tool_choice: Optional[Union[str, Dict]] = None) -> Dict[str, Any]:
        """
        带重试机制的LLM请求（增强版，支持Function Calling）
        
        Args:
            final_messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 可用工具列表（新增）
            tool_choice: 工具选择策略（新增）
            
        Returns:
            Dict: LLM响应结果
            
        Raises:
            Exception: 所有重试失败后抛出最后一个异常
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Making LLM request (attempt {attempt + 1}/{self.max_retries + 1})")
                
                # 构建请求参数（保持向后兼容）
                request_params = {
                    "model": self.model_name,
                    "messages": final_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                # 新增：添加工具参数（仅在启用时）
                if tools and self.enable_tools:
                    request_params["tools"] = tools
                    if tool_choice:
                        request_params["tool_choice"] = tool_choice
                
                # 调用OpenAI API
                response = self.client.chat.completions.create(**request_params)
                
                # 解析响应（增强版）
                message = response.choices[0].message
                usage = response.usage
                
                self.logger.info(f"LLM response received, tokens used: {usage.total_tokens}")
                
                # 构建结果（保持向后兼容）
                result = {
                    "response": message.content,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    },
                    "model": self.model_name,
                    "finish_reason": response.choices[0].finish_reason
                }
                
                # 新增：处理工具调用
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    result["tool_calls"] = []
                    for tool_call in message.tool_calls:
                        result["tool_calls"].append({
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        })
                
                # 更新消息历史
                new_message = {"role": "assistant", "content": message.content}
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    new_message["tool_calls"] = result["tool_calls"]
                
                result["messages"] = final_messages + [new_message]
                
                return result
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # 判断是否应该重试
                should_retry = self._should_retry_error(error_msg)
                
                if attempt < self.max_retries and should_retry:
                    self.logger.warning(f"LLM request failed (attempt {attempt + 1}): {error_msg}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self.logger.error(f"LLM request failed after {attempt + 1} attempts: {error_msg}")
                    break
        
        # 所有重试都失败，尝试降级方案
        return self._fallback_response(final_messages, last_exception)
    
    def _should_retry_error(self, error_msg: str) -> bool:
        """
        判断错误是否应该重试
        
        Args:
            error_msg: 错误消息
            
        Returns:
            bool: 是否应该重试
        """
        # 网络相关错误应该重试
        retry_keywords = [
            "timeout", "timed out", "connection", "network", 
            "503", "502", "500", "429", "rate limit"
        ]
        
        error_lower = error_msg.lower()
        return any(keyword in error_lower for keyword in retry_keywords)
    
    def _fallback_response(self, messages: List[Dict], original_error: Exception) -> Dict[str, Any]:
        """
        降级响应方案
        
        Args:
            messages: 原始消息列表
            original_error: 原始错误
            
        Returns:
            Dict: 降级响应结果
        """
        self.logger.warning("Using fallback response due to LLM API failure")
        
        # 提取用户问题
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # 生成智能降级回复
        fallback_response = self._generate_intelligent_fallback(user_message, original_error)
        
        return {
            "response": fallback_response,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "model": f"{self.model_name}_fallback",
            "messages": messages + [{"role": "assistant", "content": fallback_response}],
            "is_fallback": True,
            "original_error": str(original_error)
        }
    
    def _generate_intelligent_fallback(self, user_input: str, error: Exception) -> str:
        """
        生成智能降级回复
        
        Args:
            user_input: 用户输入
            error: 原始错误
            
        Returns:
            str: 降级回复内容
        """
        error_type = type(error).__name__
        
        if "timeout" in str(error).lower():
            return f"抱歉，由于网络超时，我暂时无法处理您的问题：'{user_input}'。请稍后重试，或者您可以重新表述您的问题。"
        elif "connection" in str(error).lower():
            return f"抱歉，由于网络连接问题，我暂时无法回复您的问题：'{user_input}'。请检查网络连接后重试。"
        elif "rate limit" in str(error).lower():
            return f"抱歉，由于请求频率限制，我暂时无法处理您的问题：'{user_input}'。请稍等片刻后重试。"
        else:
            return f"抱歉，我遇到了技术问题（{error_type}），暂时无法回复您的问题：'{user_input}'。请稍后重试。"

    async def _process_tool_calls(self, messages: List[Dict], tool_calls: List[Dict]) -> List[Dict]:
        """处理工具调用（新增功能）"""
        updated_messages = messages.copy()
        
        for tool_call in tool_calls:
            try:
                # 解析工具调用
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                self.logger.info(f"🔧 准备调用工具: {function_name}")
                
                # 获取工具类型信息
                tool_type = "Unknown"
                if self.tool_cell:
                    try:
                        registry = self.tool_cell.get_tool_registry()
                        tool_info = await registry.get_tool_info(function_name)
                        tool_type = tool_info.tool_type.upper() if tool_info else "Unknown"
                    except Exception as e:
                        self.logger.debug(f"获取工具类型失败: {e}")
                        # 降级到基于前缀的判断
                        tool_type = 'MCP' if ('_' in function_name and not function_name.startswith('query_')) else 'Function'
                
                self.logger.info(f"   - 工具类型: {tool_type}")
                self.logger.info(f"   - 参数: {function_args}")
                
                # 调用工具
                tool_result = await self._call_tool(function_name, function_args)
                
                # 构建工具响应消息
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False)
                }
                
                updated_messages.append(tool_message)
                
                self.logger.info(f"✅ 工具调用完成: {function_name}")
                self.logger.info(f"   - 返回数据类型: {type(tool_result).__name__}")
                self.logger.info(f"   - 返回数据长度: {len(str(tool_result))} 字符")
                
                # 显示详细的返回内容
                if len(str(tool_result)) < 2000:  # 如果不太长，显示全部
                    self.logger.info(f"   - 完整返回内容: {tool_result}")
                else:  # 如果太长，显示前后部分
                    result_str = str(tool_result)
                    self.logger.info(f"   - 返回内容预览: {result_str[:500]}...{result_str[-500:]}")
                
            except Exception as e:
                # 工具调用失败，添加错误消息
                error_msg = {"error": str(e)}
                error_message = {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(error_msg, ensure_ascii=False)
                }
                
                updated_messages.append(error_message)
                
                self.logger.error(f"❌ 工具执行失败: {function_name}")
                self.logger.error(f"   - 错误: {str(e)}")
                self.logger.error(f"   - 错误类型: {type(e).__name__}")
        
        return updated_messages
    
    async def _handle_conversation_with_tools(self, messages: List[Dict], temperature: float,
                                            max_tokens: int) -> Dict[str, Any]:
        """处理带工具调用的对话（新增功能）"""
        current_messages = messages.copy()
        tool_call_count = 0
        
        # 获取可用工具
        available_tools = await self._get_available_tools()
        
        while tool_call_count < self.max_tool_calls:
            # 调用LLM
            response = self._make_llm_request_with_retry(
                current_messages, temperature, max_tokens,
                tools=available_tools if available_tools else None,
                tool_choice=self.tool_choice if available_tools else None
            )
            
            # 检查是否有工具调用
            if "tool_calls" not in response or not response["tool_calls"]:
                # 没有工具调用，返回最终结果
                return response
            
            # 处理工具调用
            tool_call_count += 1
            current_messages = await self._process_tool_calls(
                response["messages"], response["tool_calls"]
            )
            
            self.logger.info(f"Completed tool call round {tool_call_count}")
        
        # 达到最大工具调用次数，进行最后一次LLM调用（不允许工具调用）
        self.logger.warning(f"Reached maximum tool calls limit ({self.max_tool_calls})")
        final_response = self._make_llm_request_with_retry(
            current_messages, temperature, max_tokens,
            tools=None, tool_choice=None
        )
        
        return final_response

    def _handle_conversation_with_tools_sync(self, messages: List[Dict], temperature: float,
                                           max_tokens: int) -> Dict[str, Any]:
        """处理带工具调用的对话（同步版本，避免事件循环冲突）"""
        import concurrent.futures
        import threading
        
        def run_async_in_thread():
            """在新线程中运行异步代码"""
            self.logger.info("🧵 启动新线程执行异步工具调用...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self.logger.info("🔄 线程内异步循环开始...")
                result = loop.run_until_complete(
                    self._handle_conversation_with_tools(messages, temperature, max_tokens)
                )
                self.logger.info("✅ 线程内异步调用完成")
                return result
            except Exception as e:
                self.logger.error(f"❌ 线程内异步调用失败: {e}")
                raise
            finally:
                loop.close()
                self.logger.info("🔚 线程内异步循环关闭")
        
        # 在线程池中执行异步操作
        self.logger.info("🚀 开始线程池工具调用...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_in_thread)
            try:
                # 等待结果，设置超时
                self.logger.info("⏳ 等待工具调用结果，最大超时180秒...")
                result = future.result(timeout=180)  # 3分钟超时，给MCP更多时间
                self.logger.info("🎉 线程池工具调用成功完成")
                return result
            except concurrent.futures.TimeoutError:
                self.logger.error("⏰ 工具调用超时 (180秒)")
                # 返回简单的LLM响应作为fallback
                return self._make_llm_request_with_retry(messages, temperature, max_tokens)
            except Exception as e:
                self.logger.error(f"💥 线程池工具调用失败: {e}")
                # 返回简单的LLM响应作为fallback
                return self._make_llm_request_with_retry(messages, temperature, max_tokens)

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理LLM请求（增强版，向后兼容）
        
        Args:
            context: 包含以下字段的字典：
                # 原有字段（保持向后兼容）
                - input: 用户输入文本（可选）
                - messages: 完整的消息列表（可选，优先级高于input）
                - system_prompt: 临时系统提示词（可选，覆盖默认）
                - temperature: 临时温度参数（可选，覆盖默认）
                - max_tokens: 临时最大token数（可选，覆盖默认）
                
                # 新增字段
                - enable_tools: 是否启用工具调用（可选，覆盖实例设置）
                
        Returns:
            Dict包含：
                # 原有字段（保持向后兼容）
                - response: LLM生成的响应文本
                - usage: token使用统计
                - model: 使用的模型名称
                
                # 新增字段
                - tool_calls: 工具调用信息（如果有）
        """
        # 提取输入（保持向后兼容）
        user_input = context.get("input")
        messages = context.get("messages")
        enable_tools = context.get("enable_tools", self.enable_tools)
        
        if not messages and not user_input:
            raise CellConfigurationError("Either 'input' or 'messages' must be provided")
        
        # 构建消息列表（保持向后兼容）
        if messages:
            final_messages = messages
        else:
            system_prompt = context.get("system_prompt", self.system_prompt)
            final_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        
        # 获取临时参数（保持向后兼容）
        temperature = context.get("temperature", self.temperature)
        max_tokens = context.get("max_tokens", self.max_tokens)
        
        # 处理对话（增强版）
        if enable_tools and self.tool_cell:
            # 新功能：处理工具调用 - 使用同步版本避免事件循环冲突
            try:
                self.logger.info("Processing conversation with tools enabled")
                result = self._handle_conversation_with_tools_sync(final_messages, temperature, max_tokens)
            except Exception as e:
                self.logger.error(f"Tool-enabled conversation failed: {e}")
                # 降级到不使用工具的方式
                result = self._make_llm_request_with_retry(final_messages, temperature, max_tokens)
        else:
            # 原功能：不使用工具的普通对话
            result = self._make_llm_request_with_retry(final_messages, temperature, max_tokens)
        
        return result
    
    def chat(self, message: str, system_prompt: Optional[str] = None, 
             enable_tools: Optional[bool] = None) -> str:
        """
        便捷的对话方法（增强版，向后兼容）
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词（可选）
            enable_tools: 是否启用工具调用（可选，新增参数）
            
        Returns:
            str: LLM的响应文本
        """
        context = {"input": message}
        if system_prompt:
            context["system_prompt"] = system_prompt
        if enable_tools is not None:
            context["enable_tools"] = enable_tools
        
        result = self(context)
        
        if result["success"]:
            return result["data"]["response"]
        else:
            raise Exception(f"Chat failed: {result['error']}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取LLMCell状态（增强版，向后兼容）"""
        status = super().get_status()
        status.update({
            # 原有状态字段
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_configured": bool(self.api_key),
            "base_url": self.base_url,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            
            # 新增状态字段
            "tool_support": {
                "enabled": self.enable_tools,
                "tool_cell_attached": self.tool_cell is not None,
                "tool_choice": self.tool_choice,
                "max_tool_calls": self.max_tool_calls
            }
        })
        return status


# 向后兼容：提供工厂函数
def create_llm_with_tools(model_name: Optional[str] = None, 
                         llm_config: Optional[Dict[str, Any]] = None,
                         tool_config: Optional[Dict[str, Any]] = None) -> LLMCell:
    """
    创建带工具支持的LLMCell（新功能）
    
    Args:
        model_name: 模型名称
        llm_config: LLM配置
        tool_config: 工具配置
        
    Returns:
        LLMCell: 配置好的LLMCell实例
    """
    from .tool_cell import ToolCell
    
    # 创建工具Cell
    tool_cell = ToolCell(tool_config)
    
    # 创建LLMCell
    llm_cell = LLMCell(model_name, llm_config, tool_cell)
    
    return llm_cell 