"""
ContextBuilder - 上下文构建器

为智能体提供统一的上下文管理，包括内存、工具和用户信息
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from futurembryo.cells.tool_cell import ToolCell
from futurembryo.cells.state_memory_cell import StateMemoryCell


class ContextBuilder:
    """上下文构建器 - 管理智能体的上下文信息"""
    
    def __init__(self, user_id: str, enable_memory: bool = True, 
                 memory_collection: str = None, tool_cell: Optional[ToolCell] = None):
        """
        初始化上下文构建器
        
        Args:
            user_id: 用户标识
            enable_memory: 是否启用记忆功能
            memory_collection: 记忆集合名称
            tool_cell: 工具Cell实例
        """
        self.user_id = user_id
        self.enable_memory = enable_memory
        self.logger = logging.getLogger(__name__)
        
        # 工具Cell
        self.tool_cell = tool_cell or self._create_default_tool_cell()
        
        # 记忆Cell
        self.memory_cell = None
        if enable_memory:
            self.memory_cell = self._create_memory_cell(memory_collection)
        
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
            # 返回基础配置的ToolCell
            return ToolCell({"auto_load_defaults": True})
    
    def _create_memory_cell(self, collection_name: Optional[str] = None) -> Optional[StateMemoryCell]:
        """创建记忆Cell"""
        try:
            if not collection_name:
                collection_name = f"user_{self.user_id}_memory"
            
            config = {
                "collection_name": collection_name,
                "embedding_model": "text-embedding-ada-002",
                "max_memory_items": 1000,
                "similarity_threshold": 0.7
            }
            
            memory_cell = StateMemoryCell(config)
            self.logger.info(f"💾 Memory cell created: {collection_name}")
            return memory_cell
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to create memory cell: {e}")
            return None
    
    async def build_context(self, user_input: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        构建完整的上下文信息
        
        Args:
            user_input: 用户输入
            additional_context: 额外上下文信息
            
        Returns:
            Dict: 完整的上下文信息
        """
        context = {
            "user_id": self.user_id,
            "user_input": user_input,
            "timestamp": self._get_timestamp()
        }
        
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
                available_tools = await self.tool_cell.get_available_tools()
                context["available_tools"] = len(available_tools)
                context["tool_names"] = [tool.get("function", {}).get("name", "unknown") for tool in available_tools]
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to get tool info: {e}")
                context["available_tools"] = 0
                context["tool_names"] = []
        
        # 合并额外上下文
        if additional_context:
            context.update(additional_context)
        
        return context
    
    async def _get_relevant_memories(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """获取相关记忆"""
        try:
            if not self.memory_cell:
                return []
            
            # 使用记忆Cell搜索相关内容
            memories = self.memory_cell.search(
                query=query,
                limit=max_results
            )
            
            return memories
            
        except Exception as e:
            self.logger.error(f"❌ Error retrieving memories: {e}")
            return []
    
    async def save_interaction(self, user_input: str, agent_response: str, 
                              metadata: Optional[Dict[str, Any]] = None):
        """保存交互记录"""
        try:
            if not self.memory_cell:
                self.logger.debug("💾 No memory cell available, interaction not saved")
                return
            
            # StateMemoryCell是只读的外部服务接口，不支持写入
            # 这里可以在未来集成支持写入的记忆适配器
            # 目前只记录日志表示交互发生了
            
            self.logger.debug(f"💾 Interaction logged: user_id={self.user_id}, " +
                            f"input_length={len(user_input)}, response_length={len(agent_response)}")
            
            # 可以在这里添加到本地缓存或其他持久化方案
            # 例如：保存到本地SQLite数据库或文件系统
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save interaction: {e}")
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """获取用户偏好设置"""
        # 这里可以从数据库或配置文件加载用户偏好
        return {
            "language": "zh-CN",
            "response_style": "detailed",
            "enable_tools": True,
            "max_response_length": 2000
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_status(self) -> Dict[str, Any]:
        """获取上下文构建器状态"""
        return {
            "user_id": self.user_id,
            "memory_enabled": self.memory_cell is not None,
            "tools_enabled": self.tool_cell is not None,
            "memory_collection": getattr(self.memory_cell, 'collection_name', None) if self.memory_cell else None
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理记忆Cell连接
            if self.memory_cell and hasattr(self.memory_cell, 'cleanup'):
                await self.memory_cell.cleanup()
            
            # 清理工具Cell连接
            if self.tool_cell and hasattr(self.tool_cell, 'cleanup'):
                await self.tool_cell.cleanup()
            
            self.logger.info("🧹 ContextBuilder cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")


# 便捷函数
def create_context_builder(user_id: str, enable_memory: bool = True, 
                          memory_collection: str = None, 
                          tool_config: Optional[Dict[str, Any]] = None) -> ContextBuilder:
    """创建上下文构建器的便捷函数"""
    tool_cell = None
    if tool_config:
        tool_cell = ToolCell(tool_config)
    
    return ContextBuilder(
        user_id=user_id,
        enable_memory=enable_memory,
        memory_collection=memory_collection,
        tool_cell=tool_cell
    )