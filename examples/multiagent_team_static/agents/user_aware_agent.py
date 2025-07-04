"""
用户感知智能体 - 基于FuturEmbryo框架的静态团队Agent

提供用户感知、记忆管理和@引用处理能力
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from futurembryo.cells.llm_cell import LLMCell
from cells.user_memory_cell import UserMemoryCell
from cells.mention_processor_cell import MentionProcessorCell


class UserAwareAgent:
    """用户感知智能体"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """初始化智能体"""
        self.agent_id = agent_id
        self.config = config
        
        # 基本信息
        self.name = config.get("name", agent_id)
        self.description = config.get("description", "专业智能体")
        self.role = config.get("role", "assistant")
        self.expertise = config.get("expertise", [])
        
        # 系统提示词
        self.system_prompt = self._build_system_prompt()
        
        # 初始化LLM
        llm_config = {
            "model": config.get("model", "anthropic/claude-sonnet-4-20250514"),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2000),
            "system_prompt": self.system_prompt
        }
        self.llm_cell = LLMCell(model_name=llm_config["model"], config=llm_config)
        
        # 用户记忆管理
        user_memory_config = config.get("user_memory_config", {})
        self.user_memory = UserMemoryCell(user_memory_config)
        
        # @引用处理
        mention_config = config.get("mention_processor_config", {})
        self.mention_processor = MentionProcessorCell(mention_config)
        
        # 状态
        self.conversation_count = 0
        self.last_response = None
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        prompt_parts = [
            f"你是{self.name}，一个{self.description}。",
            f"你的角色是{self.role}。"
        ]
        
        if self.expertise:
            prompt_parts.append(f"你的专长领域包括：{', '.join(self.expertise)}。")
        
        # 添加基础指令
        prompt_parts.extend([
            "",
            "## 核心能力：",
            "1. 深入理解用户需求，提供专业的帮助",
            "2. 记住用户的偏好和历史交互",
            "3. 与其他专业Agent协作完成复杂任务",
            "4. 生成高质量的专业内容",
            "",
            "## 工作原则：",
            "- 保持专业性和准确性",
            "- 用清晰易懂的方式解释复杂概念",
            "- 主动考虑用户的背景和需求",
            "- 必要时建议与其他专业Agent协作",
            "",
            "请根据你的专业能力，为用户提供最好的帮助。"
        ])
        
        # 添加自定义提示
        if "custom_prompt" in self.config:
            prompt_parts.append("")
            prompt_parts.append(self.config["custom_prompt"])
        
        return "\n".join(prompt_parts)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "expertise": self.expertise,
            "conversation_count": self.conversation_count
        }
    
    def process_user_input(self, user_input: str, conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理用户输入"""
        try:
            # 提取@引用
            mentions = self.mention_processor.extract_mentions(user_input)
            
            # 获取用户上下文
            user_context = self.user_memory.get_user_context_for_agents()
            
            # 构建上下文信息
            context_info = self._build_context_info(user_context, mentions, conversation_history)
            
            # 构建增强的提示
            enhanced_prompt = self._build_enhanced_prompt(user_input, context_info)
            
            # 调用LLM
            llm_result = self.llm_cell({"input": enhanced_prompt})
            
            if llm_result["success"]:
                response = llm_result["data"]["response"]
                
                # 从交互中学习
                learning_result = self.user_memory.learn_from_interaction(user_input, response)
                
                # 处理响应中的@引用
                processed_response, response_mentions = self.mention_processor.process_mentions(response)
                
                # 检查是否生成了产出物
                deliverables = self._extract_deliverables(response)
                
                # 更新状态
                self.conversation_count += 1
                self.last_response = processed_response
                
                return {
                    "success": True,
                    "data": {
                        "response": processed_response,
                        "agent_name": self.name,
                        "agent_id": self.agent_id,
                        "mentions": mentions + [m["mention"] for m in response_mentions],
                        "deliverables": deliverables,
                        "user_learning": learning_result,
                        "tokens_used": llm_result["data"].get("usage", {})
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"LLM调用失败: {llm_result.get('error', '未知错误')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"处理失败: {str(e)}"
            }
    
    def _build_context_info(self, user_context: Dict[str, Any], 
                           mentions: List[str], 
                           conversation_history: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """构建上下文信息"""
        context_info = {
            "user_profile": user_context.get("user_profile", {}),
            "recent_memories": user_context.get("recent_memories", [])
        }
        
        # 添加@引用上下文
        if mentions:
            mention_context = self.mention_processor.create_mention_context(
                mentions, 
                {"user_memory": self.user_memory}
            )
            context_info["mentions"] = mention_context
        
        # 添加对话历史
        if conversation_history:
            context_info["conversation_history"] = conversation_history[-5:]  # 最近5轮
        
        return context_info
    
    def _build_enhanced_prompt(self, user_input: str, context_info: Dict[str, Any]) -> str:
        """构建增强的提示"""
        prompt_parts = []
        
        # 添加用户画像信息
        user_profile = context_info.get("user_profile", {})
        if user_profile.get("interests"):
            prompt_parts.append(f"用户兴趣: {', '.join(user_profile['interests'])}")
        
        # 添加相关记忆
        recent_memories = context_info.get("recent_memories", [])
        if recent_memories:
            prompt_parts.append("\n相关历史记忆:")
            for memory in recent_memories[-3:]:  # 最近3条
                prompt_parts.append(f"- {memory['content']}")
        
        # 添加对话历史
        if context_info.get("conversation_history"):
            prompt_parts.append("\n最近对话:")
            for msg in context_info["conversation_history"][-3:]:
                role = "用户" if msg["role"] == "user" else "助手"
                prompt_parts.append(f"{role}: {msg['content'][:100]}...")
        
        # 添加用户输入
        prompt_parts.append(f"\n当前用户输入: {user_input}")
        
        return "\n".join(prompt_parts)
    
    def _extract_deliverables(self, response: str) -> List[Dict[str, Any]]:
        """从响应中提取产出物"""
        deliverables = []
        
        # 简单的产出物检测逻辑
        if any(keyword in response for keyword in ["报告", "方案", "计划", "分析"]):
            # 注册为产出物
            deliverable_id = self.mention_processor.register_deliverable(
                name=f"{self.name}的输出",
                content=response,
                metadata={
                    "agent_id": self.agent_id,
                    "type": "text"
                }
            )
            
            deliverables.append({
                "id": deliverable_id,
                "name": f"{self.name}的输出",
                "mention": f"@{deliverable_id}"
            })
        
        return deliverables
    
    def collaborate_with(self, other_agent: 'UserAwareAgent', task: str) -> Dict[str, Any]:
        """与其他Agent协作"""
        # 这里可以实现Agent间的协作逻辑
        pass
    
    def reset(self):
        """重置Agent状态"""
        self.conversation_count = 0
        self.last_response = None
        self.user_memory.clear_memories()
        self.mention_processor.clear_deliverables()
    
    def export_state(self) -> Dict[str, Any]:
        """导出Agent状态"""
        return {
            "agent_info": self.get_agent_info(),
            "user_memory": self.user_memory.export_data(),
            "mention_processor": self.mention_processor.export_data(),
            "conversation_count": self.conversation_count
        }
    
    def import_state(self, state: Dict[str, Any]):
        """导入Agent状态"""
        if "user_memory" in state:
            self.user_memory.import_data(state["user_memory"])
        if "mention_processor" in state:
            self.mention_processor.import_data(state["mention_processor"])
        if "conversation_count" in state:
            self.conversation_count = state["conversation_count"]