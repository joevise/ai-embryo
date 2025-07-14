"""
ContextBuilder - 上下文构建器

简洁高效的上下文管理器，为智能体提供统一的上下文信息
包括：用户上下文、记忆检索、工具信息、对话历史等

基于demo实践优化，简化复杂的AI压缩逻辑，专注于实用性
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..cells.tool_cell import ToolCell
from ..cells.state_memory_cell import StateMemoryCell
from ..cells.mention_processor_cell import MentionProcessorCell
from ..adapters.user_profile_adapter import UserProfileAdapter


class ContextBuilder:
    """上下文构建器 - 管理智能体的上下文信息"""
    
    def __init__(self, user_id: str, enable_memory: bool = True, 
                 memory_collection: str = None, tool_cell: Optional[ToolCell] = None,
                 enable_user_profile: bool = True, enable_mentions: bool = True):
        """
        初始化上下文构建器
        
        Args:
            user_id: 用户标识
            enable_memory: 是否启用记忆功能
            memory_collection: 记忆集合名称
            tool_cell: 工具Cell实例
            enable_user_profile: 是否启用用户画像
            enable_mentions: 是否启用@引用处理
        """
        self.user_id = user_id
        self.enable_memory = enable_memory
        self.enable_user_profile = enable_user_profile
        self.enable_mentions = enable_mentions
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self.tool_cell = tool_cell or self._create_default_tool_cell()
        self.memory_cell = None
        self.user_profile_adapter = None
        self.mention_processor = None
        
        # 初始化组件
        if enable_memory:
            self.memory_cell = self._create_memory_cell(memory_collection)
        
        if enable_user_profile:
            self.user_profile_adapter = self._create_user_profile_adapter()
        
        if enable_mentions:
            self.mention_processor = self._create_mention_processor()
        
        self.logger.info(f"✅ ContextBuilder initialized for user: {user_id}")
    
    def _create_default_tool_cell(self) -> ToolCell:
        """创建默认工具Cell"""
        try:
            config = {
                "auto_load_defaults": True,
                "tools": [
                    {
                        "name": "calculate",
                        "description": "Perform mathematical calculations",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "expression": {"type": "string", "description": "Mathematical expression to calculate"}
                            },
                            "required": ["expression"]
                        }
                    },
                    {
                        "name": "text_analysis",
                        "description": "Analyze text content",
                        "parameters": {
                            "type": "object", 
                            "properties": {
                                "text": {"type": "string", "description": "Text to analyze"},
                                "analysis_type": {"type": "string", "description": "Type of analysis"}
                            },
                            "required": ["text"]
                        }
                    }
                ]
            }
            return ToolCell(config)
        except Exception as e:
            self.logger.error(f"❌ Failed to create default tool cell: {e}")
            return ToolCell({"auto_load_defaults": True})
    
    def _create_memory_cell(self, collection_name: Optional[str] = None) -> Optional[StateMemoryCell]:
        """创建记忆Cell"""
        try:
            if not collection_name:
                collection_name = f"user_{self.user_id}_memory"
            
            config = {
                "adapters": [
                    {
                        "name": "user_profile",
                        "class_path": "futurembryo.adapters.user_profile_adapter.UserProfileAdapter",
                        "config": {
                            "user_id": self.user_id,
                            "auto_learning": True
                        }
                    }
                ],
                "routing_strategy": "priority",
                "result_aggregation": "merge",
                "enable_caching": True
            }
            
            memory_cell = StateMemoryCell(config)
            self.logger.info(f"💾 Memory cell created: {collection_name}")
            return memory_cell
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to create memory cell: {e}")
            return None
    
    def _create_user_profile_adapter(self) -> Optional[UserProfileAdapter]:
        """创建用户画像适配器"""
        try:
            config = {
                "user_id": self.user_id,
                "auto_learning": True,
                "explicit_memory_keywords": ["记住", "记录", "重要", "注意", "保存", "记下来"],
                "memory_retention_days": 365
            }
            return UserProfileAdapter(config)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to create user profile adapter: {e}")
            return None
    
    def _create_mention_processor(self) -> Optional[MentionProcessorCell]:
        """创建@引用处理器"""
        try:
            config = {
                "enable_auto_complete": True,
                "max_deliverables": 50
            }
            return MentionProcessorCell(config)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to create mention processor: {e}")
            return None
    
    async def build_context(self, user_input: str, additional_context: Optional[Dict[str, Any]] = None,
                           conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        构建完整的上下文信息
        
        Args:
            user_input: 用户输入
            additional_context: 额外上下文信息
            conversation_history: 对话历史
            
        Returns:
            Dict: 完整的上下文信息
        """
        context = {
            "user_id": self.user_id,
            "user_input": user_input,
            "timestamp": self._get_timestamp(),
            "conversation_history": conversation_history or []
        }
        
        # 处理@引用
        mentions_info = {}
        if self.mention_processor:
            try:
                mentions_result = await self.mention_processor.process_async({
                    "action": "extract",
                    "text": user_input
                })
                if mentions_result["success"]:
                    mentions_info = mentions_result
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to process mentions: {e}")
        
        context["mentions"] = mentions_info
        
        # 获取用户上下文
        if self.user_profile_adapter:
            try:
                user_context = await self._get_user_context(user_input, conversation_history)
                context["user_context"] = user_context
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to get user context: {e}")
                context["user_context"] = {}
        
        # 添加记忆上下文
        if self.memory_cell:
            try:
                relevant_memories = await self._get_relevant_memories(user_input)
                context["relevant_memories"] = relevant_memories
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to retrieve memories: {e}")
                context["relevant_memories"] = []
        
        # 添加可用工具信息
        if self.tool_cell:
            try:
                tools_info = await self._get_tools_info()
                context["tools"] = tools_info
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to get tool info: {e}")
                context["tools"] = {"available_tools": 0, "tool_names": []}
        
        # 合并额外上下文
        if additional_context:
            context.update(additional_context)
        
        return context
    
    async def _get_user_context(self, user_input: str, conversation_history: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """获取用户上下文信息"""
        user_context = {}
        
        if not self.user_profile_adapter:
            return user_context
        
        try:
            # 智能处理用户输入
            processing_result = await self.user_profile_adapter.process_async({
                "action": "process_user_input",
                "user_input": user_input,
                "conversation_context": {"history": conversation_history}
            })
            
            if processing_result["success"]:
                user_context["processing_summary"] = processing_result["data"]
            
            # 获取用户画像
            profile_result = await self.user_profile_adapter.process_async({
                "action": "get_user_profile"
            })
            
            if profile_result["success"] and profile_result["data"]["results"]:
                profile_data = profile_result["data"]["results"][0]["metadata"]["profile"]
                user_context["profile"] = profile_data
                user_context["profile_summary"] = self.user_profile_adapter.get_user_context_summary()
            
            # 获取用户偏好
            preferences_result = await self.user_profile_adapter.process_async({
                "action": "get_user_preferences"
            })
            
            if preferences_result["success"] and preferences_result["data"]["results"]:
                preferences_data = preferences_result["data"]["results"][0]["metadata"]["preferences"]
                user_context["preferences"] = preferences_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting user context: {e}")
        
        return user_context
    
    async def _get_relevant_memories(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """获取相关记忆"""
        try:
            if not self.memory_cell:
                return []
            
            # 使用记忆Cell搜索相关内容
            search_result = self.memory_cell.process({
                "action": "search",
                "query": query,
                "limit": max_results
            })
            
            if search_result.get("success"):
                return search_result.get("data", {}).get("results", [])
            else:
                self.logger.warning(f"Memory search failed: {search_result.get('error')}")
                return []
            
        except Exception as e:
            self.logger.error(f"❌ Error retrieving memories: {e}")
            return []
    
    async def _get_tools_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        try:
            if not self.tool_cell:
                return {"available_tools": 0, "tool_names": [], "tools_schema": []}
            
            # 获取可用工具
            available_tools = await self.tool_cell.get_available_tools()
            tool_names = [tool.get("function", {}).get("name", "unknown") for tool in available_tools]
            
            return {
                "available_tools": len(available_tools),
                "tool_names": tool_names,
                "tools_schema": available_tools,
                "tool_context": f"可用工具: {', '.join(tool_names)}" if tool_names else "暂无可用工具"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting tools info: {e}")
            return {"available_tools": 0, "tool_names": [], "tools_schema": []}
    
    async def save_interaction(self, user_input: str, agent_response: str, 
                              metadata: Optional[Dict[str, Any]] = None):
        """保存交互记录"""
        try:
            # 保存到用户记忆
            if self.user_profile_adapter:
                # 检测是否需要记录为显式记忆
                if any(keyword in user_input for keyword in ["记住", "记录", "重要", "注意"]):
                    await self.user_profile_adapter.process_async({
                        "action": "add_user_memory",
                        "content": f"用户说: {user_input}",
                        "memory_type": "explicit",
                        "importance": 0.9,
                        "context": metadata or {}
                    })
                
                # 学习用户偏好
                if "很好" in agent_response or "满意" in agent_response:
                    await self.user_profile_adapter.process_async({
                        "action": "learn_preference",
                        "category": "communication",
                        "preference": "helpful_response",
                        "feedback": 0.8
                    })
            
            self.logger.debug(f"💾 Interaction saved: user_id={self.user_id}, " +
                            f"input_length={len(user_input)}, response_length={len(agent_response)}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save interaction: {e}")
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """获取用户偏好设置"""
        # 从用户画像适配器获取偏好，如果不可用则使用默认值
        if self.user_profile_adapter:
            try:
                result = self.user_profile_adapter.process({
                    "action": "get_user_preferences"
                })
                if result.get("success"):
                    return result["data"]["results"][0]["metadata"]["preferences"]
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to get user preferences: {e}")
        
        # 默认偏好
        return {
            "language": "zh-CN",
            "response_style": "detailed",
            "enable_tools": True,
            "max_response_length": 2000,
            "communication_style": "friendly"
        }
    
    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """将上下文格式化为LLM可读的文本"""
        parts = []
        
        # 用户输入
        parts.append(f"=== 用户输入 ===\n{context['user_input']}")
        
        # 用户上下文
        user_context = context.get("user_context", {})
        if user_context:
            parts.append("\n=== 用户上下文 ===")
            
            profile_summary = user_context.get("profile_summary", "")
            if profile_summary:
                parts.append(f"用户画像: {profile_summary}")
            
            processing_summary = user_context.get("processing_summary", {})
            if processing_summary:
                summary = processing_summary.get("processing_summary", {})
                if summary.get("explicit_memories", 0) > 0:
                    parts.append(f"新增记忆: {summary['explicit_memories']}条")
                if summary.get("profile_updates", 0) > 0:
                    parts.append(f"画像更新: {summary['profile_updates']}项")
                if summary.get("preference_learning", 0) > 0:
                    parts.append(f"偏好学习: {summary['preference_learning']}项")
        
        # @引用信息
        mentions = context.get("mentions", {})
        if mentions.get("success") and mentions.get("mentions"):
            parts.append("\n=== @引用信息 ===")
            for mention in mentions["mentions"]:
                parts.append(f"@{mention['id']}: {mention['description']}")
        
        # 相关记忆
        memories = context.get("relevant_memories", [])
        if memories:
            parts.append("\n=== 相关记忆 ===")
            for i, memory in enumerate(memories[:3], 1):  # 最多显示3条
                content = memory.get("content", "")
                score = memory.get("score", 0)
                parts.append(f"{i}. {content} (相关度: {score:.2f})")
        
        # 可用工具
        tools = context.get("tools", {})
        if tools.get("available_tools", 0) > 0:
            parts.append("\n=== 可用工具 ===")
            parts.append(tools.get("tool_context", ""))
        
        # 对话历史
        history = context.get("conversation_history", [])
        if history:
            parts.append("\n=== 最近对话 ===")
            recent_messages = history[-3:]  # 最近3条
            for msg in recent_messages:
                role = "用户" if msg.get("role") == "user" else "助手"
                content = msg.get("content", "")
                if len(content) > 100:
                    content = content[:100] + "..."
                parts.append(f"{role}: {content}")
        
        return "\n".join(parts)
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()
    
    def get_status(self) -> Dict[str, Any]:
        """获取上下文构建器状态"""
        return {
            "user_id": self.user_id,
            "components": {
                "memory_enabled": self.memory_cell is not None,
                "tools_enabled": self.tool_cell is not None,
                "user_profile_enabled": self.user_profile_adapter is not None,
                "mentions_enabled": self.mention_processor is not None
            },
            "memory_collection": getattr(self.memory_cell, 'adapters', {}) if self.memory_cell else None
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理记忆Cell连接
            if self.memory_cell and hasattr(self.memory_cell, 'close'):
                self.memory_cell.close()
            
            # 清理工具Cell连接
            if self.tool_cell and hasattr(self.tool_cell, 'cleanup'):
                await self.tool_cell.cleanup()
            
            # 清理用户画像适配器
            if self.user_profile_adapter and hasattr(self.user_profile_adapter, 'close'):
                self.user_profile_adapter.close()
            
            self.logger.info("🧹 ContextBuilder cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")


# 便捷函数
def create_context_builder(user_id: str, enable_memory: bool = True, 
                          memory_collection: str = None, 
                          tool_config: Optional[Dict[str, Any]] = None,
                          enable_user_profile: bool = True,
                          enable_mentions: bool = True) -> ContextBuilder:
    """创建上下文构建器的便捷函数"""
    tool_cell = None
    if tool_config:
        tool_cell = ToolCell(tool_config)
    
    return ContextBuilder(
        user_id=user_id,
        enable_memory=enable_memory,
        memory_collection=memory_collection,
        tool_cell=tool_cell,
        enable_user_profile=enable_user_profile,
        enable_mentions=enable_mentions
    )


# 向后兼容的别名
IntelligentContextBuilder = ContextBuilder