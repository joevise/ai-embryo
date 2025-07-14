"""
UserAwareAgent - 用户感知的智能体

基于FuturEmbryo的Pipeline框架，实现具有用户上下文感知能力的智能体
支持@引用处理、用户记忆集成、个性化响应等功能
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from futurembryo.core.pipeline import Pipeline
from futurembryo.cells.llm_cell import LLMCell
from futurembryo.cells.tool_cell import ToolCell
from futurembryo.core.context_builder import IntelligentContextBuilder

# 导入我们的扩展Cell
sys.path.insert(0, str(Path(__file__).parent.parent))
from futurembryo.adapters.user_profile_adapter import UserProfileAdapter
from futurembryo.cells.mention_processor_cell import MentionProcessorCell


class UserAwareAgent(Pipeline):
    """
    用户感知的智能体 - 基于FuturEmbryo Pipeline
    
    核心特性：
    1. 用户上下文感知 - 自动加载用户画像和偏好
    2. @引用处理 - 支持@user-profile、@user-memory等引用
    3. 个性化响应 - 根据用户偏好调整交互风格
    4. 记忆学习 - 自动学习用户反馈和偏好
    5. 产出物生成 - 自动注册可@引用的产出物
    """
    
    def __init__(self, agent_id: str, agent_config: Dict[str, Any]):
        """
        初始化用户感知智能体
        
        Args:
            agent_id: 智能体ID（用作@引用ID）
            agent_config: 智能体配置，包含：
                - name: 显示名称
                - description: 描述
                - role: 角色定义（researcher/analyst/writer等）
                - capabilities: 能力列表
                - personality: 性格特征
                - llm_config: LLM配置
                - user_memory_config: 用户记忆配置
                - mention_processor_config: @引用处理配置
                - context_builder_config: 上下文构建配置
        """
        # 基础信息
        self.agent_id = agent_id
        self.name = agent_config.get("name", agent_id)
        self.description = agent_config.get("description", "")
        self.role = agent_config.get("role", "assistant")
        self.capabilities = agent_config.get("capabilities", [])
        self.personality = agent_config.get("personality", ["helpful", "professional"])
        self.user_id = agent_config.get("user_id", "default")  # 添加user_id属性
        
        # 初始化Pipeline配置
        pipeline_config = {
            "name": f"{self.name}_pipeline",
            "description": f"Pipeline for {self.name} agent"
        }
        
        super().__init__(pipeline_config)
        
        # 初始化核心组件
        self._init_components(agent_config)
        
        # 组装Pipeline
        self._setup_pipeline()
        
        # 注册为@引用对象
        self._register_as_mention()
        
        self.logger.info(f"UserAwareAgent '{self.agent_id}' initialized with role: {self.role}")
    
    def _init_components(self, agent_config: Dict[str, Any]):
        """初始化核心组件"""
        
        # 1. 用户画像适配器
        user_memory_config = agent_config.get("user_memory_config", {})
        user_memory_config["user_id"] = self.user_id  # 确保user_id设置
        self.user_memory = UserProfileAdapter(user_memory_config)
        
        # 2. @引用处理Cell
        mention_config = agent_config.get("mention_processor_config", {})
        self.mention_processor = MentionProcessorCell(mention_config)
        
        # 3. 工具Cell（复用现有）
        tool_config = agent_config.get("tool_config", {})
        self.tool_cell = ToolCell(tool_config)
        
        # 4. LLM Cell（复用现有）
        llm_config = agent_config.get("llm_config", {})
        # 增强系统提示词以包含角色和用户感知
        enhanced_system_prompt = self._build_enhanced_system_prompt(llm_config)
        llm_config["system_prompt"] = enhanced_system_prompt
        
        self.llm_cell = LLMCell(
            model_name=llm_config.get("model", "gpt-4"),
            config=llm_config,
            tool_cell=self.tool_cell
        )
        
        # 5. 上下文构建器（复用并扩展）
        context_config = agent_config.get("context_builder_config", {})
        self.context_builder = IntelligentContextBuilder(
            max_tokens=context_config.get("max_tokens", 4000),
            compression_threshold=context_config.get("compression_threshold", 0.8)
        )
        
        # 向上下文构建器注册我们的组件
        self.context_builder.initialize_components({
            "memory_cell": {
                "embedding_model": "text-embedding-ada-002",
                "collection_name": f"{self.agent_id}_context",
                "db_path": "./memory_db"
            }
        })
    
    def _build_enhanced_system_prompt(self, llm_config: Dict[str, Any]) -> str:
        """构建增强的系统提示词"""
        base_prompt = llm_config.get("system_prompt", "You are a helpful AI assistant.")
        
        # 角色定义
        role_prompts = {
            "researcher": "你是一个专业的研究员，擅长信息收集、分析和报告撰写。",
            "analyst": "你是一个数据分析师，专长于数据解读、趋势分析和洞察发现。",
            "writer": "你是一个专业写作者，擅长内容创作、文档编写和信息整理。",
            "creative": "你是一个创意专家，善于发散思维、创新设计和灵感激发。",
            "planner": "你是一个项目规划师，专长于任务分解、流程设计和计划制定。"
        }
        
        role_prompt = role_prompts.get(self.role, "你是一个智能助手。")
        
        # 性格特征
        personality_desc = "、".join(self.personality)
        
        # 能力描述
        capabilities_desc = "、".join(self.capabilities) if self.capabilities else "通用对话"
        
        enhanced_prompt = f"""{base_prompt}

{role_prompt}

你的核心特质：{personality_desc}
你的主要能力：{capabilities_desc}

特别说明：
1. 你具有用户感知能力，会根据用户的画像、偏好和记忆来个性化响应
2. 你能理解@引用，如@user-profile（用户画像）、@user-memory（用户记忆）等
3. 你会根据用户的沟通风格偏好调整回复方式
4. 你能学习用户的反馈并持续改进服务质量
5. 你生成的重要内容会自动成为可被@引用的产出物

请始终：
- 关注用户的个人偏好和兴趣
- 根据用户画像调整专业程度和详细度
- 记住用户明确要求记录的信息
- 在回复中体现你的专业角色特点"""
        
        return enhanced_prompt
    
    def _setup_pipeline(self):
        """组装Pipeline - 定义处理流程"""
        # 添加组件到Pipeline
        self.add_cell("user_memory", self.user_memory)
        self.add_cell("mention_processor", self.mention_processor)
        self.add_cell("llm", self.llm_cell)
        
        # 定义处理流程（可以根据需要调整）
        self.set_flow([
            "user_memory",      # 1. 处理用户记忆
            "mention_processor", # 2. 处理@引用
            "llm"               # 3. LLM生成响应
        ])
    
    def _register_as_mention(self):
        """将自己注册为@引用对象"""
        self.mention_processor.register_agent_mention(
            agent_id=self.agent_id,
            agent_name=self.name,
            description=self.description,
            handler=self._handle_self_mention
        )
    
    def _handle_self_mention(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理对自己的@引用"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "status": "available",
            "action": "activate_agent"
        }
    
    # 便捷方法
    def chat(self, message: str, conversation_history: List[Dict] = None) -> str:
        """便捷的对话方法"""
        try:
            # 简化版处理，直接使用Pipeline
            context = {
                "user_input": message,
                "conversation_history": conversation_history or []
            }
            result = self.process(context)
            
            if result.get("success"):
                return result["data"].get("response", "处理完成，但没有生成响应")
            else:
                return f"抱歉，处理出现问题：{result.get('error', '未知错误')}"
        except Exception as e:
            return f"抱歉，处理出现问题：{str(e)}"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "capabilities": self.capabilities,
            "personality": self.personality,
            "mention_format": f"@{self.agent_id}",
            "status": "active"
        }
    
    def get_user_context_summary(self) -> Dict[str, Any]:
        """获取当前用户上下文摘要"""
        return self.user_memory.get_user_context_for_agents()
    
    def learn_user_preference(self, category: str, preference: str, feedback: float):
        """便捷的用户偏好学习方法"""
        return self.user_memory.process({
            "action": "learn_preference",
            "category": category,
            "preference": preference,
            "feedback": feedback
        })