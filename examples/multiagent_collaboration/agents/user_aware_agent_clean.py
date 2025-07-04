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
from cells.user_memory_cell import UserMemoryCell
from cells.mention_processor_cell import MentionProcessorCell


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
            agent_config: 智能体配置
        """
        # 基础信息
        self.agent_id = agent_id
        self.name = agent_config.get("name", agent_id)
        self.description = agent_config.get("description", "")
        self.role = agent_config.get("role", "assistant")
        self.capabilities = agent_config.get("capabilities", [])
        self.personality = agent_config.get("personality", ["helpful", "professional"])
        
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
        
        # 1. 用户记忆Cell
        user_memory_config = agent_config.get("user_memory_config", {})
        self.user_memory = UserMemoryCell(user_memory_config)
        
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
    
    def process_user_input(self, user_input: str, conversation_history: List[Dict] = None,
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理用户输入的主入口方法
        
        Args:
            user_input: 用户输入文本
            conversation_history: 对话历史
            context: 额外上下文信息
            
        Returns:
            Dict: 处理结果，包含响应、产出物等
        """
        try:
            # 1. 准备基础上下文
            processing_context = {
                "user_input": user_input,
                "conversation_history": conversation_history or [],
                "timestamp": datetime.now(),
                "agent_id": self.agent_id,
                "extra_context": context or {}
            }
            
            # 2. 处理用户输入（学习用户信息）
            user_processing_result = self.user_memory.process({
                "action": "process_user_input",
                "user_input": user_input,
                "conversation_context": processing_context
            })
            
            if user_processing_result["success"]:
                self.logger.info(f"User learning results: {user_processing_result['data']}")
            
            # 3. 解析@引用
            mention_result = self.mention_processor.process({
                "action": "parse_mentions",
                "text": user_input
            })
            
            parsed_mentions = []
            if mention_result["success"]:
                parsed_mentions = mention_result["data"]["mentions"]
                self.logger.info(f"Parsed mentions: {parsed_mentions}")
            
            # 4. 构建用户感知的上下文
            user_aware_context = self._build_user_aware_context(
                user_input, conversation_history, parsed_mentions
            )
            
            # 5. 使用LLM生成响应
            llm_context = {
                "messages": user_aware_context["messages"],
                "enable_tools": True
            }
            
            llm_result = self.llm_cell.process(llm_context)
            
            if not llm_result["success"]:
                return {
                    "success": False,
                    "error": f"LLM processing failed: {llm_result.get('error')}",
                    "agent_id": self.agent_id
                }
            
            # 6. 处理响应和生成产出物
            response_data = llm_result["data"]
            final_result = self._post_process_response(
                response_data, user_input, processing_context
            )
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            return {
                "success": False,
                "error": f"Agent processing failed: {str(e)}",
                "agent_id": self.agent_id
            }
    
    def _build_user_aware_context(self, user_input: str, conversation_history: List[Dict],
                                 parsed_mentions: List[str]) -> Dict[str, Any]:
        """构建用户感知的上下文"""
        
        # 1. 获取用户上下文
        user_context = self.user_memory.get_user_context_for_agents()
        
        # 2. 处理@引用内容
        mention_contents = {}
        for mention in parsed_mentions:
            mention_result = self.mention_processor.process({
                "action": "handle_mention",
                "mention_id": mention,
                "mention_context": {"user_input": user_input}
            })
            
            if mention_result["success"]:
                mention_contents[mention] = mention_result["data"]
        
        # 3. 构建增强的系统提示词
        enhanced_system_prompt = self._build_context_aware_system_prompt(
            user_context, mention_contents
        )
        
        # 4. 构建消息列表
        messages = [
            {"role": "system", "content": enhanced_system_prompt}
        ]
        
        # 添加对话历史（最近几轮）
        if conversation_history:
            recent_history = conversation_history[-6:]  # 最近3轮对话
            messages.extend(recent_history)
        
        # 添加当前用户输入
        messages.append({
            "role": "user",
            "content": self._format_user_input_with_context(user_input, mention_contents)
        })
        
        return {
            "messages": messages,
            "user_context": user_context,
            "mention_contents": mention_contents
        }
    
    def _build_context_aware_system_prompt(self, user_context: Dict[str, Any],
                                          mention_contents: Dict[str, Any]) -> str:
        """构建上下文感知的系统提示词"""
        
        base_prompt = self.llm_cell.system_prompt
        
        # 用户上下文信息
        user_info_parts = []
        
        # 用户画像
        profile = user_context.get("user_profile", {})
        if profile.get("interests"):
            interests = ", ".join(profile["interests"])
            user_info_parts.append(f"用户兴趣：{interests}")
        
        if profile.get("expertise_areas"):
            expertise = ", ".join(profile["expertise_areas"])
            user_info_parts.append(f"用户专业领域：{expertise}")
        
        if profile.get("communication_style"):
            user_info_parts.append(f"用户偏好的沟通风格：{profile['communication_style']}")
        
        # 用户偏好
        preferences = user_context.get("user_preferences", {})
        if preferences.get("communication_prefs"):
            comm_prefs = preferences["communication_prefs"]
            high_pref = max(comm_prefs.items(), key=lambda x: x[1], default=None)
            if high_pref and high_pref[1] > 0.6:
                user_info_parts.append(f"用户偏好：{high_pref[0]}")
        
        # 最近记忆
        recent_memories = user_context.get("recent_memories", [])
        if recent_memories:
            important_memories = [m["content"] for m in recent_memories[:2] if m.get("importance", 0) > 0.7]
            if important_memories:
                user_info_parts.append(f"重要记忆：{'; '.join(important_memories)}")
        
        # @引用内容
        mention_info_parts = []
        for mention, content in mention_contents.items():
            if content.get("mention_type") == "user":
                mention_info_parts.append(f"@{mention}已加载到上下文中")
        
        # 组合增强提示词
        enhanced_parts = [base_prompt]
        
        if user_info_parts:
            enhanced_parts.append("\n当前用户信息：")
            enhanced_parts.extend([f"- {info}" for info in user_info_parts])
        
        if mention_info_parts:
            enhanced_parts.append("\n当前上下文：")
            enhanced_parts.extend([f"- {info}" for info in mention_info_parts])
        
        enhanced_parts.append("\n请根据用户信息个性化你的回复。")
        
        return "\n".join(enhanced_parts)
    
    def _format_user_input_with_context(self, user_input: str, 
                                       mention_contents: Dict[str, Any]) -> str:
        """格式化用户输入，包含@引用上下文"""
        if not mention_contents:
            return user_input
        
        formatted_parts = [user_input]
        
        # 添加@引用的具体内容
        for mention, content in mention_contents.items():
            if content.get("mention_type") == "user":
                # 用户相关@引用
                if "handler_result" in content:
                    handler_result = content["handler_result"]
                    if handler_result.get("success"):
                        data = handler_result.get("data", {})
                        if mention == "user-profile":
                            profile = data.get("profile", {})
                            if profile:
                                formatted_parts.append(f"\n[用户画像：{json.dumps(profile, ensure_ascii=False)}]")
                        elif mention == "user-memory":
                            memories = data.get("memories", [])
                            if memories:
                                memory_texts = [m["content"] for m in memories[:3]]
                                formatted_parts.append(f"\n[用户记忆：{'; '.join(memory_texts)}]")
                        elif mention == "user-preferences":
                            prefs = data.get("preferences", {})
                            if prefs:
                                formatted_parts.append(f"\n[用户偏好：{json.dumps(prefs, ensure_ascii=False)}]")
        
        return "\n".join(formatted_parts)
    
    def _post_process_response(self, response_data: Dict[str, Any], 
                              user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """后处理响应，生成产出物等"""
        
        response_text = response_data.get("response", "")
        
        # 1. 学习用户反馈（如果有明确的满意度信号）
        self._learn_from_response_context(user_input, response_text, context)
        
        # 2. 检查是否需要生成产出物
        deliverables = self._check_and_generate_deliverables(response_text, context)
        
        # 3. 构建最终结果
        final_result = {
            "success": True,
            "data": {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "response": response_text,
                "usage": response_data.get("usage", {}),
                "model": response_data.get("model", ""),
                "deliverables": deliverables,
                "user_learning": {
                    "profile_updated": context.get("profile_updated", False),
                    "preferences_learned": context.get("preferences_learned", False)
                }
            }
        }
        
        return final_result
    
    def _learn_from_response_context(self, user_input: str, response: str, 
                                   context: Dict[str, Any]):
        """从响应上下文中学习"""
        try:
            # 检测用户满意度信号
            satisfaction_signals = {
                "positive": ["很好", "不错", "满意", "正是我要的", "完美", "谢谢"],
                "negative": ["不对", "错了", "不是这样", "太复杂", "太简单", "不够详细"]
            }
            
            # 这里简化处理，实际可以用更复杂的NLP分析
            user_input_lower = user_input.lower()
            
            for sentiment, signals in satisfaction_signals.items():
                for signal in signals:
                    if signal in user_input_lower:
                        feedback_score = 0.8 if sentiment == "positive" else 0.2
                        
                        # 学习沟通风格偏好
                        self.user_memory.process({
                            "action": "learn_preference",
                            "category": "communication",
                            "preference": "current_style",  # 实际应该是具体的风格
                            "feedback": feedback_score
                        })
                        break
                        
        except Exception as e:
            self.logger.warning(f"Failed to learn from response context: {e}")
    
    def _check_and_generate_deliverables(self, response: str, 
                                        context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查并生成产出物"""
        deliverables = []
        
        try:
            # 检查响应是否包含重要的结构化内容
            # 这里可以根据具体需求实现更复杂的检测逻辑
            
            # 简单示例：如果响应很长且包含分析内容，生成报告产出物
            if len(response) > 500 and any(keyword in response for keyword in ["分析", "报告", "总结", "建议"]):
                deliverable_id = f"{self.agent_id}_report_{int(datetime.now().timestamp())}"
                deliverable_name = f"{self.name}生成的{self.role}报告"
                
                # 注册为@引用对象
                self.mention_processor.register_deliverable_mention(
                    deliverable_id=deliverable_id,
                    deliverable_name=deliverable_name,
                    content_type="text/markdown"
                )
                
                deliverables.append({
                    "id": deliverable_id,
                    "name": deliverable_name,
                    "type": "report",
                    "content": response,
                    "generated_by": self.agent_id,
                    "generated_at": datetime.now().isoformat(),
                    "mention": f"@{deliverable_id}"
                })
        
        except Exception as e:
            self.logger.warning(f"Failed to generate deliverables: {e}")
        
        return deliverables
    
    # 便捷方法
    def chat(self, message: str, conversation_history: List[Dict] = None) -> str:
        """便捷的对话方法"""
        result = self.process_user_input(message, conversation_history)
        
        if result["success"]:
            return result["data"]["response"]
        else:
            return f"抱歉，处理出现问题：{result.get('error', '未知错误')}"
    
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