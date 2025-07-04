"""
协调智能体 - 管理多Agent协作的智能协调员

负责任务分析、Agent选择、流程协调和结果整合
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from futurembryo.cells.llm_cell import LLMCell
from cells.user_memory_cell import UserMemoryCell
from cells.mention_processor_cell import MentionProcessorCell


class CoordinatorAgent:
    """智能协调员 - 管理多Agent协作"""
    
    def __init__(self, available_agents: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        初始化协调员
        
        Args:
            available_agents: 可用的Agent字典 {agent_id: agent_instance}
            config: 配置信息
        """
        self.available_agents = available_agents
        self.config = config or {}
        
        # 初始化LLM（用于任务分析和协调）
        llm_config = {
            "model": "anthropic/claude-sonnet-4-20250514",
            "temperature": 0.7,
            "max_tokens": 2000,
            "system_prompt": self._build_coordinator_prompt()
        }
        self.llm_cell = LLMCell(model_name=llm_config["model"], config=llm_config)
        
        # 用户记忆（共享）
        user_memory_config = config.get("user_memory", {})
        self.user_memory = UserMemoryCell(user_memory_config)
        
        # @引用处理（共享）
        mention_config = config.get("mention_system", {})
        self.mention_processor = MentionProcessorCell(mention_config)
        
        # 协调状态
        self.current_task = None
        self.task_history = []
        self.coordination_count = 0
    
    def _build_coordinator_prompt(self) -> str:
        """构建协调员系统提示词 - AI First动态发现和选择"""
        # 动态获取可用智能体的能力描述
        agent_capabilities = self._get_agent_capabilities()
        
        prompt = f"""你是一个智能协调员，负责分析用户任务并动态协调专业Agent完成工作。

## 核心能力：
你具备完全的AI智能，能够：
- 深度理解用户需求的复杂性和细节
- 智能分析任务所需的专业技能组合
- 动态发现最适合的Agent或Agent组合
- 自主制定最优的执行计划和协作流程
- 智能整合多个Agent的工作成果

## 当前可用的专业Agent能力：
{agent_capabilities}

## 工作原则：
- 深度分析任务本质，而非简单的关键词匹配
- 智能判断是否需要单个Agent还是多Agent协作
- 考虑Agent间的能力互补和协作效果
- 动态调整执行策略以确保最佳结果
- 持续学习和优化协调策略

## 重要限制：
- 只能选择上述列出的专业Agent，不能选择coordinator或其他不存在的Agent
- 所有选择的agent_id必须是实际可用的Agent ID

## 响应要求：
请提供结构化的JSON格式分析：
{{
    "task_analysis": {{
        "complexity": "simple/medium/complex",
        "required_skills": ["技能1", "技能2", ...],
        "reasoning": "分析推理过程"
    }},
    "execution_plan": {{
        "type": "single_agent/multi_agent", 
        "selected_agents": [
            {{
                "agent_id": "智能体ID",
                "role": "在此任务中的角色",
                "reason": "选择此智能体的原因"
            }}
        ],
        "workflow": [
            {{
                "step": 1,
                "agent_id": "智能体ID", 
                "action": "具体执行的动作",
                "expected_output": "预期输出"
            }}
        ]
    }},
    "expected_outcome": "整体预期结果描述"
}}
"""
        return prompt
    
    def _get_agent_capabilities(self) -> str:
        """动态获取所有可用智能体的能力描述 - AI First通用设计"""
        capabilities = []
        
        for agent_id, agent in self.available_agents.items():
            try:
                # 通用方法获取智能体信息，不硬编码特定字段
                info = agent.get_agent_info()
                
                # 构建能力描述，支持任意智能体类型
                capability_desc = f"**@{agent_id}**"
                
                # 动态提取可用信息
                if 'name' in info:
                    capability_desc += f" ({info['name']})"
                
                if 'description' in info:
                    capability_desc += f"\\n  - 专业领域: {info['description']}"
                
                if 'expertise' in info and isinstance(info['expertise'], list):
                    capability_desc += f"\\n  - 专业技能: {', '.join(info['expertise'])}"
                
                if 'role' in info:
                    capability_desc += f"\\n  - 角色定位: {info['role']}"
                
                # 如果有自定义提示词，提取关键能力信息
                if 'custom_prompt' in info:
                    # 这里可以进一步用AI来分析custom_prompt提取能力
                    capability_desc += f"\\n  - 专业能力: 详见完整能力描述"
                
                capabilities.append(capability_desc)
                
            except Exception as e:
                # 容错处理，确保即使某个智能体信息获取失败也不影响整体
                capabilities.append(f"**@{agent_id}**: 通用智能体")
        
        return "\\n\\n".join(capabilities)
    
    async def process_user_input(self, user_input: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """处理用户输入，协调Agent执行"""
        try:
            # 记录当前任务
            self.current_task = user_input
            
            # 提取@引用
            mentions = self.mention_processor.extract_mentions(user_input)
            
            # 分析任务
            task_analysis = await self._analyze_task(user_input, mentions)
            
            if not task_analysis["success"]:
                return task_analysis
            
            # 获取执行计划
            execution_plan = task_analysis["data"]["plan"]
            
            # 展示任务分析结果并等待确认
            analysis_display = self._format_analysis_for_display(
                task_analysis["data"]["analysis"],
                execution_plan
            )
            
            # 返回分析结果，需要用户确认
            return {
                "success": True,
                "data": {
                    "response": analysis_display,
                    "agent_name": "智能协调员",
                    "agent_id": "coordinator",
                    "requires_confirmation": True,
                    "execution_plan": execution_plan,
                    "user_input": user_input,
                    "conversation_history": conversation_history
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"协调处理失败: {str(e)}"
            }
    
    async def execute_confirmed_plan(self, execution_plan: Dict[str, Any], user_input: str, 
                                    conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """执行已确认的计划"""
        try:
            # 执行任务
            if execution_plan["type"] == "single_agent":
                # 单Agent执行
                result = await self._execute_single_agent_task(
                    execution_plan["agent_id"],
                    user_input,
                    conversation_history
                )
            else:
                # 多Agent协作
                result = await self._execute_multi_agent_task(
                    execution_plan["agents"],
                    execution_plan["workflow"],
                    user_input,
                    conversation_history,
                    show_progress=True
                )
            
            # 记录任务历史
            self.task_history.append({
                "task": user_input,
                "plan": execution_plan,
                "result": result,
                "timestamp": self._get_timestamp()
            })
            
            self.coordination_count += 1
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"执行失败: {str(e)}"
            }
    
    async def _analyze_task(self, user_input: str, mentions: List[str]) -> Dict[str, Any]:
        """AI First任务分析 - 让AI智能决策而非硬编码"""
        try:
            # 构建AI分析提示 - 完全由AI来理解和决策
            analysis_prompt = f"""请作为智能协调员，深度分析以下用户任务：

**用户任务**: {user_input}
**提及对象**: {mentions if mentions else '无特殊引用'}

**分析要求**:
1. 深度理解任务的本质需求和复杂度
2. 智能分析所需的专业技能组合  
3. 基于可用智能体能力，智能选择最佳组合
4. 制定最优的执行计划和协作流程

**请严格按照JSON格式回复** (不要添加任何markdown格式或其他文本):
{{
    "task_analysis": {{
        "complexity": "simple/medium/complex",
        "required_skills": ["具体技能1", "具体技能2"],
        "reasoning": "详细的分析推理过程"
    }},
    "execution_plan": {{
        "type": "single_agent/multi_agent", 
        "selected_agents": [
            {{
                "agent_id": "选择的智能体ID",
                "role": "在此任务中的具体角色",
                "reason": "选择此智能体的详细原因"
            }}
        ],
        "workflow": [
            {{
                "step": 1,
                "agent_id": "智能体ID", 
                "action": "具体要执行的动作",
                "expected_output": "此步骤的预期输出"
            }}
        ]
    }},
    "expected_outcome": "整体任务的预期结果描述"
}}"""
            
            # 调用LLM进行AI智能分析
            llm_result = self.llm_cell({"input": analysis_prompt})
            
            if llm_result["success"]:
                analysis_text = llm_result["data"]["response"]
                
                # AI First解析 - 让AI返回结构化数据，而非硬编码解析
                execution_plan = self._parse_ai_analysis(analysis_text)
                
                return {
                    "success": True,
                    "data": {
                        "analysis": analysis_text,
                        "plan": execution_plan
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "AI任务分析失败"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"AI任务分析异常: {str(e)}"
            }
    
    def _parse_ai_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """AI First解析分析结果 - 智能解析JSON而非硬编码"""
        import json
        
        try:
            # 尝试直接解析JSON
            if analysis_text.strip().startswith('{'):
                ai_plan = json.loads(analysis_text.strip())
            else:
                # 如果AI没有严格按JSON格式返回，尝试提取JSON部分
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = analysis_text[json_start:json_end]
                    ai_plan = json.loads(json_text)
                else:
                    # 降级到通用解析
                    return self._fallback_parse(analysis_text)
            
            # 将AI的决策转换为执行计划格式
            execution_plan = ai_plan.get("execution_plan", {})
            plan_type = execution_plan.get("type", "single_agent")
            
            if plan_type == "single_agent":
                selected_agents = execution_plan.get("selected_agents", [])
                agent_id = selected_agents[0]["agent_id"] if selected_agents else self._get_fallback_agent()
                
                # 验证Agent是否存在
                if agent_id not in self.available_agents:
                    print(f"⚠️ AI选择的Agent '{agent_id}' 不存在，使用降级Agent")
                    agent_id = self._get_fallback_agent()
                
                return {
                    "type": "single_agent",
                    "agent_id": agent_id,
                    "ai_reasoning": ai_plan.get("task_analysis", {}).get("reasoning", ""),
                    "expected_outcome": ai_plan.get("expected_outcome", "")
                }
            else:
                # 多智能体协作
                raw_agents = [agent["agent_id"] for agent in execution_plan.get("selected_agents", [])]
                # 过滤掉不存在的Agent
                selected_agents = [aid for aid in raw_agents if aid in self.available_agents]
                
                if not selected_agents:
                    print("⚠️ AI选择的所有Agent都不存在，降级到单Agent处理")
                    return {
                        "type": "single_agent",
                        "agent_id": self._get_fallback_agent(),
                        "ai_reasoning": "AI选择的Agent不存在，降级处理",
                        "expected_outcome": ai_plan.get("expected_outcome", "")
                    }
                
                # 过滤workflow中不存在的Agent
                workflow = execution_plan.get("workflow", [])
                valid_workflow = [step for step in workflow if step.get("agent_id") in self.available_agents]
                
                return {
                    "type": "multi_agent", 
                    "agents": selected_agents,
                    "workflow": valid_workflow,
                    "ai_reasoning": ai_plan.get("task_analysis", {}).get("reasoning", ""),
                    "expected_outcome": ai_plan.get("expected_outcome", ""),
                    "agent_roles": {agent["agent_id"]: agent.get("role", "") for agent in execution_plan.get("selected_agents", []) if agent["agent_id"] in self.available_agents}
                }
                
        except json.JSONDecodeError as e:
            print(f"⚠️ AI返回格式解析失败，使用降级解析: {e}")
            return self._fallback_parse(analysis_text)
        except Exception as e:
            print(f"⚠️ AI分析解析异常: {e}")
            return self._fallback_parse(analysis_text)
    
    def _fallback_parse(self, analysis_text: str) -> Dict[str, Any]:
        """降级解析 - 当AI格式不标准时的容错处理"""
        # 至少选择一个可用的智能体
        fallback_agent = self._get_fallback_agent()
        
        return {
            "type": "single_agent",
            "agent_id": fallback_agent,
            "ai_reasoning": "降级到通用智能体处理",
            "expected_outcome": "通过通用智能体完成任务"
        }
    
    def _get_fallback_agent(self) -> str:
        """获取降级智能体 - 通用设计，不硬编码特定智能体"""
        if self.available_agents:
            return list(self.available_agents.keys())[0]
        return "default_agent"
    
    
    def _format_analysis_for_display(self, analysis: str, execution_plan: Dict[str, Any]) -> str:
        """AI First格式化分析结果 - 动态显示而非硬编码"""
        display_text = f"""
## 🧠 AI智能协调员分析

"""
        
        # 如果是修改后的计划，显示修改信息
        modification_info = execution_plan.get("modification_info")
        if modification_info:
            display_text += f"## 🔄 AI修改分析\n\n"
            display_text += f"**用户反馈**: {modification_info.get('user_feedback', '')}\n"
            display_text += f"**调整内容**: {modification_info.get('changes_made', '')}\n"
            display_text += f"**修改理由**: {modification_info.get('reasoning', '')}\n\n"
        
        # 显示AI的推理过程
        ai_reasoning = execution_plan.get("ai_reasoning", "")
        if ai_reasoning:
            display_text += f"**智能分析**: {ai_reasoning}\n\n"
        
        # 显示预期结果
        expected_outcome = execution_plan.get("expected_outcome", "")
        if expected_outcome:
            display_text += f"**预期结果**: {expected_outcome}\n\n"
        
        display_text += "## 🎯 执行计划\n\n"
        
        if execution_plan["type"] == "single_agent":
            agent_id = execution_plan["agent_id"]
            agent_name = self._get_agent_name(agent_id)
            display_text += f"**执行模式**: 单智能体执行\n"
            display_text += f"**选择智能体**: @{agent_id} ({agent_name})\n\n"
            
        else:
            agents = execution_plan.get("agents", [])
            display_text += f"**执行模式**: 多智能体协作\n"
            display_text += f"**参与智能体**: {len(agents)} 个\n\n"
            
            # 显示智能体角色分配（如果有）
            agent_roles = execution_plan.get("agent_roles", {})
            if agent_roles:
                display_text += "**角色分配**:\n"
                for agent_id in agents:
                    agent_name = self._get_agent_name(agent_id)
                    role = agent_roles.get(agent_id, "专业协作")
                    display_text += f"• @{agent_id} ({agent_name}) - {role}\n"
                display_text += "\n"
            
            # 显示AI制定的工作流程
            workflow = execution_plan.get("workflow", [])
            if workflow:
                display_text += "**AI制定的工作流程**:\n"
                for step in workflow:
                    step_num = step.get("step", "?")
                    agent_id = step.get("agent_id", "unknown")
                    action = step.get("action", "执行任务")
                    expected_output = step.get("expected_output", "")
                    
                    agent_name = self._get_agent_name(agent_id)
                    display_text += f"{step_num}. @{agent_id} ({agent_name}) - {action}"
                    if expected_output:
                        display_text += f"\n   预期输出: {expected_output}"
                    display_text += "\n"
            
            display_text += "\n"
        
        display_text += "**请选择操作**:\n"
        display_text += "• 输入 'y' 或 'yes' 确认执行此计划\n"
        display_text += "• 输入修改意见让AI重新规划 (例如: '请增加数据分析环节')\n"
        display_text += "• 输入 'cancel' 或 '取消' 取消任务\n"
        
        return display_text
    
    def _get_agent_name(self, agent_id: str) -> str:
        """通用方法获取智能体名称 - 支持任意智能体类型"""
        try:
            if agent_id in self.available_agents:
                info = self.available_agents[agent_id].get_agent_info()
                return info.get("name", agent_id)
            return agent_id
        except:
            return agent_id
    
    async def modify_execution_plan(self, original_plan: Dict[str, Any], user_input: str, 
                                   modification_request: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """AI First处理用户修改意见 - 重新规划"""
        try:
            # 构建修改提示 - 让AI理解用户的修改需求并重新规划
            modification_prompt = f"""请作为智能协调员，根据用户的修改意见重新制定执行计划。

**原始用户任务**: {user_input}

**当前执行计划**:
{self._format_plan_for_ai(original_plan)}

**用户修改意见**: {modification_request}

**重新规划要求**:
1. 充分理解用户的修改意见
2. 在原有计划基础上进行优化调整
3. 确保修改后的计划更符合用户期望
4. 保持任务的完整性和逻辑性

**请严格按照JSON格式回复新的执行计划** (不要添加任何markdown格式或其他文本):
{{
    "modification_analysis": {{
        "user_feedback": "对用户修改意见的理解",
        "changes_made": "具体做了哪些调整",
        "reasoning": "修改的理由和逻辑"
    }},
    "task_analysis": {{
        "complexity": "simple/medium/complex",
        "required_skills": ["技能1", "技能2"],
        "reasoning": "重新分析的推理过程"
    }},
    "execution_plan": {{
        "type": "single_agent/multi_agent", 
        "selected_agents": [
            {{
                "agent_id": "智能体ID",
                "role": "在此任务中的角色",
                "reason": "选择此智能体的原因"
            }}
        ],
        "workflow": [
            {{
                "step": 1,
                "agent_id": "智能体ID", 
                "action": "具体要执行的动作",
                "expected_output": "此步骤的预期输出"
            }}
        ]
    }},
    "expected_outcome": "修改后的整体预期结果"
}}"""
            
            # 调用AI重新规划
            llm_result = self.llm_cell({"input": modification_prompt})
            
            if llm_result["success"]:
                analysis_text = llm_result["data"]["response"]
                
                # 解析AI的新规划
                new_execution_plan = self._parse_ai_analysis(analysis_text)
                
                # 添加修改信息
                try:
                    import json
                    if analysis_text.strip().startswith('{'):
                        ai_plan = json.loads(analysis_text.strip())
                        modification_info = ai_plan.get("modification_analysis", {})
                        new_execution_plan["modification_info"] = modification_info
                except:
                    new_execution_plan["modification_info"] = {
                        "user_feedback": modification_request,
                        "changes_made": "AI重新规划了执行方案",
                        "reasoning": "根据用户反馈进行调整"
                    }
                
                return {
                    "success": True,
                    "data": {
                        "analysis": analysis_text,
                        "plan": new_execution_plan,
                        "is_modified": True
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "AI修改规划失败"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"AI修改规划异常: {str(e)}"
            }
    
    def _format_plan_for_ai(self, execution_plan: Dict[str, Any]) -> str:
        """将执行计划格式化给AI理解"""
        plan_text = f"执行类型: {execution_plan.get('type', 'unknown')}\n"
        
        if execution_plan.get("type") == "single_agent":
            agent_id = execution_plan.get("agent_id", "unknown")
            plan_text += f"选择的智能体: @{agent_id} ({self._get_agent_name(agent_id)})\n"
        else:
            agents = execution_plan.get("agents", [])
            plan_text += f"参与智能体: {', '.join([f'@{aid}' for aid in agents])}\n"
            
            workflow = execution_plan.get("workflow", [])
            if workflow:
                plan_text += "工作流程:\n"
                for step in workflow:
                    step_num = step.get("step", "?")
                    agent_id = step.get("agent_id", "unknown")
                    action = step.get("action", "")
                    plan_text += f"  {step_num}. @{agent_id} - {action}\n"
        
        if execution_plan.get("ai_reasoning"):
            plan_text += f"AI推理: {execution_plan['ai_reasoning']}\n"
        
        if execution_plan.get("expected_outcome"):
            plan_text += f"预期结果: {execution_plan['expected_outcome']}\n"
        
        return plan_text
    
    async def _execute_single_agent_task(self, agent_id: str, user_input: str, 
                                       conversation_history: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """执行单Agent任务"""
        if agent_id not in self.available_agents:
            return {
                "success": False,
                "error": f"Agent '{agent_id}' 不存在"
            }
        
        agent = self.available_agents[agent_id]
        
        # 直接调用Agent处理
        result = agent.process_user_input(user_input, conversation_history)
        
        # 添加协调信息
        if result["success"]:
            result["data"]["coordination_info"] = {
                "execution_type": "single_agent",
                "agent_used": agent_id
            }
        
        return result
    
    async def _execute_multi_agent_task(self, agents: List[str], workflow: List[Dict[str, Any]], 
                                      user_input: str, conversation_history: Optional[List[Dict[str, Any]]], 
                                      show_progress: bool = False) -> Dict[str, Any]:
        """AI First多智能体协作执行 - 按AI制定的工作流程执行"""
        results = []
        progress_updates = []
        
        # 按AI制定的工作流程执行每个步骤
        for step in workflow:
            agent_id = step.get("agent_id")
            action = step.get("action", "执行任务")
            expected_output = step.get("expected_output", "")
            
            if not agent_id or agent_id not in self.available_agents:
                print(f"⚠️ 跳过无效智能体: {agent_id}")
                continue
            
            agent = self.available_agents[agent_id]
            agent_name = self._get_agent_name(agent_id)
            
            # 显示进度
            if show_progress:
                step_num = step.get("step", "?")
                progress_msg = f"\n🔄 **步骤 {step_num}**: 正在执行 @{agent_id} ({agent_name}) - {action}"
                if expected_output:
                    progress_msg += f"\n   目标输出: {expected_output}"
                progress_updates.append(progress_msg)
                print(progress_msg)
            
            # AI First构建上下文 - 基于前序结果智能构建
            enhanced_input = self._build_ai_context_for_agent(results, step, user_input)
            
            # 执行智能体任务
            result = agent.process_user_input(enhanced_input, conversation_history)
            
            if result["success"]:
                agent_response = result["data"]["response"]
                results.append({
                    "step": step.get("step", len(results) + 1),
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "action": action,
                    "response": agent_response,
                    "expected_output": expected_output
                })
                
                # 显示单个Agent的结果
                if show_progress:
                    progress_msg = f"\n✅ **{agent_name}** 完成任务:\n{agent_response}\n"
                    progress_updates.append(progress_msg)
                    print(progress_msg)
            else:
                error_msg = f"❌ {agent_name} 执行失败: {result.get('error', '未知错误')}"
                progress_updates.append(error_msg)
                if show_progress:
                    print(error_msg)
        
        # AI First结果整合 - 让AI来整合最终结果
        final_response = await self._ai_integrate_final_result(results, user_input, workflow)
        
        if show_progress:
            progress_msg = f"\n🎯 **AI智能协调员** 整合最终结果:\n{final_response}\n"
            progress_updates.append(progress_msg)
            print(progress_msg)
        
        return {
            "success": True,
            "data": {
                "response": final_response,
                "agent_name": "AI智能协调员",
                "agent_id": "coordinator",
                "coordination_info": {
                    "execution_type": "ai_multi_agent",
                    "agents_used": agents,
                    "ai_workflow": workflow,
                    "individual_results": results,
                    "progress_updates": progress_updates if show_progress else []
                },
                "deliverables": [],
                "user_learning": {}
            }
        }
    
    def _build_context_for_agent(self, previous_results: List[Dict[str, Any]], current_stage: int, user_input: str) -> str:
        """为当前智能体构建包含前面结果的上下文信息"""
        if not previous_results:
            return user_input
        
        context_parts = [
            "## 前序工作成果",
            "",
            "以下是前面智能体的工作成果，请基于这些信息继续完成您的任务：",
            ""
        ]
        
        for i, result in enumerate(previous_results):
            context_parts.append(f"### {i+1}. {result['agent_name']}的工作成果:")
            context_parts.append(result['response'])
            context_parts.append("")
        
        context_parts.extend([
            "## 您的任务",
            "",
            f"原始用户需求: {user_input}",
            "",
            "请基于以上前序工作成果，完成您的专业任务。"
        ])
        
        return "\n".join(context_parts)
    
    def _integrate_final_result(self, results: List[Dict[str, Any]], user_input: str) -> str:
        """整合最终结果"""
        if not results:
            return "没有可用的结果进行整合。"
        
        # 如果只有一个结果，直接返回
        if len(results) == 1:
            return results[0]['response']
        
        # 多个结果需要整合
        integration_parts = [
            "## 📊 多智能体协作成果整合",
            "",
            f"针对您的需求「{user_input}」，我们的专业智能体团队已完成协作，以下是整合后的综合成果：",
            ""
        ]
        
        for i, result in enumerate(results):
            integration_parts.append(f"### {i+1}. {result['agent_name']}的贡献")
            integration_parts.append(result['response'])
            integration_parts.append("")
        
        integration_parts.extend([
            "## 🎯 综合建议",
            "",
            "基于以上各专业智能体的分析和建议，我们为您提供了全面的解决方案。",
            "每个智能体都从其专业角度提供了有价值的见解，您可以根据实际需求选择采纳相应的建议。"
        ])
        
        return "\n".join(integration_parts)
    
    def _build_ai_context_for_agent(self, previous_results: List[Dict[str, Any]], current_step: Dict[str, Any], user_input: str) -> str:
        """AI First上下文构建 - 智能为当前智能体构建最佳上下文"""
        if not previous_results:
            # 第一个智能体，直接使用原始任务加上AI的指导
            action = current_step.get("action", "")
            expected_output = current_step.get("expected_output", "")
            
            context = f"""## 🎯 您的专业任务

**原始用户需求**: {user_input}

**AI协调员为您分配的具体任务**: {action}
"""
            if expected_output:
                context += f"\n**期望您产出的结果**: {expected_output}\n"
            
            context += "\n请发挥您的专业能力，完成以上任务。"
            return context
        
        # 后续智能体，需要基于前序结果构建上下文
        context_parts = [
            "## 🔄 协作任务上下文",
            "",
            f"**原始用户需求**: {user_input}",
            "",
            "**前序智能体工作成果**:"
        ]
        
        # 按步骤顺序展示前序结果
        for result in previous_results:
            step_num = result.get("step", "?")
            agent_name = result.get("agent_name", "智能体")
            action = result.get("action", "")
            response = result.get("response", "")
            
            context_parts.extend([
                f"",
                f"### 步骤 {step_num}: {agent_name}",
                f"**执行任务**: {action}",
                f"**产出结果**: {response}",
                ""
            ])
        
        # 当前智能体的任务
        action = current_step.get("action", "")
        expected_output = current_step.get("expected_output", "")
        
        context_parts.extend([
            "## 🎯 您的专业任务",
            "",
            f"**AI协调员为您分配的任务**: {action}"
        ])
        
        if expected_output:
            context_parts.append(f"**期望您产出的结果**: {expected_output}")
        
        context_parts.extend([
            "",
            "**请基于以上前序工作成果，发挥您的专业能力完成您的任务。**"
        ])
        
        return "\n".join(context_parts)
    
    async def _ai_integrate_final_result(self, results: List[Dict[str, Any]], user_input: str, workflow: List[Dict[str, Any]]) -> str:
        """AI First最终结果整合 - 让AI智能整合而非模板化"""
        if not results:
            return "没有可整合的结果。"
        
        if len(results) == 1:
            # 单智能体结果直接返回
            return results[0]["response"]
        
        # 多智能体结果需要AI智能整合
        integration_prompt = f"""请作为智能协调员，将多个专业智能体的工作成果智能整合成一个完整、连贯的最终答案。

**原始用户需求**: {user_input}

**各专业智能体的工作成果**:
"""
        
        for result in results:
            step_num = result.get("step", "?")
            agent_name = result.get("agent_name", "智能体")
            action = result.get("action", "")
            response = result.get("response", "")
            
            integration_prompt += f"""
### 步骤 {step_num}: {agent_name}
**执行任务**: {action}
**产出结果**: {response}
"""
        
        integration_prompt += f"""

**整合要求**:
1. 将各智能体的成果有机整合，形成完整答案
2. 确保逻辑清晰，结构合理
3. 突出各专业智能体的价值贡献
4. 直接回答用户的原始需求
5. 避免简单罗列，要做到深度整合

请提供最终的整合结果："""
        
        try:
            # 让AI来整合结果
            llm_result = self.llm_cell({"input": integration_prompt})
            
            if llm_result["success"]:
                return llm_result["data"]["response"]
            else:
                # 降级到简单整合
                return self._fallback_integrate_result(results, user_input)
                
        except Exception as e:
            print(f"⚠️ AI整合失败，使用降级整合: {e}")
            return self._fallback_integrate_result(results, user_input)
    
    def _fallback_integrate_result(self, results: List[Dict[str, Any]], user_input: str) -> str:
        """降级结果整合"""
        integration_parts = [
            f"## 📊 多智能体协作成果",
            f"",
            f"针对您的需求「{user_input}」，我们的专业智能体团队完成了以下工作：",
            f""
        ]
        
        for result in results:
            step_num = result.get("step", "?")
            agent_name = result.get("agent_name", "智能体")
            response = result.get("response", "")
            
            integration_parts.append(f"### {step_num}. {agent_name}的贡献")
            integration_parts.append(response)
            integration_parts.append("")
        
        return "\n".join(integration_parts)
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_status(self) -> Dict[str, Any]:
        """获取协调员状态"""
        return {
            "available_agents": list(self.available_agents.keys()),
            "current_task": self.current_task,
            "coordination_count": self.coordination_count,
            "recent_tasks": self.task_history[-5:] if self.task_history else []
        }
    
    def reset(self):
        """重置协调员状态"""
        self.current_task = None
        self.task_history = []
        self.coordination_count = 0