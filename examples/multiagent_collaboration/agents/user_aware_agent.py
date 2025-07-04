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
        
        return enhanced_prompt\n    \n    def _setup_pipeline(self):\n        \"\"\"组装Pipeline - 定义处理流程\"\"\"\n        # 添加组件到Pipeline\n        self.add_cell(\"user_memory\", self.user_memory)\n        self.add_cell(\"mention_processor\", self.mention_processor)\n        self.add_cell(\"llm\", self.llm_cell)\n        \n        # 定义处理流程（可以根据需要调整）\n        self.set_flow([\n            \"user_memory\",      # 1. 处理用户记忆\n            \"mention_processor\", # 2. 处理@引用\n            \"llm\"               # 3. LLM生成响应\n        ])\n    \n    def _register_as_mention(self):\n        \"\"\"将自己注册为@引用对象\"\"\"\n        self.mention_processor.register_agent_mention(\n            agent_id=self.agent_id,\n            agent_name=self.name,\n            description=self.description,\n            handler=self._handle_self_mention\n        )\n    \n    def _handle_self_mention(self, context: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"处理对自己的@引用\"\"\"\n        return {\n            \"agent_id\": self.agent_id,\n            \"name\": self.name,\n            \"role\": self.role,\n            \"capabilities\": self.capabilities,\n            \"status\": \"available\",\n            \"action\": \"activate_agent\"\n        }\n    \n    def process_user_input(self, user_input: str, conversation_history: List[Dict] = None,\n                          context: Dict[str, Any] = None) -> Dict[str, Any]:\n        \"\"\"\n        处理用户输入的主入口方法\n        \n        Args:\n            user_input: 用户输入文本\n            conversation_history: 对话历史\n            context: 额外上下文信息\n            \n        Returns:\n            Dict: 处理结果，包含响应、产出物等\n        \"\"\"\n        try:\n            # 1. 准备基础上下文\n            processing_context = {\n                \"user_input\": user_input,\n                \"conversation_history\": conversation_history or [],\n                \"timestamp\": datetime.now(),\n                \"agent_id\": self.agent_id,\n                \"extra_context\": context or {}\n            }\n            \n            # 2. 处理用户输入（学习用户信息）\n            user_processing_result = self.user_memory.process({\n                \"action\": \"process_user_input\",\n                \"user_input\": user_input,\n                \"conversation_context\": processing_context\n            })\n            \n            if user_processing_result[\"success\"]:\n                self.logger.info(f\"User learning results: {user_processing_result['data']}\")\n            \n            # 3. 解析@引用\n            mention_result = self.mention_processor.process({\n                \"action\": \"parse_mentions\",\n                \"text\": user_input\n            })\n            \n            parsed_mentions = []\n            if mention_result[\"success\"]:\n                parsed_mentions = mention_result[\"data\"][\"mentions\"]\n                self.logger.info(f\"Parsed mentions: {parsed_mentions}\")\n            \n            # 4. 构建用户感知的上下文\n            user_aware_context = self._build_user_aware_context(\n                user_input, conversation_history, parsed_mentions\n            )\n            \n            # 5. 使用LLM生成响应\n            llm_context = {\n                \"messages\": user_aware_context[\"messages\"],\n                \"enable_tools\": True\n            }\n            \n            llm_result = self.llm_cell.process(llm_context)\n            \n            if not llm_result[\"success\"]:\n                return {\n                    \"success\": False,\n                    \"error\": f\"LLM processing failed: {llm_result.get('error')}\",\n                    \"agent_id\": self.agent_id\n                }\n            \n            # 6. 处理响应和生成产出物\n            response_data = llm_result[\"data\"]\n            final_result = self._post_process_response(\n                response_data, user_input, processing_context\n            )\n            \n            return final_result\n            \n        except Exception as e:\n            self.logger.error(f\"Error processing user input: {e}\")\n            return {\n                \"success\": False,\n                \"error\": f\"Agent processing failed: {str(e)}\",\n                \"agent_id\": self.agent_id\n            }\n    \n    def _build_user_aware_context(self, user_input: str, conversation_history: List[Dict],\n                                 parsed_mentions: List[str]) -> Dict[str, Any]:\n        \"\"\"构建用户感知的上下文\"\"\"\n        \n        # 1. 获取用户上下文\n        user_context = self.user_memory.get_user_context_for_agents()\n        \n        # 2. 处理@引用内容\n        mention_contents = {}\n        for mention in parsed_mentions:\n            mention_result = self.mention_processor.process({\n                \"action\": \"handle_mention\",\n                \"mention_id\": mention,\n                \"mention_context\": {\"user_input\": user_input}\n            })\n            \n            if mention_result[\"success\"]:\n                mention_contents[mention] = mention_result[\"data\"]\n        \n        # 3. 构建增强的系统提示词\n        enhanced_system_prompt = self._build_context_aware_system_prompt(\n            user_context, mention_contents\n        )\n        \n        # 4. 构建消息列表\n        messages = [\n            {\"role\": \"system\", \"content\": enhanced_system_prompt}\n        ]\n        \n        # 添加对话历史（最近几轮）\n        if conversation_history:\n            recent_history = conversation_history[-6:]  # 最近3轮对话\n            messages.extend(recent_history)\n        \n        # 添加当前用户输入\n        messages.append({\n            \"role\": \"user\",\n            \"content\": self._format_user_input_with_context(user_input, mention_contents)\n        })\n        \n        return {\n            \"messages\": messages,\n            \"user_context\": user_context,\n            \"mention_contents\": mention_contents\n        }\n    \n    def _build_context_aware_system_prompt(self, user_context: Dict[str, Any],\n                                          mention_contents: Dict[str, Any]) -> str:\n        \"\"\"构建上下文感知的系统提示词\"\"\"\n        \n        base_prompt = self.llm_cell.system_prompt\n        \n        # 用户上下文信息\n        user_info_parts = []\n        \n        # 用户画像\n        profile = user_context.get(\"user_profile\", {})\n        if profile.get(\"interests\"):\n            interests = \", \".join(profile[\"interests\"])\n            user_info_parts.append(f\"用户兴趣：{interests}\")\n        \n        if profile.get(\"expertise_areas\"):\n            expertise = \", \".join(profile[\"expertise_areas\"])\n            user_info_parts.append(f\"用户专业领域：{expertise}\")\n        \n        if profile.get(\"communication_style\"):\n            user_info_parts.append(f\"用户偏好的沟通风格：{profile['communication_style']}\")\n        \n        # 用户偏好\n        preferences = user_context.get(\"user_preferences\", {})\n        if preferences.get(\"communication_prefs\"):\n            comm_prefs = preferences[\"communication_prefs\"]\n            high_pref = max(comm_prefs.items(), key=lambda x: x[1], default=None)\n            if high_pref and high_pref[1] > 0.6:\n                user_info_parts.append(f\"用户偏好：{high_pref[0]}\")\n        \n        # 最近记忆\n        recent_memories = user_context.get(\"recent_memories\", [])\n        if recent_memories:\n            important_memories = [m[\"content\"] for m in recent_memories[:2] if m.get(\"importance\", 0) > 0.7]\n            if important_memories:\n                user_info_parts.append(f\"重要记忆：{'; '.join(important_memories)}\")\n        \n        # @引用内容\n        mention_info_parts = []\n        for mention, content in mention_contents.items():\n            if content.get(\"mention_type\") == \"user\":\n                mention_info_parts.append(f\"@{mention}已加载到上下文中\")\n        \n        # 组合增强提示词\n        enhanced_parts = [base_prompt]\n        \n        if user_info_parts:\n            enhanced_parts.append(\"\\n当前用户信息：\")\n            enhanced_parts.extend([f\"- {info}\" for info in user_info_parts])\n        \n        if mention_info_parts:\n            enhanced_parts.append(\"\\n当前上下文：\")\n            enhanced_parts.extend([f\"- {info}\" for info in mention_info_parts])\n        \n        enhanced_parts.append(\"\\n请根据用户信息个性化你的回复。\")\n        \n        return \"\\n\".join(enhanced_parts)\n    \n    def _format_user_input_with_context(self, user_input: str, \n                                       mention_contents: Dict[str, Any]) -> str:\n        \"\"\"格式化用户输入，包含@引用上下文\"\"\"\n        if not mention_contents:\n            return user_input\n        \n        formatted_parts = [user_input]\n        \n        # 添加@引用的具体内容\n        for mention, content in mention_contents.items():\n            if content.get(\"mention_type\") == \"user\":\n                # 用户相关@引用\n                if \"handler_result\" in content:\n                    handler_result = content[\"handler_result\"]\n                    if handler_result.get(\"success\"):\n                        data = handler_result.get(\"data\", {})\n                        if mention == \"user-profile\":\n                            profile = data.get(\"profile\", {})\n                            if profile:\n                                formatted_parts.append(f\"\\n[用户画像：{json.dumps(profile, ensure_ascii=False)}]\")\n                        elif mention == \"user-memory\":\n                            memories = data.get(\"memories\", [])\n                            if memories:\n                                memory_texts = [m[\"content\"] for m in memories[:3]]\n                                formatted_parts.append(f\"\\n[用户记忆：{'; '.join(memory_texts)}]\")\n                        elif mention == \"user-preferences\":\n                            prefs = data.get(\"preferences\", {})\n                            if prefs:\n                                formatted_parts.append(f\"\\n[用户偏好：{json.dumps(prefs, ensure_ascii=False)}]\")\n        \n        return \"\\n\".join(formatted_parts)\n    \n    def _post_process_response(self, response_data: Dict[str, Any], \n                              user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"后处理响应，生成产出物等\"\"\"\n        \n        response_text = response_data.get(\"response\", \"\")\n        \n        # 1. 学习用户反馈（如果有明确的满意度信号）\n        self._learn_from_response_context(user_input, response_text, context)\n        \n        # 2. 检查是否需要生成产出物\n        deliverables = self._check_and_generate_deliverables(response_text, context)\n        \n        # 3. 构建最终结果\n        final_result = {\n            \"success\": True,\n            \"data\": {\n                \"agent_id\": self.agent_id,\n                \"agent_name\": self.name,\n                \"response\": response_text,\n                \"usage\": response_data.get(\"usage\", {}),\n                \"model\": response_data.get(\"model\", \"\"),\n                \"deliverables\": deliverables,\n                \"user_learning\": {\n                    \"profile_updated\": context.get(\"profile_updated\", False),\n                    \"preferences_learned\": context.get(\"preferences_learned\", False)\n                }\n            }\n        }\n        \n        return final_result\n    \n    def _learn_from_response_context(self, user_input: str, response: str, \n                                   context: Dict[str, Any]):\n        \"\"\"从响应上下文中学习\"\"\"\n        try:\n            # 检测用户满意度信号\n            satisfaction_signals = {\n                \"positive\": [\"很好\", \"不错\", \"满意\", \"正是我要的\", \"完美\", \"谢谢\"],\n                \"negative\": [\"不对\", \"错了\", \"不是这样\", \"太复杂\", \"太简单\", \"不够详细\"]\n            }\n            \n            # 这里简化处理，实际可以用更复杂的NLP分析\n            user_input_lower = user_input.lower()\n            \n            for sentiment, signals in satisfaction_signals.items():\n                for signal in signals:\n                    if signal in user_input_lower:\n                        feedback_score = 0.8 if sentiment == \"positive\" else 0.2\n                        \n                        # 学习沟通风格偏好\n                        self.user_memory.process({\n                            \"action\": \"learn_preference\",\n                            \"category\": \"communication\",\n                            \"preference\": \"current_style\",  # 实际应该是具体的风格\n                            \"feedback\": feedback_score\n                        })\n                        break\n                        \n        except Exception as e:\n            self.logger.warning(f\"Failed to learn from response context: {e}\")\n    \n    def _check_and_generate_deliverables(self, response: str, \n                                        context: Dict[str, Any]) -> List[Dict[str, Any]]:\n        \"\"\"检查并生成产出物\"\"\"\n        deliverables = []\n        \n        try:\n            # 检查响应是否包含重要的结构化内容\n            # 这里可以根据具体需求实现更复杂的检测逻辑\n            \n            # 简单示例：如果响应很长且包含分析内容，生成报告产出物\n            if len(response) > 500 and any(keyword in response for keyword in [\"分析\", \"报告\", \"总结\", \"建议\"]):\n                deliverable_id = f\"{self.agent_id}_report_{int(datetime.now().timestamp())}\"\n                deliverable_name = f\"{self.name}生成的{self.role}报告\"\n                \n                # 注册为@引用对象\n                self.mention_processor.register_deliverable_mention(\n                    deliverable_id=deliverable_id,\n                    deliverable_name=deliverable_name,\n                    content_type=\"text/markdown\"\n                )\n                \n                deliverables.append({\n                    \"id\": deliverable_id,\n                    \"name\": deliverable_name,\n                    \"type\": \"report\",\n                    \"content\": response,\n                    \"generated_by\": self.agent_id,\n                    \"generated_at\": datetime.now().isoformat(),\n                    \"mention\": f\"@{deliverable_id}\"\n                })\n        \n        except Exception as e:\n            self.logger.warning(f\"Failed to generate deliverables: {e}\")\n        \n        return deliverables\n    \n    # 便捷方法\n    def chat(self, message: str, conversation_history: List[Dict] = None) -> str:\n        \"\"\"便捷的对话方法\"\"\"\n        result = self.process_user_input(message, conversation_history)\n        \n        if result[\"success\"]:\n            return result[\"data\"][\"response\"]\n        else:\n            return f\"抱歉，处理出现问题：{result.get('error', '未知错误')}\"\n    \n    def get_agent_info(self) -> Dict[str, Any]:\n        \"\"\"获取智能体信息\"\"\"\n        return {\n            \"agent_id\": self.agent_id,\n            \"name\": self.name,\n            \"description\": self.description,\n            \"role\": self.role,\n            \"capabilities\": self.capabilities,\n            \"personality\": self.personality,\n            \"mention_format\": f\"@{self.agent_id}\",\n            \"status\": \"active\"\n        }\n    \n    def get_user_context_summary(self) -> Dict[str, Any]:\n        \"\"\"获取当前用户上下文摘要\"\"\"\n        return self.user_memory.get_user_context_for_agents()\n    \n    def learn_user_preference(self, category: str, preference: str, feedback: float):\n        \"\"\"便捷的用户偏好学习方法\"\"\"\n        return self.user_memory.process({\n            \"action\": \"learn_preference\",\n            \"category\": category,\n            \"preference\": preference,\n            \"feedback\": feedback\n        })"