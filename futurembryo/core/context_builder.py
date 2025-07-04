"""
智能上下文构建器 - IntelligentContextBuilder

统一管理五大组件的上下文：
1. MindCell(思考过程) 
2. 对话历史
3. StateMemoryCell(记忆) 
4. ToolCell(工具) 
5. 其他上下文(扩展)
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from ..cells.mind_cell import MindCell
from ..cells.state_memory_cell import StateMemoryCell
from ..cells.tool_cell import ToolCell
from ..cells.llm_cell import LLMCell
from ..core.config import get_config


class IntelligentContextBuilder:
    """智能上下文构建和管理器"""
    
    def __init__(self, 
                 max_tokens: int = 4000,
                 compression_threshold: float = 0.8,  # 80%时开始压缩
                 summary_model: str = "gpt-3.5-turbo",
                 conversation_history_limit: int = 10,  # 显示对话历史条数
                 message_max_length: int = 500):  # 单条消息最大显示长度
        """
        初始化智能上下文构建器
        
        Args:
            max_tokens: 最大token数
            compression_threshold: 压缩阈值（0.0-1.0）
            summary_model: 用于总结的模型
            conversation_history_limit: 显示对话历史的条数
            message_max_length: 单条消息最大显示长度
        """
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold
        self.summary_model = summary_model
        self.conversation_history_limit = conversation_history_limit
        self.message_max_length = message_max_length
        
        # 初始化各组件
        self.mind_cell = None
        self.memory_cell = None
        self.tool_cell = None
        self.summarizer = ContextSummarizer(summary_model)
        
        # 上下文缓存
        self.context_cache = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("IntelligentContextBuilder initialized")
    
    def initialize_components(self, config: Dict[str, Any] = None):
        """初始化各个组件"""
        config = config or {}
        
        # 初始化MindCell
        mind_config = config.get("mind_cell", {})
        self.mind_cell = MindCell(mind_config)
        
        # 初始化StateMemoryCell
        memory_config = config.get("memory_cell", {})
        self.memory_cell = StateMemoryCell(memory_config)
        
        # 初始化ToolCell
        tool_config = config.get("tool_cell", {})
        self.tool_cell = ToolCell(tool_config)
        
        self.logger.info("All components initialized")
    
    async def build_full_context(
        self,
        user_input: str,
        conversation_history: List[Dict] = None,
        # 组件开关
        enable_thinking: bool = True,
        enable_memory: bool = True,
        enable_tools: bool = True,
        enable_compression: bool = True,
        # 具体配置
        thinking_mode: str = "chain_of_thought",
        memory_search_mode: str = "hybrid",
        selected_tools: List[str] = None,
        mind_rule: str = None,
        # 其他上下文
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        构建完整的智能上下文
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            enable_thinking: 是否启用思考过程
            enable_memory: 是否启用记忆检索
            enable_tools: 是否启用工具调用
            enable_compression: 是否启用智能压缩
            thinking_mode: 思考模式
            memory_search_mode: 记忆搜索模式
            selected_tools: 指定的工具列表
            mind_rule: 思维规则（可选）
            additional_context: 额外的上下文信息
            
        Returns:
            完整的上下文字典
        """
        context_components = {}
        
        # 1. 构建思考上下文
        if enable_thinking and self.mind_cell:
            thinking_context = await self._build_thinking_context(
                user_input, conversation_history, thinking_mode, mind_rule
            )
            context_components["thinking"] = thinking_context
        
        # 2. 构建记忆上下文
        if enable_memory and self.memory_cell:
            memory_context = await self._build_memory_context(
                user_input, conversation_history, memory_search_mode
            )
            context_components["memory"] = memory_context
        
        # 3. 构建工具上下文
        if enable_tools and self.tool_cell:
            tool_context = await self._build_tool_context(
                user_input, conversation_history, selected_tools
            )
            context_components["tools"] = tool_context
        
        # 4. 处理对话历史
        conversation_context = self._build_conversation_context(conversation_history)
        context_components["conversation"] = conversation_context
        
        # 5. 添加其他上下文
        if additional_context:
            context_components["additional"] = additional_context
        
        # 6. 组合完整上下文
        full_context = await self._combine_contexts(
            context_components, user_input, enable_compression
        )
        
        return full_context
    
    async def _build_thinking_context(
        self, 
        user_input: str, 
        conversation_history: List[Dict], 
        thinking_mode: str,
        mind_rule: str = None
    ) -> Dict[str, Any]:
        """构建思考上下文 - 使用异步版本避免事件循环冲突"""
        try:
            # 构建思考请求
            thinking_request = {
                "action": "generate_thinking",
                "user_input": user_input,
                "conversation_context": self._format_conversation_for_thinking(conversation_history),
                "thinking_mode": thinking_mode,
                "mind_rule": mind_rule
            }
            
            # 使用异步版本执行思考过程
            thinking_result = await self.mind_cell.process_async(thinking_request)
            
            return {
                "thinking_process": thinking_result.get("thinking_process", ""),
                "reasoning_steps": thinking_result.get("reasoning_steps", []),
                "conclusion": thinking_result.get("conclusion", ""),
                "confidence": thinking_result.get("confidence", 0.0),
                "mode": thinking_mode,
                "enabled": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build thinking context: {e}")
            return {
                "thinking_process": f"思考过程生成失败: {str(e)}",
                "reasoning_steps": [],
                "conclusion": "无法生成思考过程",
                "confidence": 0.0,
                "mode": thinking_mode,
                "enabled": False,
                "error": str(e)
            }
    
    async def _build_memory_context(
        self, 
        user_input: str, 
        conversation_history: List[Dict], 
        search_mode: str
    ) -> Dict[str, Any]:
        """构建记忆上下文"""
        try:
            # 构建记忆检索请求
            memory_request = {
                "action": "retrieve",
                "query": user_input,
                "memory_type": "all",
                "search_mode": search_mode,
                "limit": 5
            }
            
            # 执行记忆检索
            memory_result = self.memory_cell.process(memory_request)
            
            if memory_result.get("success", False):
                memories = memory_result.get("data", {}).get("memories", [])
                formatted_memories = self._format_memories_for_context(memories)
                
                return {
                    "retrieved_memories": formatted_memories,
                    "memory_count": len(memories),
                    "search_mode": search_mode,
                    "enabled": True
                }
            else:
                return {
                    "retrieved_memories": "暂无相关记忆",
                    "memory_count": 0,
                    "search_mode": search_mode,
                    "enabled": True,
                    "error": memory_result.get("error", "记忆检索失败")
                }
                
        except Exception as e:
            self.logger.error(f"Failed to build memory context: {e}")
            return {
                "retrieved_memories": f"记忆检索失败: {str(e)}",
                "memory_count": 0,
                "search_mode": search_mode,
                "enabled": False,
                "error": str(e)
            }
    
    async def _build_tool_context(
        self, 
        user_input: str, 
        conversation_history: List[Dict], 
        selected_tools: List[str] = None
    ) -> Dict[str, Any]:
        """构建工具上下文 - 适配新版ToolCell"""
        try:
            # 新版ToolCell不再在context_builder中直接执行工具
            # 而是让LLMCell通过Function Calling机制调用
            # 这里只获取可用工具信息作为上下文
            
            # 直接使用ToolCell的异步方法，避免同步包装导致的事件循环冲突
            await self.tool_cell._ensure_mcp_servers_initialized()
            tools_schema = await self.tool_cell.registry.get_tools_schema()
            
            # 构建结果
            tool_result = {
                "success": True,
                "tools_schema": tools_schema,
                "tools_count": len(tools_schema)
            }
            
            if tool_result.get("success", True):
                tools_schema = tool_result.get("tools_schema", [])
                available_tools = [tool.get("function", {}).get("name", "unknown") for tool in tools_schema]
                
                return {
                    "available_tools": available_tools,
                    "tools_count": len(available_tools),
                    "tool_context": f"可用工具: {', '.join(available_tools)}" if available_tools else "暂无可用工具",
                    "tools_schema": tools_schema,
                    "enabled": True
                }
            else:
                return {
                    "available_tools": [],
                    "tools_count": 0,
                    "tool_context": f"工具获取失败: {tool_result.get('error', '未知错误')}",
                    "tools_schema": [],
                    "enabled": False,
                    "error": tool_result.get('error', '未知错误')
                }
            
        except Exception as e:
            self.logger.error(f"Failed to build tool context: {e}")
            return {
                "available_tools": [],
                "tools_count": 0,
                "tool_context": f"工具上下文构建失败: {str(e)}",
                "tools_schema": [],
                "enabled": False,
                "error": str(e)
            }
    
    def _build_conversation_context(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """构建对话上下文"""
        if not conversation_history:
            return {
                "messages": [],
                "message_count": 0,
                "context_summary": "暂无对话历史"
            }
        
        # 格式化对话历史
        formatted_messages = []
        for msg in conversation_history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                formatted_messages.append(msg)
        
        # 生成对话摘要
        context_summary = self._generate_conversation_summary(formatted_messages)
        
        return {
            "messages": formatted_messages,
            "message_count": len(formatted_messages),
            "context_summary": context_summary
        }
    
    async def _combine_contexts(
        self, 
        context_components: Dict[str, Any], 
        user_input: str,
        enable_compression: bool
    ) -> Dict[str, Any]:
        """组合所有上下文组件"""
        # 构建完整上下文
        full_context = {
            "user_input": user_input,
            "components": context_components,
            "metadata": {
                "timestamp": self._get_timestamp(),
                "enabled_components": list(context_components.keys()),
                "compression_enabled": enable_compression
            }
        }
        
        # 计算上下文长度
        context_text = self._format_context_for_llm(full_context)
        token_count = self._estimate_token_count(context_text)
        
        full_context["metadata"]["token_count"] = token_count
        full_context["metadata"]["max_tokens"] = self.max_tokens
        
        # 检查是否需要压缩
        if enable_compression and token_count > self.max_tokens * self.compression_threshold:
            self.logger.info(f"Context too long ({token_count} tokens), applying compression")
            compressed_context = await self._compress_context(full_context)
            compressed_context["metadata"]["compressed"] = True
            compressed_context["metadata"]["original_token_count"] = token_count
            return compressed_context
        
        full_context["metadata"]["compressed"] = False
        return full_context
    
    async def _compress_context(self, full_context: Dict[str, Any]) -> Dict[str, Any]:
        """智能压缩上下文"""
        try:
            # 使用AI总结器压缩上下文
            compressed_result = await self.summarizer.compress_context(
                full_context, self.max_tokens
            )
            
            return compressed_result
            
        except Exception as e:
            self.logger.error(f"Context compression failed: {e}")
            # 如果压缩失败，使用简单截断
            return self._simple_truncate_context(full_context)
    
    def _simple_truncate_context(self, full_context: Dict[str, Any]) -> Dict[str, Any]:
        """简单截断上下文"""
        # 保留最重要的组件
        essential_components = {}
        
        # 优先级：对话历史 > 思考过程 > 记忆 > 工具 > 其他
        priority_order = ["conversation", "thinking", "memory", "tools", "additional"]
        
        current_tokens = 0
        for component_name in priority_order:
            if component_name in full_context["components"]:
                component = full_context["components"][component_name]
                component_text = str(component)
                component_tokens = self._estimate_token_count(component_text)
                
                if current_tokens + component_tokens <= self.max_tokens * 0.9:
                    essential_components[component_name] = component
                    current_tokens += component_tokens
                else:
                    # 截断这个组件
                    truncated_component = self._truncate_component(component, 
                        self.max_tokens * 0.9 - current_tokens)
                    essential_components[component_name] = truncated_component
                    break
        
        full_context["components"] = essential_components
        full_context["metadata"]["truncated"] = True
        
        return full_context
    
    def _format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """将上下文格式化为LLM可读的文本"""
        parts = []
        
        # 添加用户输入
        parts.append(f"=== 用户输入 ===\n{context['user_input']}")
        
        components = context.get("components", {})
        
        # 添加思考过程
        if "thinking" in components and components["thinking"].get("enabled"):
            thinking = components["thinking"]
            parts.append(f"\n=== 思考过程 ===")
            parts.append(f"模式: {thinking.get('mode', 'unknown')}")
            parts.append(f"过程: {thinking.get('thinking_process', '')}")
            if thinking.get("reasoning_steps"):
                parts.append(f"推理步骤: {', '.join(thinking['reasoning_steps'])}")
            parts.append(f"结论: {thinking.get('conclusion', '')}")
        
        # 添加记忆上下文
        if "memory" in components and components["memory"].get("enabled"):
            memory = components["memory"]
            parts.append(f"\n=== 相关记忆 ===")
            parts.append(f"检索到 {memory.get('memory_count', 0)} 条相关记忆:")
            parts.append(memory.get("retrieved_memories", "暂无记忆"))
        
        # 添加工具上下文
        if "tools" in components and components["tools"].get("enabled"):
            tools = components["tools"]
            parts.append(f"\n=== 可用工具 ===")
            parts.append(f"工具数量: {tools.get('tools_count', 0)}")
            if tools.get("tool_context"):
                parts.append(tools["tool_context"])
        
        # 添加对话历史
        if "conversation" in components:
            conversation = components["conversation"]
            parts.append(f"\n=== 对话历史 ===")
            parts.append(f"历史消息数: {conversation.get('message_count', 0)}")
            
            # 显示完整历史，数量可配置
            messages = conversation.get("messages", [])
            if messages:
                display_count = min(len(messages), self.conversation_history_limit)
                parts.append(f"最近{display_count}条对话:")
                for msg in messages[-display_count:]:
                    role = "用户" if msg.get("role") == "user" else "助手"
                    content = msg.get("content", "")
                    # 按配置截断过长的消息
                    if len(content) > self.message_max_length:
                        content = content[:self.message_max_length] + "..."
                    parts.append(f"{role}: {content}")
            else:
                parts.append(conversation.get("context_summary", ""))
        
        # 添加其他上下文
        if "additional" in components:
            additional = components["additional"]
            parts.append(f"\n=== 其他上下文 ===")
            parts.append(str(additional))
        
        return "\n".join(parts)
    
    def _format_conversation_for_thinking(self, conversation_history: List[Dict]) -> str:
        """为思考过程格式化对话历史"""
        if not conversation_history:
            return ""
        
        recent_messages = conversation_history[-3:]  # 最近3条消息
        formatted = []
        
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _format_conversation_for_tools(self, conversation_history: List[Dict]) -> str:
        """为工具调用格式化对话历史"""
        if not conversation_history:
            return ""
        
        # 提取可能与工具相关的信息
        tool_relevant = []
        for msg in conversation_history[-5:]:  # 最近5条消息
            content = msg.get("content", "").lower()
            if any(keyword in content for keyword in ["计算", "搜索", "文件", "工具"]):
                tool_relevant.append(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}")
        
        return "\n".join(tool_relevant) if tool_relevant else "无工具相关历史"
    
    def _format_memories_for_context(self, memories: List[Dict]) -> str:
        """格式化记忆为上下文文本"""
        if not memories:
            return "暂无相关记忆"
        
        formatted = []
        for i, memory in enumerate(memories[:5], 1):  # 最多5条记忆
            content = memory.get("content", "")
            importance = memory.get("importance", 0.0)
            formatted.append(f"{i}. {content} (重要性: {importance:.2f})")
        
        return "\n".join(formatted)
    
    def _generate_conversation_summary(self, messages: List[Dict]) -> str:
        """生成对话摘要"""
        if not messages:
            return "暂无对话历史"
        
        if len(messages) <= 3:
            return f"包含 {len(messages)} 条消息的简短对话"
        
        # 简单的摘要逻辑
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        
        summary = f"对话包含 {len(user_messages)} 条用户消息和 {len(assistant_messages)} 条助手回复"
        
        # 添加最近的话题
        if messages:
            last_user_msg = next((msg for msg in reversed(messages) if msg.get("role") == "user"), None)
            if last_user_msg:
                content = last_user_msg.get("content", "")[:50]
                summary += f"，最近讨论: {content}..."
        
        return summary
    
    def _truncate_component(self, component: Any, max_tokens: int) -> Any:
        """截断单个组件"""
        if isinstance(component, dict):
            # 对字典类型的组件进行智能截断
            truncated = {}
            current_tokens = 0
            
            for key, value in component.items():
                value_str = str(value)
                value_tokens = self._estimate_token_count(value_str)
                
                if current_tokens + value_tokens <= max_tokens:
                    truncated[key] = value
                    current_tokens += value_tokens
                else:
                    # 截断这个值
                    remaining_tokens = max_tokens - current_tokens
                    if remaining_tokens > 10:  # 至少保留10个token
                        truncated_value = value_str[:remaining_tokens * 4]  # 粗略估算
                        truncated[key] = truncated_value + "..."
                    break
            
            return truncated
        else:
            # 对其他类型直接截断
            component_str = str(component)
            if self._estimate_token_count(component_str) <= max_tokens:
                return component
            else:
                truncated_str = component_str[:max_tokens * 4]  # 粗略估算
                return truncated_str + "..."
    
    def _estimate_token_count(self, text: str) -> int:
        """估算文本的token数量"""
        # 简单的token估算：1个token约等于4个字符
        return len(str(text)) // 4
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_status(self) -> Dict[str, Any]:
        """获取构建器状态"""
        return {
            "max_tokens": self.max_tokens,
            "compression_threshold": self.compression_threshold,
            "summary_model": self.summary_model,
            "components_initialized": {
                "mind_cell": self.mind_cell is not None,
                "memory_cell": self.memory_cell is not None,
                "tool_cell": self.tool_cell is not None
            },
            "cache_size": len(self.context_cache)
        }

    def build_enhanced_system_prompt(
        self, 
        original_system_prompt: str, 
        thinking_guidance: Dict[str, Any] = None,
        mind_rule: str = None
    ) -> str:
        """
        构建增强的系统提示词 - 融合基础角色和深度思考指导
        
        核心逻辑：
        基础角色（专业技能） + 深度思考指导（个性化分析） = 独特的角色个性
        
        Args:
            original_system_prompt: 原始系统提示词（基础角色设定）
            thinking_guidance: MindCell的完整思考指导
            mind_rule: 思维规则（仅用于判断是否应用个性化）
            
        Returns:
            融合后的系统提示词
        """
        if not thinking_guidance:
            return original_system_prompt
        
        enhanced_prompt_parts = [original_system_prompt]
        
        # 核心改进：使用MindCell的完整思考过程作为指导
        thinking_process = thinking_guidance.get("thinking_process", "")
        
        if thinking_process and len(thinking_process.strip()) > 100:
            # 使用完整的深度思考结果作为指导
            enhanced_prompt_parts.extend([
                "",
                "=== 深度思考指导 ===",
                "基于以下深度思考来组织你的回复：",
                "",
                thinking_process,
                "",
                "请基于上述深度思考指导来组织你的回复，确保：",
                "1. 体现出深度思考的过程和逻辑",
                "2. 遵循思考中体现的分析角度和风格", 
                "3. 保持思考过程中展现的个性特征",
                "4. 将思考结论融入到你的专业分析中",
                "5. 保持专业水准和准确性"
            ])
        else:
            # 如果思考过程不够详细，使用基础的思考指导
            conclusion = thinking_guidance.get("conclusion", "")
            reasoning_steps = thinking_guidance.get("reasoning_steps", [])
            
            enhanced_prompt_parts.extend([
                "",
                "=== 思考指导 ===",
                "基于深度思考来组织你的回复：",
                ""
            ])
            
            if conclusion:
                enhanced_prompt_parts.append(f"思考结论：{conclusion}")
            
            if reasoning_steps:
                enhanced_prompt_parts.append(f"推理路径：{' → '.join(reasoning_steps)}")
            
            enhanced_prompt_parts.extend([
                "",
                "请基于上述思考指导来组织你的回复。"
            ])
        
        return "\n".join(enhanced_prompt_parts)

    def extract_thinking_guidance(self, full_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        从完整上下文中提取思考指导
        
        Args:
            full_context: 完整的上下文信息
            
        Returns:
            思考指导信息
        """
        components = full_context.get("components", {})
        thinking_component = components.get("thinking", {})
        
        if not thinking_component.get("enabled", False):
            return {}
        
        return {
            "thinking_process": thinking_component.get("thinking_process", ""),
            "reasoning_steps": thinking_component.get("reasoning_steps", []),
            "conclusion": thinking_component.get("conclusion", ""),
            "confidence": thinking_component.get("confidence", 0.0),
            "mode": thinking_component.get("mode", "unknown")
        }


class ContextSummarizer:
    """上下文总结器 - 使用AI进行智能压缩"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
    
    async def compress_context(self, context: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """使用AI压缩上下文"""
        try:
            # 构建压缩提示
            compression_prompt = self._build_compression_prompt(context, max_tokens)
            
            # 调用LLM进行压缩（这里需要实际的LLM调用）
            compressed_result = await self._call_llm_for_compression(compression_prompt)
            
            # 构建压缩后的上下文
            compressed_context = {
                "user_input": context["user_input"],
                "components": {
                    "compressed_summary": {
                        "summary": compressed_result,
                        "compression_method": "ai_summary",
                        "original_components": list(context["components"].keys())
                    }
                },
                "metadata": context["metadata"].copy()
            }
            
            compressed_context["metadata"]["compressed"] = True
            compressed_context["metadata"]["compression_method"] = "ai_summary"
            
            return compressed_context
            
        except Exception as e:
            self.logger.error(f"AI compression failed: {e}")
            # 回退到简单压缩
            return self._simple_compression(context, max_tokens)
    
    def _build_compression_prompt(self, context: Dict[str, Any], max_tokens: int) -> str:
        """构建压缩提示词"""
        context_text = str(context["components"])
        
        prompt = f"""
请将以下上下文信息压缩为不超过{max_tokens // 4}个字符的摘要，保留最重要的信息：

原始上下文：
{context_text}

压缩要求：
1. 保留核心信息和关键细节
2. 保持逻辑连贯性
3. 突出重要的思考过程、记忆和工具结果
4. 使用简洁明了的语言

压缩后的摘要：
"""
        return prompt
    
    async def _call_llm_for_compression(self, prompt: str) -> str:
        """调用LLM进行压缩（模拟实现）"""
        # 这里应该调用实际的LLM API
        # 目前返回模拟结果
        return f"AI压缩摘要：{prompt[:200]}..."
    
    def _simple_compression(self, context: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """简单压缩方法"""
        # 提取关键信息
        key_info = []
        
        components = context.get("components", {})
        
        if "thinking" in components:
            thinking = components["thinking"]
            key_info.append(f"思考结论: {thinking.get('conclusion', '')}")
        
        if "memory" in components:
            memory = components["memory"]
            key_info.append(f"相关记忆: {memory.get('memory_count', 0)}条")
        
        if "tools" in components:
            tools = components["tools"]
            available = tools.get("available_tools", [])
            if available:
                key_info.append(f"可用工具: {', '.join(available[:3])}{'...' if len(available) > 3 else ''}")
        
        if "conversation" in components:
            conversation = components["conversation"]
            key_info.append(f"对话历史: {conversation.get('message_count', 0)}条消息")
        
        summary = "; ".join(key_info)
        
        return {
            "user_input": context["user_input"],
            "components": {
                "simple_summary": {
                    "summary": summary,
                    "compression_method": "simple",
                    "original_components": list(components.keys())
                }
            },
            "metadata": context["metadata"]
        } 