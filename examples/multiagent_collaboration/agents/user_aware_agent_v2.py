"""
UserAwareAgent v2 - 用户感知智能体

基于FuturEmbryo框架的智能体实现，支持工具调用和记忆管理
使用组合模式而非继承，避免Pipeline冲突
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from futurembryo.cells.llm_cell import LLMCell
from futurembryo.cells.tool_cell import ToolCell
from futurembryo.core.cell import Cell
from core.context_builder import ContextBuilder


class UserAwareAgent:
    """用户感知智能体 - 支持工具调用和上下文管理"""
    
    def __init__(self, agent_id: str, agent_config: Dict[str, Any], 
                 context_builder: Optional[ContextBuilder] = None):
        """
        初始化智能体
        
        Args:
            agent_id: 智能体标识
            agent_config: 智能体配置
            context_builder: 上下文构建器（可选）
        """
        self.agent_id = agent_id.lstrip('@')  # 移除@符号
        self.config = agent_config
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
        # 基础属性
        self.name = agent_config.get("name", agent_id)
        self.role = agent_config.get("role", "assistant")
        self.system_prompt = agent_config.get("system_prompt", f"You are {self.name}, a helpful AI assistant.")
        self.capabilities = agent_config.get("capabilities", [])
        
        # 上下文构建器
        self.context_builder = context_builder or ContextBuilder(
            user_id="default",
            enable_memory=True
        )
        
        # LLM配置
        llm_config = agent_config.get("llm_config", {})
        final_llm_config = {
            "model": "anthropic/claude-sonnet-4-20250514",
            "temperature": 0.7,
            "max_tokens": 2000,
            "enable_tools": True,
            "tool_choice": "auto",
            "max_tool_calls": 3,
            **llm_config
        }
        
        # 创建LLM Cell
        self.llm_cell = LLMCell(
            model_name=final_llm_config.get("model", "anthropic/claude-sonnet-4-20250514"),
            config=final_llm_config,
            tool_cell=self.context_builder.tool_cell
        )
        
        self.logger.info(f"✅ UserAwareAgent '{self.name}' initialized")
        self.logger.info(f"   - Role: {self.role}")
        self.logger.info(f"   - Capabilities: {self.capabilities}")
        self.logger.info(f"   - Model: {final_llm_config.get('model')}")
    
    async def process_message(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        处理用户消息
        
        Args:
            user_input: 用户输入
            context: 额外上下文信息
            
        Returns:
            str: 智能体响应
        """
        try:
            self.logger.info(f"📥 {self.name} processing message")
            
            # 构建系统提示词
            system_prompt = self._build_system_prompt(context)
            
            # 构建消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # 处理LLM请求
            llm_context = {
                "messages": messages,
                "enable_tools": True
            }
            
            result = self.llm_cell(llm_context)
            
            if result["success"]:
                response = result["data"]["response"]
                
                # 记录对话（如果有内存）
                await self._save_conversation(user_input, response)
                
                self.logger.info(f"✅ {self.name} response generated")
                return response
            else:
                error_msg = f"LLM处理失败: {result['error']}"
                self.logger.error(f"❌ {error_msg}")
                return f"抱歉，处理您的请求时出现错误: {result['error']}"
                
        except Exception as e:
            error_msg = f"处理消息时出现错误: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return f"抱歉，{error_msg}"
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """构建系统提示词"""
        prompt_parts = [self.system_prompt]
        
        # 添加角色信息
        if self.role:
            prompt_parts.append(f"\n你的角色: {self.role}")
        
        # 添加能力信息
        if self.capabilities:
            prompt_parts.append(f"\n你的核心能力: {', '.join(self.capabilities)}")
        
        # 添加上下文信息
        if context:
            if context.get("additional_instructions"):
                prompt_parts.append(f"\n额外指令: {context['additional_instructions']}")
        
        # 添加工具使用指南
        prompt_parts.append("""
\n## 工具使用指南
- 当需要执行具体操作时，主动使用可用的工具
- 工具调用要准确，参数要完整
- 始终向用户展示工具执行的结果
- 如果工具执行失败，向用户说明并提供替代方案

## 响应要求
- 提供详细、准确的回答
- 保持友好和专业的语调
- 当不确定时，诚实地说明并寻求澄清
- 完成任务后，总结执行的步骤和结果""")
        
        return "".join(prompt_parts)
    
    async def _save_conversation(self, user_input: str, agent_response: str):
        """保存对话到记忆中"""
        try:
            if hasattr(self.context_builder, 'memory_cell') and self.context_builder.memory_cell:
                # 检查是否有save_interaction方法（推荐方式）
                if hasattr(self.context_builder, 'save_interaction'):
                    await self.context_builder.save_interaction(
                        user_input, 
                        agent_response, 
                        {
                            "agent_id": self.agent_id,
                            "agent_name": self.name
                        }
                    )
                    self.logger.debug(f"💾 Conversation saved via context builder")
                else:
                    # 如果没有save_interaction方法，记录但不失败
                    self.logger.debug(f"💾 Memory saving not available, conversation not persisted")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to save conversation: {e}")
    
    async def get_memory_context(self, query: str, max_items: int = 5) -> List[Dict[str, Any]]:
        """获取相关的记忆上下文"""
        try:
            if hasattr(self.context_builder, 'memory_cell') and self.context_builder.memory_cell:
                memories = self.context_builder.memory_cell.search(
                    query=query,
                    limit=max_items
                )
                return memories
            return []
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to retrieve memory context: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "llm_model": self.llm_cell.model_name,
            "has_tools": self.llm_cell.tool_cell is not None,
            "memory_enabled": hasattr(self.context_builder, 'memory_cell') and self.context_builder.memory_cell is not None
        }
    
    def get_capabilities(self) -> List[str]:
        """获取智能体能力列表"""
        return self.capabilities.copy()
    
    def add_capability(self, capability: str):
        """添加能力"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.logger.info(f"➕ Added capability: {capability}")
    
    def remove_capability(self, capability: str):
        """移除能力"""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
            self.logger.info(f"➖ Removed capability: {capability}")
    
    def update_system_prompt(self, new_prompt: str):
        """更新系统提示词"""
        self.system_prompt = new_prompt
        self.logger.info("📝 System prompt updated")
    
    async def reset_memory(self):
        """重置记忆"""
        try:
            if hasattr(self.context_builder, 'memory_cell') and self.context_builder.memory_cell:
                # 这里可以实现记忆清理逻辑
                self.logger.info("🧹 Memory reset requested")
        except Exception as e:
            self.logger.error(f"❌ Failed to reset memory: {e}")
    
    def __str__(self) -> str:
        return f"UserAwareAgent(id={self.agent_id}, name={self.name}, role={self.role})"
    
    def __repr__(self) -> str:
        return self.__str__()