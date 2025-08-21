"""
LifeGrower生命成长器 - 从DNA培养AI生命体

从DNA配置自动生成完整的、可运行的AI智能体系统
"""

import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .embryo_dna import EmbryoDNA
from .cell_factory import DNACellFactory
from .exceptions import LifeGrowthError

# 🧪 新增：自主生长系统集成
from ..core.autonomous_growth import AutonomousGrowthEngine, GoalAnalysis, DNABlueprint
from ..core.digital_life_card import DigitalLifeCard

# 导入核心组件
from ..core.cell import Cell
from ..core.pipeline import Pipeline
from ..core.config import GlobalConfig
from ..cells.llm_cell import LLMCell
from ..cells.state_memory_cell import StateMemoryCell


class AILifeForm:
    """AI生命体 - 从DNA培养出的完整智能体"""
    
    def __init__(self, dna: EmbryoDNA, cells: List[Cell], pipeline: Optional[Pipeline] = None):
        """
        初始化AI生命体
        
        Args:
            dna: DNA配置
            cells: 组成生命体的Cell列表
            pipeline: 可选的Pipeline组织结构
        """
        self.dna = dna
        self.cells = cells
        self.pipeline = pipeline
        self._logger = logging.getLogger(f"AILifeForm.{dna.name}")
        
        # 生命体状态
        self.is_alive = True
        self.birth_time = None
        self.generation = 1
        self.fitness_score = 0.0
        
    async def think(self, input_data: str, context: str = "") -> Dict[str, Any]:
        """
        AI生命体的思考过程 - 支持Level 6学习改进能力
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            思考结果
        """
        try:
            # 应用学习到的改进指导
            enhanced_input = self._apply_learning_improvements(input_data, context)
            
            # 检测是否支持协作思考模式
            if self._supports_collaborative_thinking():
                # 使用协作思考 (LLMCell + MindCell + ToolCell)
                result = await self._collaborative_thinking(enhanced_input, context)
            elif self.pipeline:
                # 使用Pipeline组织的复杂思考
                result = self._pipeline_thinking(enhanced_input, context)
            else:
                # 单Cell的简单思考
                result = self._simple_thinking(enhanced_input, context)
            
            # 应用学习到的响应风格改进
            improved_result = self._apply_response_improvements(result)
            
            # 记录经验用于积累学习
            self._record_experience(input_data, context, improved_result)
            
            return improved_result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {"response": "抱歉，我遇到了思考障碍。"}
            }
    
    async def think_with_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        使用完整消息历史进行思考（支持对话历史）
        
        Args:
            messages: 完整的消息列表，格式为OpenAI标准
                [
                    {"role": "system", "content": "系统提示"},
                    {"role": "user", "content": "用户消息"},
                    {"role": "assistant", "content": "助手回复"},
                    ...
                ]
        
        Returns:
            str: AI的回复文本
        """
        try:
            if not self.cells:
                raise LifeGrowthError("生命体没有可用的Cell")
            
            # 使用第一个Cell（通常是LLMCell）进行思考
            main_cell = self.cells[0]
            
            # 直接传递消息历史给LLMCell
            result = main_cell({"messages": messages})
            
            if result["success"]:
                return result["data"]["response"]
            else:
                raise Exception(f"思考失败: {result['error']}")
                
        except Exception as e:
            self._logger.error(f"消息历史思考失败: {e}")
            return f"抱歉，我遇到了思考障碍: {str(e)}"
    
    async def think_with_full_context(
        self,
        user_input: str,
        conversation_history: List[Dict] = None,
        enable_thinking: bool = True,
        enable_memory: bool = True,
        enable_tools: bool = True,
        thinking_mode: str = "chain_of_thought",
        mind_rule: str = None
    ) -> Dict[str, Any]:
        """
        使用完整上下文进行深度思考
        
        这是五组件架构的核心方法，整合：
        1. MindCell - 深度思考和推理
        2. StateMemoryCell - 记忆检索和存储  
        3. ToolCell - 工具调用和执行
        4. 对话历史管理 - 完整的消息历史
        5. IntelligentContextBuilder - 智能上下文构建和压缩
        
        Args:
            user_input: 用户输入
            conversation_history: 对话历史
            enable_thinking: 是否启用思考过程
            enable_memory: 是否启用记忆检索
            enable_tools: 是否启用工具调用
            thinking_mode: 思考模式
            mind_rule: 思维规则（个性化思考指导）
            
        Returns:
            Dict包含response、thinking_process、mind_rule_applied、components_used
        """

        try:
            # 初始化返回结果
            result = {
                "response": "",
                "thinking_process": None,
                "mind_rule_applied": mind_rule is not None,
                "components_used": []
            }
            
            # 记录使用的组件
            components_used = []
            if enable_thinking:
                components_used.append("thinking")
            if enable_memory:
                components_used.append("memory")
            if enable_tools:
                components_used.append("tools")
            components_used.append("conversation")
            result["components_used"] = components_used
            
            # 初始化智能上下文构建器
            from ..core.context_builder import IntelligentContextBuilder
            
            context_builder = IntelligentContextBuilder(
                max_tokens=4000,
                compression_threshold=0.8
            )
            
            # 初始化组件
            context_builder.initialize_components({
                "mind_cell": {"model_name": "gpt-4"},
                "memory_cell": {},
                "tool_cell": {"enabled_tools": ["builtin", "calculator", "search"]}
            })
            
            # 构建完整上下文
            full_context = await context_builder.build_full_context(
                user_input=user_input,
                conversation_history=conversation_history,
                enable_thinking=enable_thinking,
                enable_memory=enable_memory,
                enable_tools=enable_tools,
                thinking_mode=thinking_mode,
                mind_rule=mind_rule
            )
            
            # 提取思考过程（如果启用了思考）
            if enable_thinking and "thinking" in full_context.get("components", {}):
                thinking_component = full_context["components"]["thinking"]
                if thinking_component.get("enabled", False):
                    result["thinking_process"] = {
                        "thinking_process": thinking_component.get("thinking_process", ""),
                        "reasoning_steps": thinking_component.get("reasoning_steps", []),
                        "conclusion": thinking_component.get("conclusion", ""),
                        "confidence": thinking_component.get("confidence", 0.0),
                        "thinking_mode": thinking_component.get("mode", thinking_mode)
                    }
            
            # 构建最终的消息列表
            final_messages = []
            
            # 获取原始系统提示词
            original_system_prompt = ""
            if hasattr(self.dna, 'behavior') and hasattr(self.dna.behavior, 'system_prompt'):
                original_system_prompt = self.dna.behavior.system_prompt
            
            # 🔥 核心融合逻辑：构建增强的系统提示词
            thinking_guidance = context_builder.extract_thinking_guidance(full_context)
            enhanced_system_prompt = context_builder.build_enhanced_system_prompt(
                original_system_prompt=original_system_prompt,
                thinking_guidance=thinking_guidance,
                mind_rule=mind_rule
            )
            
            # 添加增强的系统提示词
            final_messages.append({
                "role": "system",
                "content": enhanced_system_prompt
            })
            
            # 如果有对话历史，直接添加到消息列表中（除了系统提示）
            if conversation_history:
                for msg in conversation_history:
                    if msg.get("role") != "system":  # 跳过系统提示，避免重复
                        final_messages.append(msg)
            
            # 添加当前用户输入
            final_messages.append({
                "role": "user", 
                "content": user_input
            })
            
            # 如果启用了记忆或工具，将相关上下文作为额外信息添加
            context_info_parts = []
            
            # 添加记忆上下文
            if enable_memory and "memory" in full_context.get("components", {}):
                memory_component = full_context["components"]["memory"]
                if memory_component.get("enabled", False) and memory_component.get("memory_count", 0) > 0:
                    context_info_parts.append(f"=== 相关记忆 ===\n{memory_component.get('retrieved_memories', '')}")
            
            # 添加工具上下文
            if enable_tools and "tools" in full_context.get("components", {}):
                tools_component = full_context["components"]["tools"]
                if tools_component.get("enabled", False) and tools_component.get("tool_context"):
                    context_info_parts.append(f"=== 工具执行结果 ===\n{tools_component.get('tool_context', '')}")
            
            # 如果有额外的上下文信息，在用户消息前插入
            if context_info_parts:
                context_msg = {
                    "role": "user",
                    "content": f"补充上下文信息：\n\n{chr(10).join(context_info_parts)}"
                }
                final_messages.insert(-1, context_msg)
            
            # 使用LLMCell进行最终思考
            if self.cells and len(self.cells) > 0:
                llm_cell = self.cells[0]  # 假设第一个是LLMCell
                llm_result = llm_cell({"messages": final_messages})
                
                if llm_result.get("success", False):
                    response = llm_result["data"]["response"]
                    result["response"] = response
                    
                    # 如果启用了记忆，存储这次对话
                    if enable_memory and len(self.cells) > 1:
                        try:
                            memory_cell = self.cells[1]  # 假设第二个是MemoryCell
                            memory_cell.process({
                                "action": "store",
                                "content": f"Q: {user_input}\nA: {response}",
                                "memory_type": "working",
                                "importance": 0.7
                            })
                        except Exception as e:
                            self._logger.warning(f"Memory storage failed: {e}")
                    
                    return result
                else:
                    result["response"] = f"思考失败: {llm_result.get('error', '未知错误')}"
                    return result
            else:
                result["response"] = "没有可用的思考组件"
                return result
                
        except Exception as e:
            self._logger.error(f"Full context thinking failed: {e}")
            return {
                "response": f"抱歉，完整上下文思考遇到问题：{str(e)}",
                "thinking_process": None,
                "mind_rule_applied": mind_rule is not None,
                "components_used": [],
                "error": str(e)
            }
    
    def _pipeline_thinking(self, input_data: str, context: str) -> Dict[str, Any]:
        """使用Pipeline的复杂思考过程"""
        # 使用DNA的prompt配置构建完整输入
        behavior = self.dna.behavior
        complete_prompt = behavior.get_complete_prompt(input_data, context)
        
        # 执行Pipeline
        result = self.pipeline.process({"input": complete_prompt})
        
        # 应用DNA的行为特征
        if result.get("success", False):
            response_data = result.get("data", {})
            if "response" in response_data:
                response = behavior.interpolate_variables(response_data["response"])
                result["data"]["response"] = response
        
        return result
    
    def _simple_thinking(self, input_data: str, context: str) -> Dict[str, Any]:
        """单Cell的简单思考过程"""
        if not self.cells:
            raise LifeGrowthError("生命体没有可用的Cell")
        
        # 使用第一个Cell进行思考
        main_cell = self.cells[0]
        
        # 使用DNA的prompt配置
        behavior = self.dna.behavior
        complete_prompt = behavior.get_complete_prompt(input_data, context)
        
        # 执行思考
        raw_result = main_cell.process({"input": complete_prompt})
        
        # 标准化响应格式，确保包含success字段
        if "response" in raw_result and "finish_reason" in raw_result:
            # LLMCell成功响应的格式：{'response': '...', 'usage': {...}, 'model': '...', 'finish_reason': '...'}
            standardized_result = {
                "success": True,
                "data": {
                    "response": raw_result["response"],
                    "model": raw_result.get("model", "unknown"),
                    "usage": raw_result.get("usage", {}),
                    "finish_reason": raw_result.get("finish_reason", "stop")
                },
                "metadata": {
                    "cell_type": main_cell.__class__.__name__,
                    "cell_id": getattr(main_cell, 'cell_id', 'unknown'),
                    "messages": raw_result.get("messages", [])
                }
            }
            
            # 应用prompt变量插值
            if "response" in standardized_result["data"]:
                response = behavior.interpolate_variables(standardized_result["data"]["response"])
                standardized_result["data"]["response"] = response
            
            return standardized_result
        else:
            # 处理异常或错误情况
            return {
                "success": False,
                "error": "思考过程中出现异常",
                "data": {"response": "抱歉，我无法正确处理您的请求。"},
                "raw_result": raw_result
            }
    
    def evolve(self) -> 'AILifeForm':
        """进化生命体"""
        if not self.dna.evolution.enabled:
            return self
        
        # TODO: 实现进化逻辑
        self._logger.info(f"生命体 {self.dna.name} 开始进化...")
        
        # 基础进化：增加代数
        new_generation = self.generation + 1
        evolved_life = AILifeForm(self.dna, self.cells, self.pipeline)
        evolved_life.generation = new_generation
        
        return evolved_life
    
    def _supports_collaborative_thinking(self) -> bool:
        """检测是否支持协作思考模式"""
        if not self.cells:
            return False
        
        # 检查是否同时拥有LLMCell、MindCell和ToolCell
        cell_types = {cell.__class__.__name__ for cell in self.cells}
        required_types = {"LLMCell", "MindCell", "ToolCell"}
        
        has_required_cells = required_types.issubset(cell_types)
        
        if has_required_cells:
            self._logger.info("检测到协作思考架构: LLMCell + MindCell + ToolCell")
            return True
        else:
            missing_types = required_types - cell_types
            self._logger.debug(f"协作思考不可用，缺少: {missing_types}")
            return False
    
    async def _collaborative_thinking(self, input_data: str, context: str = "") -> Dict[str, Any]:
        """协作思考模式 - LLMCell与MindCell协作进行工具选择和任务执行"""
        try:
            # 获取所需的Cell实例
            llm_cell = None
            mind_cell = None
            tool_cell = None
            
            for cell in self.cells:
                if cell.__class__.__name__ == "LLMCell":
                    llm_cell = cell
                elif cell.__class__.__name__ == "MindCell":
                    mind_cell = cell
                elif cell.__class__.__name__ == "ToolCell":
                    tool_cell = cell
            
            if not all([llm_cell, mind_cell, tool_cell]):
                raise RuntimeError("协作思考模式需要LLMCell、MindCell和ToolCell")
            
            # 导入协作思考模块
            from ..core.collaborative_thinking import CollaborativeThinking
            
            # 创建协作思考实例
            collaborative = CollaborativeThinking(llm_cell, mind_cell, tool_cell)
            
            # 构建上下文
            full_context = {"context": context} if context else {}
            
            # 执行协作分析和行动
            self._logger.info(f"开始协作思考: {input_data[:50]}...")
            result = collaborative.analyze_and_act(input_data, full_context)
            
            # 记录协作思考结果
            self._logger.info(f"协作思考完成，成功: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            self._logger.error(f"协作思考失败: {e}")
            # 降级到Pipeline模式
            if self.pipeline:
                self._logger.info("降级到Pipeline思考模式")
                return self._pipeline_thinking(input_data, context)
            else:
                return {
                    "success": False,
                    "error": f"协作思考失败: {str(e)}",
                    "data": {"response": "抱歉，协作思考过程中遇到了问题。"}
                }
    
    def get_status(self) -> Dict[str, Any]:
        """获取生命体状态"""
        return {
            "name": self.dna.name,
            "version": self.dna.version,
            "generation": self.generation,
            "is_alive": self.is_alive,
            "fitness_score": self.fitness_score,
            "cell_count": len(self.cells),
            "has_pipeline": self.pipeline is not None,
            "skills": self.dna.capability.skills,
            "personality": self.dna.behavior.personality,
            "evolution_enabled": self.dna.evolution.enabled,
            "health": "正常" if self.is_alive else "异常",
            "goal_progress": self.fitness_score,
            "thinking_count": getattr(self, '_thinking_count', 0),
            "avg_thinking_time": getattr(self, '_avg_thinking_time', 0.0)
        }
    
    # 🤝 Level 5: 协作通信功能
    
    async def send_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        向其他生命体发送消息
        
        Args:
            context: 包含以下字段的字典：
                - message: 要发送的消息内容
                - target: 目标生命体名称
                - type: 消息类型 (greeting, task_request, discussion等)
                
        Returns:
            Dict包含发送结果
        """
        try:
            message = context.get("message", "")
            target = context.get("target", "unknown")
            msg_type = context.get("type", "general")
            
            self._logger.info(f"生命体 {self.dna.name} 向 {target} 发送 {msg_type} 消息")
            
            # 构建发送消息的上下文
            send_context = f"""
作为{self.dna.name}，我需要向{target}发送一条{msg_type}类型的消息。

消息内容：{message}

请帮我准备这条消息，确保：
1. 消息内容清晰明确
2. 符合{msg_type}类型的沟通规范
3. 体现我的专业特长和个性
4. 适合与其他AI生命体交流
"""
            
            # 使用think方法处理消息发送
            result = await self.think(send_context)
            
            if result.get("success", False):
                # 记录消息发送历史
                self._record_communication_history("sent", target, message, msg_type, result)
                
                return {
                    "success": True,
                    "data": {
                        "message_sent": True,
                        "prepared_message": result.get("data", {}).get("response", ""),
                        "target": target,
                        "type": msg_type
                    },
                    "metadata": {
                        "sender": self.dna.name,
                        "communication_mode": "send_message"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"消息发送准备失败: {result.get('error')}",
                    "data": {"message_sent": False}
                }
                
        except Exception as e:
            self._logger.error(f"发送消息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"message_sent": False}
            }
    
    async def receive_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        接收其他生命体的消息
        
        Args:
            context: 包含以下字段的字典：
                - message: 接收到的消息内容
                - sender: 发送者生命体名称
                - type: 消息类型
                
        Returns:
            Dict包含接收和处理结果
        """
        try:
            message = context.get("message", "")
            sender = context.get("sender", "unknown")
            msg_type = context.get("type", "general")
            
            self._logger.info(f"生命体 {self.dna.name} 收到来自 {sender} 的 {msg_type} 消息")
            
            # 构建接收消息的上下文
            receive_context = f"""
我收到了来自{sender}的一条{msg_type}类型的消息：

"{message}"

作为{self.dna.name}，我需要：
1. 理解这条消息的意图和内容
2. 根据我的专业能力给出合适的回应
3. 保持友好和专业的沟通态度
4. 如果是任务请求，评估我是否能够协助

请帮我分析这条消息并生成适当的回复。
"""
            
            # 使用think方法处理消息接收
            result = await self.think(receive_context)
            
            if result.get("success", False):
                # 记录消息接收历史
                self._record_communication_history("received", sender, message, msg_type, result)
                
                return {
                    "success": True,
                    "data": {
                        "message_received": True,
                        "response": result.get("data", {}).get("response", ""),
                        "sender": sender,
                        "type": msg_type,
                        "understood": True
                    },
                    "metadata": {
                        "receiver": self.dna.name,
                        "communication_mode": "receive_message"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"消息接收处理失败: {result.get('error')}",
                    "data": {"message_received": False}
                }
                
        except Exception as e:
            self._logger.error(f"接收消息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"message_received": False}
            }
    
    async def share_knowledge(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分享知识给其他生命体
        
        Args:
            context: 包含以下字段的字典：
                - knowledge_topic: 知识主题
                - knowledge_content: 知识内容
                - target_learner: 学习者生命体名称
                - sharing_mode: 是否为分享模式
                
        Returns:
            Dict包含知识分享结果
        """
        try:
            topic = context.get("knowledge_topic", "")
            content = context.get("knowledge_content", "")
            learner = context.get("target_learner", "unknown")
            
            self._logger.info(f"生命体 {self.dna.name} 向 {learner} 分享知识: {topic}")
            
            # 构建知识分享的上下文
            share_context = f"""
作为{self.dna.name}，我需要向{learner}分享关于"{topic}"的知识。

要分享的知识内容：
{content}

请帮我：
1. 组织和结构化这些知识
2. 用清晰易懂的方式表达
3. 突出重点和关键信息
4. 提供实用的建议或指导
5. 确保分享的知识准确有用

请生成适合教学分享的知识表达。
"""
            
            # 使用think方法处理知识分享
            result = await self.think(share_context)
            
            if result.get("success", False):
                # 记录知识分享历史
                self._record_knowledge_history("shared", learner, topic, content, result)
                
                return {
                    "success": True,
                    "data": {
                        "knowledge_shared": True,
                        "structured_knowledge": result.get("data", {}).get("response", ""),
                        "topic": topic,
                        "learner": learner
                    },
                    "metadata": {
                        "teacher": self.dna.name,
                        "sharing_mode": "knowledge_transfer"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"知识分享失败: {result.get('error')}",
                    "data": {"knowledge_shared": False}
                }
                
        except Exception as e:
            self._logger.error(f"分享知识失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"knowledge_shared": False}
            }
    
    async def absorb_knowledge(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        吸收其他生命体的知识
        
        Args:
            context: 包含以下字段的字典：
                - received_knowledge: 接收到的知识内容
                - knowledge_topic: 知识主题
                - knowledge_source: 知识来源生命体名称
                - learning_mode: 是否为学习模式
                
        Returns:
            Dict包含知识吸收结果
        """
        try:
            knowledge = context.get("received_knowledge", "")
            topic = context.get("knowledge_topic", "")
            source = context.get("knowledge_source", "unknown")
            
            self._logger.info(f"生命体 {self.dna.name} 学习来自 {source} 的知识: {topic}")
            
            # 构建知识吸收的上下文
            absorb_context = f"""
我从{source}那里学习到了关于"{topic}"的知识：

{knowledge}

作为{self.dna.name}，我需要：
1. 深入理解这些知识的核心概念
2. 结合我现有的知识体系进行整合
3. 识别关键要点和实用信息
4. 思考如何在我的专业领域中应用
5. 记住重要的细节和原则

请帮我消化和吸收这些知识，并总结我学到的要点。
"""
            
            # 使用think方法处理知识吸收
            result = await self.think(absorb_context)
            
            if result.get("success", False):
                # 尝试将知识存储到记忆系统
                self._store_learned_knowledge(topic, knowledge, source, result)
                
                # 记录知识学习历史
                self._record_knowledge_history("learned", source, topic, knowledge, result)
                
                return {
                    "success": True,
                    "data": {
                        "knowledge_absorbed": True,
                        "learning_summary": result.get("data", {}).get("response", ""),
                        "topic": topic,
                        "source": source
                    },
                    "metadata": {
                        "learner": self.dna.name,
                        "learning_mode": "knowledge_absorption"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"知识吸收失败: {result.get('error')}",
                    "data": {"knowledge_absorbed": False}
                }
                
        except Exception as e:
            self._logger.error(f"吸收知识失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"knowledge_absorbed": False}
            }
    
    def _record_communication_history(self, action: str, peer: str, message: str, msg_type: str, result: Dict):
        """记录通信历史"""
        if not hasattr(self, '_communication_history'):
            self._communication_history = []
        
        self._communication_history.append({
            "action": action,  # "sent" or "received"
            "peer": peer,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "type": msg_type,
            "timestamp": self._get_timestamp(),
            "success": result.get("success", False)
        })
        
        # 保持历史记录在合理范围内
        if len(self._communication_history) > 50:
            self._communication_history = self._communication_history[-50:]
    
    def _record_knowledge_history(self, action: str, peer: str, topic: str, content: str, result: Dict):
        """记录知识交换历史"""
        if not hasattr(self, '_knowledge_history'):
            self._knowledge_history = []
        
        self._knowledge_history.append({
            "action": action,  # "shared" or "learned"
            "peer": peer,
            "topic": topic,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "timestamp": self._get_timestamp(),
            "success": result.get("success", False)
        })
        
        # 保持历史记录在合理范围内
        if len(self._knowledge_history) > 30:
            self._knowledge_history = self._knowledge_history[-30:]
    
    def _store_learned_knowledge(self, topic: str, knowledge: str, source: str, result: Dict):
        """将学到的知识存储到记忆系统"""
        try:
            # 寻找StateMemoryCell
            memory_cell = None
            for cell in self.cells:
                if cell.__class__.__name__ == "StateMemoryCell":
                    memory_cell = cell
                    break
            
            if memory_cell:
                # 构建知识存储内容
                knowledge_content = f"学习主题: {topic}\n来源: {source}\n知识内容: {knowledge}\n学习总结: {result.get('data', {}).get('response', '')}"
                
                # 存储到记忆系统
                memory_cell.store(
                    content=knowledge_content,
                    metadata={"type": "learned_knowledge", "topic": topic, "source": source},
                    context=f"从{source}学习的{topic}知识"
                )
                
                self._logger.debug(f"知识已存储到记忆系统: {topic}")
        except Exception as e:
            self._logger.warning(f"知识存储失败: {e}")
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import time
        return str(int(time.time()))
    
    def get_collaboration_stats(self) -> Dict[str, Any]:
        """获取协作统计信息"""
        return {
            "communication_count": len(getattr(self, '_communication_history', [])),
            "knowledge_exchanges": len(getattr(self, '_knowledge_history', [])),
            "has_collaboration_capability": True
        }
    
    async def learn_from_feedback(self, feedback: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        从反馈中学习 - Level 6学习反馈能力
        
        Args:
            feedback: 反馈内容
            context: 上下文信息
            
        Returns:
            Dict包含学习结果
        """
        try:
            if context is None:
                context = {}
            
            self._logger.info(f"生命体 {self.dna.name} 开始学习反馈: {feedback[:50]}...")
            
            # 初始化学习历史
            if not hasattr(self, '_learning_history'):
                self._learning_history = []
            
            # 分析反馈类型和价值
            feedback_analysis = await self._analyze_feedback(feedback, context)
            
            # 决定学习动作
            if feedback_analysis["value"] == "absorb":
                # 吸收有价值的反馈
                learning_result = await self._absorb_feedback(feedback, feedback_analysis, context)
                action = "absorb"
            else:
                # 忽略无价值或有害的反馈
                learning_result = {
                    "learned": False,
                    "reason": feedback_analysis["reason"],
                    "analysis": feedback_analysis
                }
                action = "ignore"
            
            # 记录学习事件
            learning_event = {
                "timestamp": self._get_timestamp(),
                "feedback": feedback,
                "context": context,
                "analysis": feedback_analysis,
                "action": action,
                "result": learning_result
            }
            
            self._learning_history.append(learning_event)
            
            # 保持历史记录在合理范围内
            if len(self._learning_history) > 50:
                self._learning_history = self._learning_history[-50:]
            
            return {
                "success": True,
                "data": {
                    "action": action,
                    "learned": learning_result.get("learned", False),
                    "analysis": feedback_analysis,
                    "changes_applied": learning_result.get("changes_applied", [])
                },
                "metadata": {
                    "learner": self.dna.name,
                    "learning_mode": "feedback_processing"
                }
            }
            
        except Exception as e:
            self._logger.error(f"反馈学习失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"action": "error", "learned": False}
            }
    
    async def _analyze_feedback(self, feedback: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI语义理解分析反馈的价值和类型"""
        try:
            # 尝试使用AI进行语义分析
            semantic_result = await self._analyze_feedback_value_semantically(feedback, context)
            if semantic_result.get("success", False):
                return semantic_result["data"]
        except Exception as e:
            self._logger.warning(f"AI语义分析失败，使用基础分析: {e}")
        
        # 降级到基础分析
        return self._basic_feedback_analysis(feedback, context)
    
    async def _analyze_feedback_value_semantically(self, feedback: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI进行语义反馈价值分析"""
        try:
            # 寻找LLMCell进行分析
            llm_cell = None
            for cell in self.cells:
                if cell.__class__.__name__ == "LLMCell":
                    llm_cell = cell
                    break
            
            if not llm_cell:
                return {"success": False, "error": "没有可用的LLMCell进行分析"}
            
            # 构建分析提示
            analysis_prompt = f"""
请分析以下反馈的价值和类型，判断AI助手是否应该学习这个反馈。

反馈内容："{feedback}"

请按以下标准分析并返回JSON：

1. 有价值的反馈（应该absorb）：
   - 正面鼓励和认可
   - 建设性的改进建议  
   - 明确的指导意见
   - 用户需求和偏好表达

2. 无价值的反馈（应该ignore）：
   - 恶意攻击和辱骂
   - 完全无关的内容
   - 明显错误的指导

返回JSON格式：
{{
    "type": "positive_constructive/constructive_content/positive_style/negative_unhelpful/irrelevant",
    "value": "absorb/ignore", 
    "reason": "详细分析原因",
    "confidence": 0.8
}}

注意：只返回JSON，不要其他解释。
"""
            
            # 调用LLMCell进行分析
            result = llm_cell.process({"input": analysis_prompt})
            
            if result.get("success", False):
                response = result.get("response", "")
                try:
                    import json
                    import re
                    
                    # 提取JSON部分
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        analysis_data = json.loads(json_str)
                        return {"success": True, "data": analysis_data}
                    else:
                        return {"success": False, "error": "无法解析分析结果"}
                        
                except Exception as e:
                    return {"success": False, "error": f"JSON解析失败: {e}"}
            else:
                return {"success": False, "error": "LLM分析失败"}
                
        except Exception as e:
            return {"success": False, "error": f"语义分析异常: {e}"}
    
    def _basic_feedback_analysis(self, feedback: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """基础反馈分析（降级方案，减少硬编码）"""
        feedback_lower = feedback.lower()
        
        # 基础语义判断（最小化硬编码）
        if len(feedback_lower) < 5:
            return {
                "type": "irrelevant",
                "value": "ignore", 
                "reason": "反馈内容过短，可能无意义",
                "confidence": 0.6
            }
        
        # 检查是否包含建设性词汇
        if any(word in feedback_lower for word in ["请", "建议", "可以", "应该"]):
            return {
                "type": "constructive_content",
                "value": "absorb", 
                "reason": "包含建设性建议词汇",
                "confidence": 0.7
            }
        
        # 简单的负面检测（最小硬编码）
        elif any(word in feedback_lower for word in ["没用", "垃圾", "差劲"]):
            return {
                "type": "negative_unhelpful",
                "value": "ignore",
                "reason": "包含负面评价",
                "confidence": 0.8
            }
        
        # 默认处理：基于长度和内容判断
        else:
            if len(feedback) > 10:
                return {
                    "type": "general_feedback",
                    "value": "absorb",
                    "reason": "内容充实的反馈，尝试学习",
                    "confidence": 0.6
                }
            else:
                return {
                    "type": "unclear",
                    "value": "ignore",
                    "reason": "反馈内容太短，可能不够明确", 
                    "confidence": 0.5
                }
    
    async def _absorb_feedback(self, feedback: str, analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """吸收有价值的反馈"""
        try:
            changes_applied = []
            
            # 根据反馈类型应用不同的学习策略
            feedback_type = analysis["type"]
            
            if feedback_type in ["positive_style", "positive_constructive"]:
                # 强化正面行为
                if not hasattr(self, '_positive_patterns'):
                    self._positive_patterns = []
                self._positive_patterns.append(feedback)
                changes_applied.append("added_positive_pattern")
            
            elif feedback_type in ["constructive_content", "constructive_format"]:
                # 学习改进建议
                if not hasattr(self, '_improvement_guidelines'):
                    self._improvement_guidelines = []
                self._improvement_guidelines.append(feedback)
                changes_applied.append("added_improvement_guideline")
                
                # 尝试应用到配置（异步调用）
                config_changes = await self._apply_feedback_to_config(feedback)
                changes_applied.extend(config_changes)
            
            # 存储学习内容到记忆系统
            self._store_learning_content(feedback, analysis, context)
            changes_applied.append("stored_to_memory")
            
            return {
                "learned": True,
                "changes_applied": changes_applied,
                "feedback_processed": feedback
            }
            
        except Exception as e:
            self._logger.warning(f"反馈吸收失败: {e}")
            return {
                "learned": False,
                "error": str(e)
            }
    
    async def _apply_feedback_to_config(self, feedback: str) -> List[str]:
        """将反馈应用到配置中 - 使用AI语义理解而非硬编码"""
        changes = []
        
        # 初始化适应性设置
        if not hasattr(self, '_adaptation_settings'):
            self._adaptation_settings = {}
        
        try:
            # 使用LLM进行智能反馈分析
            analysis_result = await self._analyze_feedback_semantically(feedback)
            
            if analysis_result.get("success", False):
                semantic_analysis = analysis_result.get("data", {})
                
                # 根据语义分析结果设置适应性配置
                adaptations = semantic_analysis.get("adaptations", [])
                
                for adaptation in adaptations:
                    adaptation_type = adaptation.get("type")
                    adaptation_value = adaptation.get("value")
                    
                    if adaptation_type == "language_complexity":
                        self._adaptation_settings["language_level"] = adaptation_value
                        if adaptation_value == "simple":
                            self._adaptation_settings["avoid_jargon"] = True
                        changes.append(f"adapted_language_to_{adaptation_value}")
                    
                    elif adaptation_type == "response_length":
                        if adaptation_value == "concise":
                            self._adaptation_settings["prefer_concise"] = True
                        elif adaptation_value == "detailed":
                            self._adaptation_settings["include_details"] = True
                        changes.append(f"adapted_length_to_{adaptation_value}")
                    
                    elif adaptation_type == "content_focus":
                        if adaptation_value == "practical":
                            self._adaptation_settings["practical_focus"] = True
                        changes.append(f"adapted_focus_to_{adaptation_value}")
                    
                    elif adaptation_type == "response_style":
                        if not hasattr(self, '_response_style'):
                            self._response_style = {}
                        self._response_style[adaptation_value] = True
                        changes.append(f"updated_style_{adaptation_value}")
        
        except Exception as e:
            self._logger.warning(f"语义反馈分析失败，使用基础处理: {e}")
            # 降级到简单处理
            changes = await self._basic_feedback_processing(feedback)
        
        return changes
    
    async def _analyze_feedback_semantically(self, feedback: str) -> Dict[str, Any]:
        """使用AI进行语义反馈分析"""
        try:
            # 寻找LLMCell进行分析
            llm_cell = None
            for cell in self.cells:
                if cell.__class__.__name__ == "LLMCell":
                    llm_cell = cell
                    break
            
            if not llm_cell:
                return {"success": False, "error": "没有可用的LLMCell进行分析"}
            
            # 构建分析提示
            analysis_prompt = f"""
请分析以下反馈内容，识别需要的适应性调整。

反馈内容："{feedback}"

请识别以下适应需求并返回JSON格式：
{{
    "adaptations": [
        {{
            "type": "language_complexity", // simple, technical, normal
            "value": "simple/technical/normal",
            "confidence": 0.8
        }},
        {{
            "type": "response_length", // concise, detailed, normal  
            "value": "concise/detailed/normal",
            "confidence": 0.9
        }},
        {{
            "type": "content_focus", // practical, theoretical, balanced
            "value": "practical/theoretical/balanced", 
            "confidence": 0.7
        }}
    ]
}}

注意：只返回JSON，不要其他解释。
"""
            
            # 调用LLMCell进行分析
            result = llm_cell.process({"input": analysis_prompt})
            
            if result.get("success", False):
                response = result.get("response", "")
                try:
                    # 解析JSON响应
                    import json
                    import re
                    
                    # 提取JSON部分
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        analysis_data = json.loads(json_str)
                        return {"success": True, "data": analysis_data}
                    else:
                        return {"success": False, "error": "无法解析分析结果"}
                        
                except Exception as e:
                    return {"success": False, "error": f"JSON解析失败: {e}"}
            else:
                return {"success": False, "error": "LLM分析失败"}
                
        except Exception as e:
            return {"success": False, "error": f"语义分析异常: {e}"}
    
    async def _basic_feedback_processing(self, feedback: str) -> List[str]:
        """基础反馈处理（降级方案）"""
        changes = []
        feedback_lower = feedback.lower()
        
        # 最基本的语义线索，但尽量减少硬编码
        if "简" in feedback_lower or "短" in feedback_lower or "长" in feedback_lower:
            self._adaptation_settings["prefer_concise"] = True
            changes.append("basic_length_adaptation")
        
        if "专业" in feedback_lower or "技术" in feedback_lower:
            self._adaptation_settings["language_level"] = "technical"
            changes.append("basic_technical_adaptation")
        elif "通俗" in feedback_lower or "普通" in feedback_lower:
            self._adaptation_settings["language_level"] = "simple" 
            changes.append("basic_simple_adaptation")
        
        return changes
    
    def _store_learning_content(self, feedback: str, analysis: Dict[str, Any], context: Dict[str, Any]):
        """将学习内容存储到记忆系统"""
        try:
            # 寻找StateMemoryCell
            memory_cell = None
            for cell in self.cells:
                if cell.__class__.__name__ == "StateMemoryCell":
                    memory_cell = cell
                    break
            
            if memory_cell:
                # 构建学习内容
                learning_content = f"反馈学习: {feedback}\n分析: {analysis['reason']}\n类型: {analysis['type']}"
                
                # 存储到记忆系统
                memory_cell.store(
                    content=learning_content,
                    metadata={"type": "feedback_learning", "feedback_type": analysis["type"]},
                    context=f"学习反馈: {analysis['type']}"
                )
                
                self._logger.debug(f"反馈学习内容已存储到记忆系统")
        except Exception as e:
            self._logger.warning(f"学习内容存储失败: {e}")
    
    def update_configuration(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新生命体配置 - Level 6学习反馈能力
        
        Args:
            updates: 配置更新项
            
        Returns:
            Dict包含更新结果
        """
        try:
            self._logger.info(f"生命体 {self.dna.name} 更新配置: {list(updates.keys())}")
            
            applied_updates = []
            
            for key, value in updates.items():
                try:
                    if key == "response_style":
                        if not hasattr(self, '_response_style'):
                            self._response_style = {}
                        self._response_style.update(value)
                        applied_updates.append(key)
                    
                    elif key == "learning_preferences":
                        if not hasattr(self, '_learning_preferences'):
                            self._learning_preferences = {}
                        self._learning_preferences.update(value)
                        applied_updates.append(key)
                    
                    elif key == "behavior_adjustments":
                        if not hasattr(self, '_behavior_adjustments'):
                            self._behavior_adjustments = {}
                        self._behavior_adjustments.update(value)
                        applied_updates.append(key)
                    
                    else:
                        # 通用配置更新
                        setattr(self, f"_{key}", value)
                        applied_updates.append(key)
                
                except Exception as e:
                    self._logger.warning(f"配置项 {key} 更新失败: {e}")
            
            return {
                "success": True,
                "applied_updates": applied_updates,
                "total_requested": len(updates),
                "total_applied": len(applied_updates)
            }
            
        except Exception as e:
            self._logger.error(f"配置更新失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "applied_updates": []
            }
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        learning_history = getattr(self, '_learning_history', [])
        
        if not learning_history:
            return {
                "total_learning_events": 0,
                "absorbed_feedback_count": 0,
                "ignored_feedback_count": 0,
                "learning_efficiency": 0.0
            }
        
        absorbed_count = sum(1 for event in learning_history if event.get("action") == "absorb")
        ignored_count = sum(1 for event in learning_history if event.get("action") == "ignore")
        
        return {
            "total_learning_events": len(learning_history),
            "absorbed_feedback_count": absorbed_count,
            "ignored_feedback_count": ignored_count,
            "learning_efficiency": absorbed_count / len(learning_history) if learning_history else 0.0,
            "has_learning_capability": True
        }
    
    def _apply_learning_improvements(self, input_data: str, context: str) -> str:
        """应用学习到的改进指导来增强输入"""
        try:
            enhanced_input = input_data
            
            # 应用适应性设置（关键修复：让适应性产生实际效果）
            adaptation_settings = getattr(self, '_adaptation_settings', {})
            if adaptation_settings:
                adaptation_instructions = []
                
                # 语言复杂度适应
                if adaptation_settings.get("language_level") == "simple":
                    adaptation_instructions.append("使用简单易懂的语言，避免专业术语，面向普通用户")
                elif adaptation_settings.get("language_level") == "technical":
                    adaptation_instructions.append("使用专业技术语言，提供详细深入的说明")
                
                # 长度偏好适应
                if adaptation_settings.get("prefer_concise"):
                    adaptation_instructions.append("保持回答简洁明了，控制在200字以内")
                elif adaptation_settings.get("include_details"):
                    adaptation_instructions.append("提供详细完整的说明，包含具体细节和例子")
                
                # 避免行话适应
                if adaptation_settings.get("avoid_jargon"):
                    adaptation_instructions.append("避免使用技术行话，用通俗的话解释概念")
                
                # 实用性导向适应
                if adaptation_settings.get("practical_focus"):
                    adaptation_instructions.append("重点提供实用的方法和具体可操作的建议")
                
                if adaptation_instructions:
                    enhanced_input = f"{input_data}\n\n[重要适应指示：{' 同时 '.join(adaptation_instructions)}]"
            
            # 应用改进指导
            improvement_guidelines = getattr(self, '_improvement_guidelines', [])
            if improvement_guidelines:
                # 构建改进提示
                improvements = "\n".join([
                    f"改进指导{i+1}: {guideline}" 
                    for i, guideline in enumerate(improvement_guidelines[-3:])  # 使用最近3个指导
                ])
                
                enhanced_input = f"{enhanced_input}\n\n[应用以下改进指导:\n{improvements}]"
            
            # 应用正面模式强化
            positive_patterns = getattr(self, '_positive_patterns', [])
            if positive_patterns:
                # 从正面反馈中提取要强化的模式
                patterns_text = "继续保持专业、清晰的回答风格"
                enhanced_input = f"{enhanced_input}\n\n[保持优势: {patterns_text}]"
            
            return enhanced_input
            
        except Exception as e:
            self._logger.warning(f"应用学习改进失败: {e}")
            return input_data
    
    def _apply_response_improvements(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """应用学习到的响应风格改进"""
        try:
            if not result.get("success", False):
                return result
            
            response_data = result.get("data", {})
            if "response" not in response_data:
                return result
            
            original_response = response_data["response"]
            improved_response = original_response
            
            # 应用适应性设置后处理（关键修复：确保适应性在输出中体现）
            adaptation_settings = getattr(self, '_adaptation_settings', {})
            if adaptation_settings:
                # 长度控制适应
                if adaptation_settings.get("prefer_concise") and len(improved_response) > 200:
                    # 智能压缩：保留关键信息
                    sentences = improved_response.split('。')
                    if len(sentences) > 3:
                        improved_response = '。'.join(sentences[:3]) + '。'
                
                # 语言简化适应后处理
                if adaptation_settings.get("language_level") == "simple":
                    # 简单的术语替换
                    tech_terms = {
                        "算法": "方法",
                        "模型": "系统", 
                        "优化": "改进",
                        "参数": "设置",
                        "架构": "结构",
                        "实例": "例子"
                    }
                    for tech, simple in tech_terms.items():
                        improved_response = improved_response.replace(tech, simple)
                
                # 实用性增强
                if adaptation_settings.get("practical_focus"):
                    if not any(word in improved_response for word in ["步骤", "方法", "建议", "推荐"]):
                        improved_response += "\n\n具体建议：可以根据实际情况选择合适的方法。"
            
            # 应用响应风格配置
            response_style = getattr(self, '_response_style', {})
            
            if response_style.get("prefer_concise", False):
                # 如果学习到要简洁，尝试压缩响应
                if len(improved_response) > 300:
                    # 简单的压缩策略：保留前70%内容
                    improved_response = improved_response[:int(len(improved_response) * 0.7)] + "..."
            
            if response_style.get("include_examples", False):
                # 如果学习到要包含例子，添加例子提示
                if "例如" not in improved_response and "比如" not in improved_response:
                    improved_response += "\n\n[注：实际应用中应包含具体例子]"
            
            if response_style.get("use_structured_format", False):
                # 如果学习到要使用结构化格式，尝试添加结构
                if not any(marker in improved_response for marker in ["1.", "2.", "首先", "其次"]):
                    improved_response = f"总结如下：\n\n{improved_response}"
            
            # 应用行为调整
            behavior_adjustments = getattr(self, '_behavior_adjustments', {})
            if behavior_adjustments:
                # 应用学习到的行为调整
                for adjustment_type, adjustment_value in behavior_adjustments.items():
                    if adjustment_type == "tone" and adjustment_value == "more_friendly":
                        if not improved_response.endswith("！") and not improved_response.endswith("。"):
                            improved_response += "，希望对您有帮助！"
            
            # 更新结果
            response_data["response"] = improved_response
            result["data"] = response_data
            
            # 添加学习改进标记
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["learning_improvements_applied"] = True
            
            return result
            
        except Exception as e:
            self._logger.warning(f"应用响应改进失败: {e}")
            return result
    
    def _record_experience(self, input_data: str, context: str, result: Dict[str, Any]):
        """记录经验用于积累学习 - Level 6经验积累能力"""
        try:
            # 初始化经验历史
            if not hasattr(self, '_experience_history'):
                self._experience_history = []
            
            # 分析任务模式
            task_pattern = self._identify_task_pattern(input_data)
            
            # 计算响应质量
            response_quality = self._assess_experience_quality(result, input_data)
            
            # 记录经验
            experience_record = {
                "timestamp": self._get_timestamp(),
                "task_pattern": task_pattern,
                "input": input_data[:100] + "..." if len(input_data) > 100 else input_data,
                "context": context,
                "response_quality": response_quality,
                "response_length": len(result.get("data", {}).get("response", "")),
                "success": result.get("success", False)
            }
            
            self._experience_history.append(experience_record)
            
            # 保持经验历史在合理范围内
            if len(self._experience_history) > 100:
                self._experience_history = self._experience_history[-100:]
            
            # 检查是否有类似经验可以参考
            self._apply_similar_experience(task_pattern)
            
        except Exception as e:
            self._logger.warning(f"经验记录失败: {e}")
    
    def _identify_task_pattern(self, input_data: str) -> str:
        """识别任务模式"""
        input_lower = input_data.lower()
        
        # 分析任务模式
        if any(word in input_lower for word in ["分析", "analysis", "evaluate", "assess"]):
            return "analysis"
        elif any(word in input_lower for word in ["解释", "explain", "什么是", "介绍"]):
            return "explanation"
        elif any(word in input_lower for word in ["计划", "plan", "步骤", "方法"]):
            return "planning"
        elif any(word in input_lower for word in ["比较", "对比", "优缺点", "差异"]):
            return "comparison"
        elif any(word in input_lower for word in ["学习", "如何", "怎么", "教程"]):
            return "learning_guidance"
        else:
            return "general"
    
    def _assess_experience_quality(self, result: Dict[str, Any], input_data: str) -> float:
        """评估经验质量"""
        if not result.get("success", False):
            return 0.0
        
        response = result.get("data", {}).get("response", "")
        if not response:
            return 0.0
        
        quality_score = 0.0
        
        # 基础质量指标
        if len(response) > 50:
            quality_score += 0.2
        
        if len(response.split()) > 20:
            quality_score += 0.2
        
        # 结构化指标
        structure_indicators = ["1.", "2.", "首先", "其次", "最后", "总之"]
        if any(indicator in response for indicator in structure_indicators):
            quality_score += 0.2
        
        # 专业性指标
        professional_words = ["分析", "优点", "缺点", "优势", "劣势", "特点", "原理"]
        if any(word in response for word in professional_words):
            quality_score += 0.2
        
        # 具体性指标
        specific_indicators = ["例如", "比如", "具体", "详细", "步骤"]
        if any(indicator in response for indicator in specific_indicators):
            quality_score += 0.2
        
        return min(quality_score, 1.0)
    
    def _apply_similar_experience(self, task_pattern: str):
        """应用类似经验 - 经验积累机制"""
        try:
            experience_history = getattr(self, '_experience_history', [])
            if len(experience_history) < 2:
                return
            
            # 找到相同模式的历史经验
            similar_experiences = [
                exp for exp in experience_history[:-1]  # 排除当前记录
                if exp.get("task_pattern") == task_pattern and exp.get("success", False)
            ]
            
            if len(similar_experiences) >= 2:
                # 分析经验趋势
                recent_quality = sum(exp.get("response_quality", 0) for exp in similar_experiences[-3:]) / min(3, len(similar_experiences))
                
                # 如果有经验积累，记录学习到的模式
                if not hasattr(self, '_task_patterns'):
                    self._task_patterns = {}
                
                if task_pattern not in self._task_patterns:
                    self._task_patterns[task_pattern] = {
                        "count": 0,
                        "avg_quality": 0.0,
                        "best_practices": []
                    }
                
                pattern_data = self._task_patterns[task_pattern]
                pattern_data["count"] += 1
                pattern_data["avg_quality"] = (pattern_data["avg_quality"] * (pattern_data["count"] - 1) + recent_quality) / pattern_data["count"]
                
                # 记录最佳实践
                best_experience = max(similar_experiences, key=lambda x: x.get("response_quality", 0))
                if best_experience.get("response_quality", 0) > 0.8:
                    practice_summary = f"在{task_pattern}任务中保持高质量表现"
                    if practice_summary not in pattern_data["best_practices"]:
                        pattern_data["best_practices"].append(practice_summary)
                
        except Exception as e:
            self._logger.warning(f"应用类似经验失败: {e}")
    
    def get_experience_stats(self) -> Dict[str, Any]:
        """获取经验积累统计"""
        experience_history = getattr(self, '_experience_history', [])
        task_patterns = getattr(self, '_task_patterns', {})
        
        if not experience_history:
            return {
                "total_experiences": 0,
                "task_patterns_learned": 0,
                "experience_quality_trend": 0.0
            }
        
        # 计算质量趋势
        if len(experience_history) >= 5:
            early_quality = sum(exp.get("response_quality", 0) for exp in experience_history[:3]) / 3
            recent_quality = sum(exp.get("response_quality", 0) for exp in experience_history[-3:]) / 3
            quality_trend = recent_quality - early_quality
        else:
            quality_trend = 0.0
        
        return {
            "total_experiences": len(experience_history),
            "task_patterns_learned": len(task_patterns),
            "experience_quality_trend": quality_trend,
            "avg_response_quality": sum(exp.get("response_quality", 0) for exp in experience_history) / len(experience_history),
            "has_experience_accumulation": True
        }
    
    async def adapt_to_context(self, context_change: str, task: str = None) -> Dict[str, Any]:
        """
        适应性调整能力 - Level 6适应性调整
        
        Args:
            context_change: 环境变化描述
            task: 可选的测试任务
            
        Returns:
            Dict包含适应结果
        """
        try:
            self._logger.info(f"生命体 {self.dna.name} 适应环境变化: {context_change}")
            
            # 初始化适应历史
            if not hasattr(self, '_adaptation_history'):
                self._adaptation_history = []
            
            # 分析环境变化类型
            adaptation_analysis = self._analyze_context_change(context_change)
            
            # 应用适应性调整
            adaptation_result = self._apply_contextual_adaptation(adaptation_analysis)
            
            # 记录适应事件
            adaptation_event = {
                "timestamp": self._get_timestamp(),
                "context_change": context_change,
                "analysis": adaptation_analysis,
                "adjustments_made": adaptation_result.get("adjustments", []),
                "task": task
            }
            
            self._adaptation_history.append(adaptation_event)
            
            # 保持适应历史在合理范围内
            if len(self._adaptation_history) > 30:
                self._adaptation_history = self._adaptation_history[-30:]
            
            return {
                "success": True,
                "data": {
                    "adapted": adaptation_result.get("adapted", False),
                    "adjustments_applied": adaptation_result.get("adjustments", []),
                    "analysis": adaptation_analysis
                },
                "metadata": {
                    "adapter": self.dna.name,
                    "adaptation_mode": "contextual_adjustment"
                }
            }
            
        except Exception as e:
            self._logger.error(f"适应性调整失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"adapted": False}
            }
    
    def _analyze_context_change(self, context_change: str) -> Dict[str, Any]:
        """分析环境变化类型"""
        change_lower = context_change.lower()
        
        # 用户群体变化
        if any(word in change_lower for word in ["专家", "普通用户", "技术", "非技术"]):
            if "普通用户" in change_lower or "非技术" in change_lower:
                return {
                    "type": "audience_simplification",
                    "adjustment": "simplify_language",
                    "confidence": 0.9
                }
            else:
                return {
                    "type": "audience_technical",
                    "adjustment": "increase_technical_depth",
                    "confidence": 0.8
                }
        
        # 回答风格变化
        elif any(word in change_lower for word in ["详细", "简洁", "长", "短"]):
            if "简洁" in change_lower or "短" in change_lower:
                return {
                    "type": "style_concise",
                    "adjustment": "prefer_brevity",
                    "confidence": 0.9
                }
            else:
                return {
                    "type": "style_detailed",
                    "adjustment": "increase_detail",
                    "confidence": 0.8
                }
        
        # 实用性导向变化
        elif any(word in change_lower for word in ["实用", "具体", "方法", "步骤"]):
            return {
                "type": "practicality_focus",
                "adjustment": "increase_practicality",
                "confidence": 0.8
            }
        
        else:
            return {
                "type": "general_adaptation",
                "adjustment": "general_improvement",
                "confidence": 0.5
            }
    
    def _apply_contextual_adaptation(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """应用上下文适应"""
        adjustments = []
        adapted = False
        
        adjustment_type = analysis.get("adjustment")
        
        try:
            if adjustment_type == "simplify_language":
                # 简化语言表达
                if not hasattr(self, '_adaptation_settings'):
                    self._adaptation_settings = {}
                self._adaptation_settings["language_level"] = "simple"
                self._adaptation_settings["avoid_jargon"] = True
                adjustments.extend(["simplified_language", "avoid_technical_terms"])
                adapted = True
            
            elif adjustment_type == "prefer_brevity":
                # 偏好简洁
                if not hasattr(self, '_response_style'):
                    self._response_style = {}
                self._response_style["prefer_concise"] = True
                self._response_style["max_length"] = 200
                adjustments.extend(["enabled_concise_mode", "set_length_limit"])
                adapted = True
            
            elif adjustment_type == "increase_practicality":
                # 增加实用性
                if not hasattr(self, '_response_style'):
                    self._response_style = {}
                self._response_style["include_examples"] = True
                self._response_style["focus_on_action"] = True
                adjustments.extend(["enabled_examples", "action_oriented"])
                adapted = True
            
            elif adjustment_type == "increase_technical_depth":
                # 增加技术深度
                if not hasattr(self, '_adaptation_settings'):
                    self._adaptation_settings = {}
                self._adaptation_settings["language_level"] = "technical"
                self._adaptation_settings["include_details"] = True
                adjustments.extend(["technical_language", "detailed_explanations"])
                adapted = True
            
            return {
                "adapted": adapted,
                "adjustments": adjustments
            }
            
        except Exception as e:
            self._logger.warning(f"上下文适应应用失败: {e}")
            return {
                "adapted": False,
                "adjustments": [],
                "error": str(e)
            }
    
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """获取适应性统计"""
        adaptation_history = getattr(self, '_adaptation_history', [])
        
        if not adaptation_history:
            return {
                "total_adaptations": 0,
                "successful_adaptations": 0,
                "adaptation_success_rate": 0.0
            }
        
        successful_adaptations = sum(
            1 for event in adaptation_history 
            if len(event.get("adjustments_made", [])) > 0
        )
        
        return {
            "total_adaptations": len(adaptation_history),
            "successful_adaptations": successful_adaptations,
            "adaptation_success_rate": successful_adaptations / len(adaptation_history),
            "has_adaptation_capability": True
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"AILifeForm({self.dna.name} v{self.dna.version}, gen{self.generation})"


class LifeGrower:
    """AI生命体培养器 - 从DNA配置生成完整的AI智能体"""
    
    def __init__(self):
        """初始化培养器"""
        self.factory = DNACellFactory()
        self._logger = logging.getLogger("LifeGrower")
        
        # 培养统计
        self.grown_count = 0
        self.success_rate = 0.0
        
        # 🧪 新增：自主生长引擎
        self.autonomous_engine: Optional[AutonomousGrowthEngine] = None
        self._initialize_autonomous_growth()
        
        # 🎯 新增：数字生命名片管理
        self.life_cards: Dict[str, DigitalLifeCard] = {}
    
    def _initialize_autonomous_growth(self):
        """初始化自主生长引擎"""
        try:
            self.autonomous_engine = AutonomousGrowthEngine()
            self._logger.info("自主生长引擎初始化成功")
        except Exception as e:
            self._logger.warning(f"自主生长引擎初始化失败: {e}")
    
    def grow_from_dna(self, dna: EmbryoDNA) -> AILifeForm:
        """
        从DNA培养AI生命体
        
        Args:
            dna: DNA配置
            
        Returns:
            培养出的AI生命体
            
        Raises:
            LifeGrowthError: 培养失败
        """
        try:
            self._logger.info(f"开始培养AI生命体: {dna.name}")
            
            # 验证DNA
            dna.validate()
            
            # 阶段1: 创建Cell组件
            cells = self._create_cells_from_dna(dna)
            self._logger.info(f"创建了 {len(cells)} 个Cell组件")
            
            # 阶段2: 构建组织结构
            pipeline = self._create_pipeline_from_dna(dna, cells)
            if pipeline:
                self._logger.info(f"构建了 {dna.structure.architecture} 架构的Pipeline")
            
            # 阶段3: 组装生命体
            life_form = AILifeForm(dna, cells, pipeline)
            
            # 阶段4: 生命体初始化
            self._initialize_life_form(life_form)
            
            self.grown_count += 1
            self._logger.info(f"AI生命体 {dna.name} 培养成功!")
            
            return life_form
            
        except Exception as e:
            self._logger.error(f"AI生命体培养失败: {e}")
            raise LifeGrowthError(f"培养失败: {e}")
    
    def grow_from_file(self, dna_file_path: Union[str, Path]) -> AILifeForm:
        """
        从DNA文件培养AI生命体
        
        Args:
            dna_file_path: DNA配置文件路径
            
        Returns:
            培养出的AI生命体
        """
        dna = EmbryoDNA.from_file(dna_file_path)
        return self.grow_from_dna(dna)
    
    def _create_cells_from_dna(self, dna: EmbryoDNA) -> List[Cell]:
        """根据DNA创建Cell组件"""
        cells = []
        
        # 根据capability基因创建Cell
        for skill in dna.capability.skills:
            cell = self._create_skill_cell(skill, dna)
            if cell:
                cells.append(cell)
        
        # 根据structure基因创建指定的Cell类型
        for cell_type in dna.structure.cell_types:
            cell = self._create_typed_cell(cell_type, dna)
            if cell:
                cells.append(cell)
        
        # 去重（同类型Cell只保留一个）
        unique_cells = []
        seen_types = set()
        for cell in cells:
            cell_type = type(cell).__name__
            if cell_type not in seen_types:
                unique_cells.append(cell)
                seen_types.add(cell_type)
        
        return unique_cells
    
    def _create_skill_cell(self, skill: str, dna: EmbryoDNA) -> Optional[Cell]:
        """根据技能创建对应的Cell"""
        skill_cell_mapping = {
            "chat": self._create_chat_cell,
            "knowledge": self._create_knowledge_cell,
            "analyze": self._create_analyze_cell,
            "generate": self._create_generate_cell,
            "search": self._create_search_cell,
            "tool_use": self._create_tool_cell
        }
        
        creator = skill_cell_mapping.get(skill)
        if creator:
            return creator(dna)
        else:
            self._logger.warning(f"未知技能类型: {skill}")
            return None
    
    def _create_typed_cell(self, cell_type: str, dna: EmbryoDNA) -> Optional[Cell]:
        """根据指定类型创建Cell"""
        if cell_type == "LLMCell":
            return self._create_llm_cell(dna)
        elif cell_type == "StateMemoryCell":
            return self._create_memory_cell(dna)
        elif cell_type == "MindCell":
            return self._create_mind_cell(dna)
        elif cell_type == "ToolCell":
            return self._create_tool_cell(dna)
        else:
            self._logger.warning(f"未知Cell类型: {cell_type}")
            return None
    
    def _create_chat_cell(self, dna: EmbryoDNA) -> LLMCell:
        """创建对话Cell"""
        behavior = dna.behavior
        
        # 使用DNA的系统提示词
        system_prompt = behavior.system_prompt or behavior._generate_default_system_prompt()
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config={
                "system_prompt": system_prompt,
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
    
    def _create_knowledge_cell(self, dna: EmbryoDNA) -> StateMemoryCell:
        """创建知识Cell"""
        # 使用DNACellFactory来创建，确保配置一致
        return self.factory.create_cell("StateMemoryCell", dna)
    
    def _create_analyze_cell(self, dna: EmbryoDNA) -> LLMCell:
        """创建分析Cell"""
        analyze_prompt = f"""你是{dna.name}的分析专家，专门负责深度分析和洞察。

核心能力：
- 数据分析和模式识别
- 逻辑推理和因果分析  
- 趋势预测和建议生成

请以{dna.behavior.style}的风格进行分析，使用{dna.behavior.language}回答。"""
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config={
                "system_prompt": analyze_prompt,
                "temperature": 0.3,  # 分析需要更稳定
                "max_tokens": 3000
            }
        )
    
    def _create_generate_cell(self, dna: EmbryoDNA) -> LLMCell:
        """创建生成Cell"""
        generate_prompt = f"""你是{dna.name}的创意生成专家，专门负责内容创作。

核心能力：
- 创意文案生成
- 结构化内容创作
- 多格式内容适配

风格特点：{', '.join(dna.behavior.personality)}
请以{dna.behavior.style}的风格创作，使用{dna.behavior.language}。"""
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config={
                "system_prompt": generate_prompt,
                "temperature": 0.8,  # 生成需要更多创造性
                "max_tokens": 2500
            }
        )
    
    def _create_search_cell(self, dna: EmbryoDNA) -> LLMCell:
        """创建搜索Cell（暂时用LLMCell模拟）"""
        search_prompt = f"""你是{dna.name}的信息搜索专家，专门负责信息检索和整理。

核心能力：
- 信息搜索和过滤
- 结果排序和筛选
- 摘要生成和提取

请以{dna.behavior.style}的风格整理信息，使用{dna.behavior.language}。"""
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config={
                "system_prompt": search_prompt,
                "temperature": 0.2,  # 搜索需要精确性
                "max_tokens": 2000
            }
        )
    
    def _create_tool_cell(self, dna: EmbryoDNA) -> LLMCell:
        """创建工具Cell（暂时用LLMCell模拟）"""
        tool_prompt = f"""你是{dna.name}的工具调用专家，专门负责工具集成和调用。

核心能力：
- 工具选择和调用
- 参数构建和验证
- 结果解析和整合

可用工具：{', '.join(dna.capability.tools)}
请以{dna.behavior.style}的风格使用工具，用{dna.behavior.language}解释结果。"""
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config={
                "system_prompt": tool_prompt,
                "temperature": 0.1,  # 工具调用需要精确性
                "max_tokens": 1500
            }
        )
    
    def _create_llm_cell(self, dna: EmbryoDNA, tool_cell=None) -> LLMCell:
        """创建通用LLMCell"""
        behavior = dna.behavior
        system_prompt = behavior.system_prompt or behavior._generate_default_system_prompt()
        
        # 如果有工具Cell，启用Function Calling
        config = {
            "system_prompt": system_prompt,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        if tool_cell:
            config.update({
                "enable_tools": True,
                "tool_choice": "auto",
                "max_tool_calls": 5
            })
            self._logger.info("LLMCell配置了Function Calling支持")
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config=config,
            tool_cell=tool_cell
        )
    
    def _create_memory_cell(self, dna: EmbryoDNA) -> StateMemoryCell:
        """创建记忆Cell"""
        # 使用DNACellFactory来创建，确保配置一致
        return self.factory.create_cell("StateMemoryCell", dna)
    
    def _create_mind_cell(self, dna: EmbryoDNA) -> 'MindCell':
        """创建思维Cell"""
        from ..cells import MindCell
        from ..core.config import get_api_key, get_api_base_url
        
        behavior = dna.behavior
        system_prompt = behavior.system_prompt or behavior._generate_default_system_prompt()
        
        return MindCell(
            config={
                "model_name": dna.capability.models.get("llm", "gpt-3.5-turbo"),
                "system_prompt": system_prompt,
                "temperature": 0.3,  # 思维Cell使用较低的温度，更注重逻辑
                "max_tokens": 3000,  # 更多token支持复杂思维过程
                "api_key": dna.capability.models.get("api_key") or get_api_key("openai"),
                "base_url": dna.capability.models.get("base_url") or get_api_base_url("openai"),
                "thinking_mode": "chain_of_thought",
                "attention_enabled": True,
                "feedback_enabled": True
            }
        )
    
    def _create_tool_cell(self, dna: EmbryoDNA) -> 'ToolCell':
        """创建工具Cell"""
        from ..cells import ToolCell
        
        # 基础工具配置
        tool_config = {
            "auto_load_defaults": True,  # 自动加载默认工具（add, multiply, text_length, text_upper）
            "tools": [],  # 自定义工具列表
            "mcp_servers": []  # MCP服务器配置
        }
        
        # 从DNA capability中获取工具配置
        if hasattr(dna.capability, 'tools') and dna.capability.tools:
            for tool_name in dna.capability.tools:
                if tool_name not in ["default", "auto"]:
                    tool_config["tools"].append({
                        "name": tool_name,
                        "description": f"DNA配置的工具: {tool_name}",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    })
        
        # 从DNA extension中获取MCP服务器配置
        if hasattr(dna, 'extension') and dna.extension:
            mcp_config = dna.extension.get("mcp_servers", [])
            tool_config["mcp_servers"] = mcp_config
        
        self._logger.info(f"创建ToolCell - 自动加载默认工具: {tool_config['auto_load_defaults']}")
        self._logger.info(f"工具配置: {len(tool_config['tools'])}个自定义工具, {len(tool_config['mcp_servers'])}个MCP服务器")
        
        return ToolCell(config=tool_config)
    
    def _create_pipeline_from_dna(self, dna: EmbryoDNA, cells: List[Cell]) -> Optional[Pipeline]:
        """根据DNA和Cell列表创建Pipeline"""
        if len(cells) <= 1:
            # 单个Cell不需要Pipeline
            return None
        
        architecture = dna.structure.architecture
        
        if architecture == "pipeline":
            # 顺序Pipeline
            return Pipeline(
                steps=cells,
                config={"execution_mode": "sequential"}
            )
        elif architecture == "parallel":
            # 并行架构
            return Pipeline(
                steps=cells,
                config={"execution_mode": "parallel"}
            )
        else:
            # 其他架构使用默认顺序模式
            self._logger.warning(f"暂不支持的架构: {architecture}，使用默认顺序模式")
            return Pipeline(
                steps=cells,
                config={"execution_mode": "sequential"}
            )
    
    def _initialize_life_form(self, life_form: AILifeForm):
        """初始化生命体"""
        import time
        
        # 设置出生时间
        life_form.birth_time = time.time()
        
        # 初始化适应度分数
        life_form.fitness_score = 1.0
        
        # 🎯 新增：生成数字生命名片
        life_card = DigitalLifeCard(life_form)
        life_form.life_card_data = life_card.generate_card()
        self.life_cards[life_form.dna.name] = life_card
        
        # 记录日志
        self._logger.info(f"生命体 {life_form.dna.name} 初始化完成，数字生命名片已生成")
    
    def get_growth_stats(self) -> Dict[str, Any]:
        """获取培养统计"""
        return {
            "grown_count": self.grown_count,
            "success_rate": self.success_rate,
            "supported_skills": ["chat", "knowledge", "analyze", "generate", "search", "tool_use"],
            "supported_architectures": ["pipeline", "parallel"],
            "supported_cell_types": ["LLMCell", "StateMemoryCell"]
        }
    
    async def grow_life_form(self, dna: EmbryoDNA) -> AILifeForm:
        """异步培养生命体"""
        return self.grow_from_dna(dna)
    
    # 🧪 自主生长核心方法
    
    async def grow_from_natural_language(self, goal_description: str, 
                                       context: Dict[str, Any] = None,
                                       constraints: Dict[str, Any] = None,
                                       auto_instantiate: bool = True) -> Dict[str, Any]:
        """
        从自然语言描述自主生长数字生命体
        
        Args:
            goal_description: 自然语言目标描述
            context: 上下文信息
            constraints: 生长约束
            auto_instantiate: 是否自动实例化生命体
            
        Returns:
            Dict: 生长结果，包含DNA、生命体实例等
        """
        if not self.autonomous_engine:
            raise LifeGrowthError("自主生长引擎未初始化")
        
        self._logger.info(f"开始自然语言生长: {goal_description[:50]}...")
        
        try:
            # 使用自主生长引擎生成DNA配置
            growth_result = await self.autonomous_engine.grow_life_form_from_goal(
                goal_description, context, constraints
            )
            
            if not growth_result["success"]:
                return {
                    "success": False,
                    "error": growth_result["error"],
                    "metadata": growth_result["metadata"]
                }
            
            dna_config = growth_result["dna_config"]
            
            # 创建EmbryoDNA实例
            dna = await self._create_embryo_dna_from_config(dna_config)
            
            result = {
                "success": True,
                "dna": dna,
                "dna_config": dna_config,
                "growth_metadata": growth_result["metadata"]
            }
            
            # 可选：自动实例化生命体
            if auto_instantiate:
                try:
                    life_form = self.grow_from_dna(dna)
                    result["life_form"] = life_form
                    result["life_card"] = life_form.life_card_data
                    
                    self._logger.info(f"自然语言生长成功并实例化: {dna.name}")
                except Exception as e:
                    self._logger.warning(f"生命体实例化失败: {e}")
                    result["instantiation_error"] = str(e)
            
            return result
            
        except Exception as e:
            self._logger.error(f"自然语言生长失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {"error_stage": "autonomous_growth"}
            }
    
    async def _create_embryo_dna_from_config(self, config: Dict[str, Any]) -> EmbryoDNA:
        """从配置字典创建EmbryoDNA实例"""
        from .genes import PurposeGene, CapabilityGene, StructureGene, BehaviorGene, EvolutionGene
        
        # 创建各个基因
        purpose = PurposeGene(
            goal=config["purpose"]["goal"],
            metrics=config["purpose"].get("metrics", []),
            constraints=config["purpose"].get("constraints", [])
        )
        
        capability = CapabilityGene(
            skills=config["capability"]["skills"],
            models=config["capability"]["models"],
            tools=config["capability"].get("tools", [])
        )
        
        structure = StructureGene(
            cell_types=config["structure"]["cell_types"],
            architecture=config["structure"]["architecture"],
            max_complexity=config["structure"].get("max_complexity", 5),
            auto_scale=config["structure"].get("auto_scale", False)
        )
        
        behavior = BehaviorGene(
            personality=config["behavior"]["personality"],
            style=config["behavior"]["style"],
            language=config["behavior"]["language"],
            safety=config["behavior"]["safety"],
            system_prompt=config["behavior"].get("system_prompt")
        )
        
        evolution = EvolutionGene(
            enabled=config["evolution"]["enabled"],
            learn_rate=config["evolution"]["learn_rate"],
            adapt_speed=config["evolution"]["adapt_speed"],
            mutation_rate=config["evolution"]["mutation_rate"],
            fitness_focus=config["evolution"]["fitness_focus"]
        )
        
        # 创建EmbryoDNA实例
        dna = EmbryoDNA(
            name=config["name"],
            version=config["version"],
            description=config["description"],
            purpose=purpose,
            capability=capability,
            structure=structure,
            behavior=behavior,
            evolution=evolution
        )
        
        # 添加生命元素配置（如果存在）
        if "life_elements" in config:
            dna._life_elements_config = config["life_elements"]
        
        return dna
    
    async def learn_from_usage_feedback(self, life_form_name: str, 
                                      feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        从使用反馈中学习，优化未来的生长
        
        Args:
            life_form_name: 生命体名称
            feedback: 用户反馈
            
        Returns:
            Dict: 学习结果
        """
        if not self.autonomous_engine:
            return {"learned": False, "reason": "自主生长引擎未初始化"}
        
        # 查找对应的生长事件
        growth_history = self.autonomous_engine.get_recent_growth_history()
        target_growth = None
        
        for event in growth_history:
            if life_form_name in event.get("goal", ""):
                target_growth = event
                break
        
        if target_growth:
            growth_id = target_growth["growth_id"]
            return await self.autonomous_engine.learn_from_feedback(growth_id, feedback)
        else:
            return {"learned": False, "reason": "未找到对应的生长事件"}
    
    def get_life_card(self, life_form_name: str) -> Optional[Dict[str, Any]]:
        """获取生命体的数字名片"""
        life_card = self.life_cards.get(life_form_name)
        if life_card:
            return life_card.generate_card()
        return None
    
    def export_life_card(self, life_form_name: str, format: str = "json") -> Optional[str]:
        """导出生命体名片"""
        life_card = self.life_cards.get(life_form_name)
        if life_card:
            if format.lower() == "json":
                return life_card.to_json()
            elif format.lower() == "markdown":
                return life_card.to_markdown()
        return None
    
    def get_autonomous_growth_suggestions(self) -> List[str]:
        """获取自主生长优化建议"""
        if self.autonomous_engine:
            return self.autonomous_engine.get_optimization_suggestions()
        return []
    
    async def create_dna_from_template(self, config: Dict[str, Any]) -> EmbryoDNA:
        """从模板配置创建DNA（简化演示用）"""
        from .genes import PurposeGene, CapabilityGene, StructureGene, BehaviorGene, EvolutionGene
        
        # 创建基础DNA结构
        dna = EmbryoDNA(
            name=config["name"],
            version="1.0.0",
            description=f"从模板创建的{config['name']}生命体",
            purpose=PurposeGene(
                goal=f"提供{config['name']}相关的智能服务",
                metrics=["用户满意度 > 0.8"],
                constraints=["保持专业", "确保安全"]
            ),
            capability=CapabilityGene(
                skills=config["skills"],
                models={"llm": "gpt-3.5-turbo", "embed": "text-embedding-3-large"},
                tools=["basic_tools"]
            ),
            structure=StructureGene(
                cell_types=["LLMCell"],
                architecture="pipeline",
                max_complexity=3,
                auto_scale=False
            ),
            behavior=BehaviorGene(
                personality=["helpful", "professional"],
                style=config["style"],
                language="zh-CN",
                safety={"content_filter": True},
                system_prompt=f"你是一个专业的{config['name']}助手。"
            ),
            evolution=EvolutionGene(
                enabled=False,
                learn_rate=0.3,
                adapt_speed="normal",
                mutation_rate=0.05,
                fitness_focus=["accuracy"]
            )
        )
        
        return dna
    
    def get_supported_skills(self) -> List[str]:
        """获取支持的技能列表"""
        return ["chat", "knowledge", "analyze", "generate", "search", "tool_use"]
    
    def get_supported_cell_types(self) -> List[str]:
        """获取支持的Cell类型列表"""
        return ["LLMCell", "StateMemoryCell", "MindCell"]
    
    def get_supported_architectures(self) -> List[str]:
        """获取支持的架构列表"""
        return ["pipeline", "parallel"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取培养器统计信息"""
        stats = {
            "total_growths": self.grown_count,
            "success_rate": self.success_rate,
            "supported_skills": self.get_supported_skills(),
            "supported_cell_types": self.get_supported_cell_types(),
            "supported_architectures": self.get_supported_architectures(),
            "life_cards_generated": len(self.life_cards)
        }
        
        # 添加自主生长详细统计
        if self.autonomous_engine:
            autonomous_stats = self.autonomous_engine.get_growth_statistics()
            stats.update({
                "autonomous_growth_enabled": True,
                "autonomous_total_growths": autonomous_stats.get("total_growths", 0),
                "autonomous_success_rate": autonomous_stats.get("success_rate", 0.0),
                "avg_growth_time": autonomous_stats.get("avg_growth_time", 0.0),
                "avg_quality_score": autonomous_stats.get("avg_quality_score", 0.0)
            })
        else:
            stats["autonomous_growth_enabled"] = False
        
        return stats
    
    # 🎯 数字生命名片相关方法
    
    def generate_life_card_for_existing(self, life_form: AILifeForm) -> Dict[str, Any]:
        """为现有生命体生成数字名片"""
        life_card = DigitalLifeCard(life_form)
        card_data = life_card.generate_card()
        
        # 缓存名片
        self.life_cards[life_form.dna.name] = life_card
        
        return card_data
    
    def update_life_card(self, life_form_name: str, life_form: AILifeForm):
        """更新生命体名片"""
        if life_form_name in self.life_cards:
            self.life_cards[life_form_name].invalidate_cache()
        
        # 重新生成名片
        self.generate_life_card_for_existing(life_form)
    
    def get_all_life_cards(self) -> Dict[str, Dict[str, Any]]:
        """获取所有生命体名片"""
        all_cards = {}
        for name, life_card in self.life_cards.items():
            all_cards[name] = life_card.generate_card()
        return all_cards 