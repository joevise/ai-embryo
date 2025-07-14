"""
CoordinatorAgent - 智能协调管理器

AI驱动的任务分析、智能体设计和工作流协调系统
支持动态智能体生成和三阶段工作流
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from futurembryo.cells.llm_cell import LLMCell
from futurembryo.cells.tool_cell import ToolCell
from futurembryo.core.context_builder import ContextBuilder
from core.dynamic_agent_factory import get_dynamic_agent_factory, create_agent_from_ai_design
from agents.user_aware_agent_v2 import UserAwareAgent


class CoordinatorAgent:
    """智能协调器 - AI驱动的任务分析和智能体协调"""
    
    def __init__(self, user_id: str = "default"):
        """
        初始化协调器
        
        Args:
            user_id: 用户标识
        """
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        
        # 状态管理
        self.is_waiting_confirmation = False
        self.pending_plan = None
        self.current_phase = "idle"  # idle, analyzing, confirming, executing
        self.created_agents: Dict[str, UserAwareAgent] = {}
        
        # 创建上下文构建器
        self.context_builder = ContextBuilder(
            user_id=user_id,
            enable_memory=True
        )
        
        # 配置LLM（使用Claude 4模型）
        llm_config = {
            "model": "anthropic/claude-sonnet-4-20250514",
            "temperature": 0.7,
            "max_tokens": 2000,  # 限制输出长度，强制只做规划
            "enable_tools": True,
            "tool_choice": "auto",
            "max_tool_calls": 2
        }
        
        # 创建LLM Cell
        self.llm_cell = LLMCell(
            model_name=llm_config["model"],
            config=llm_config,
            tool_cell=self.context_builder.tool_cell
        )
        
        # 动态智能体工厂
        self.agent_factory = None
        
        self.logger.info("🎯 Coordinator Agent initialized")
    
    async def initialize(self):
        """异步初始化"""
        try:
            # 初始化动态智能体工厂
            self.agent_factory = await get_dynamic_agent_factory()
            self.logger.info("✅ Coordinator Agent fully initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize coordinator: {e}")
            raise
    
    def get_system_prompt(self) -> str:
        """获取协调器的系统提示词"""
        return """你是一个智能协调器，负责分析任务并设计专门的AI智能体来完成工作。

## 核心能力
1. **任务分析**: 深度理解用户需求，识别任务类型和复杂度
2. **智能体设计**: 基于任务需求设计专门的AI智能体
3. **工具配置**: 为每个智能体配置合适的工具和能力
4. **工作流协调**: 协调多个智能体的协作执行

## 工作流程
### 第一阶段：任务分析和智能体设计
当收到任务时，你需要：
1. 分析任务的性质、复杂度和所需技能
2. 设计需要的智能体，包括：
   - 智能体角色和职责
   - 所需工具和能力
   - 工作顺序和协作方式
3. 输出完整的执行计划

### 第二阶段：确认阶段
- 等待用户确认你的计划
- 根据用户反馈调整计划

### 第三阶段：创建智能体并执行
- 动态创建所需的智能体
- 协调智能体按计划执行任务
- 收集和整理最终结果

## 智能体设计模板
为任务设计智能体时，使用以下JSON格式：

```json
{
  "agent_id": "unique_agent_identifier",
  "name": "Agent Display Name", 
  "role": "researcher|analyst|writer|planner|calculator|creator|specialist",
  "system_prompt": "详细的角色描述和工作指令",
  "capabilities": ["capability1", "capability2"],
  "required_tools": ["knowledge_search", "news_search"],
  "tool_categories": ["basic", "research", "knowledge", "information", "search", "current_events"],
  "creativity_level": "low|medium|high",
  "task_complexity": "simple|medium|complex",
  "tool_usage": "minimal|moderate|intensive",
  "enable_memory": true,
  "max_memory_items": 100,
  "task_description": "具体的任务描述"
}
```

## 真实可用工具说明
- **basic**: 基础工具（add, multiply, text_length, text_upper）
- **research/knowledge**: 技术文档查询（context7 MCP工具）
- **information/search**: 知识库搜索功能  
- **current_events/news**: 最新政经新闻动态（dynamic-knowledgebase MCP工具）

注意：智能体只能使用系统中真实存在的工具，不要设计不存在的工具。

## 当前阶段行为准则
### 分析阶段 (current_phase="analyzing")
- 专注于任务分析和智能体设计
- 输出详细的执行计划
- **必须在输出最后明确说明：等待用户确认**
- 不要立即执行任务

### 确认阶段 (current_phase="confirming") 
- 只处理用户的确认或修改意见
- 根据反馈调整计划
- 获得确认后进入执行阶段

### 执行阶段 (current_phase="executing")
- 创建设计的智能体
- 协调智能体执行任务
- 收集完整结果并呈现给用户

## 重要提醒
1. **分阶段执行**: 严格按照三阶段流程，不要跳过确认阶段
2. **输出完整结果**: 执行阶段要确保显示智能体的完整输出，不要总结
3. **AI驱动决策**: 所有判断都应该基于AI分析，不使用硬编码逻辑
4. **工程控制**: 分析阶段限制在2000tokens内，确保停在规划阶段"""
    
    async def process_message(self, user_input: str) -> str:
        """
        处理用户消息的主要入口
        
        Args:
            user_input: 用户输入
            
        Returns:
            str: 协调器的响应
        """
        try:
            self.logger.info(f"📥 Coordinator processing message in phase: {self.current_phase}")
            
            # 检查是否在等待确认
            if self.is_waiting_confirmation:
                return await self._handle_confirmation_response(user_input)
            
            # 分析阶段：处理新任务
            return await self._handle_new_task(user_input)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing message: {e}")
            return f"抱歉，处理您的请求时出现错误：{str(e)}"
    
    async def _handle_new_task(self, user_input: str) -> str:
        """处理新任务（分析阶段）"""
        try:
            self.current_phase = "analyzing"
            self.logger.info("🔍 Starting task analysis phase")
            
            # 构建分析阶段的消息
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"""请分析以下任务并设计相应的AI智能体来完成：

任务描述：{user_input}

请按照以下步骤进行：

1. **任务分析**
   - 任务类型和复杂度
   - 所需的核心技能和能力
   - 可能的挑战和难点

2. **智能体设计**
   - 列出需要创建的智能体
   - 每个智能体的具体配置（使用JSON模板）
   - 智能体之间的协作关系

3. **执行计划**
   - 详细的执行步骤
   - 预期的输出和交付物
   - 时间估算

请在分析结束后明确说明：**等待用户确认计划后开始执行**

当前阶段：analyzing（只做规划，不执行）"""}
            ]
            
            # 调用LLM进行分析
            context = {
                "messages": messages,
                "enable_tools": False  # 分析阶段不使用工具
            }
            
            result = self.llm_cell(context)
            
            if result["success"]:
                response = result["data"]["response"]
                
                # 设置等待确认状态
                self.is_waiting_confirmation = True
                self.current_phase = "confirming"
                self.pending_plan = response
                
                self.logger.info("✅ Task analysis completed, waiting for confirmation")
                return response
            else:
                return f"分析任务时出现错误：{result['error']}"
                
        except Exception as e:
            self.logger.error(f"❌ Error in task analysis: {e}")
            return f"分析任务时出现错误：{str(e)}"
    
    async def _handle_confirmation_response(self, user_input: str) -> str:
        """处理用户确认响应"""
        try:
            self.logger.info("💬 Processing confirmation response")
            
            # 使用AI判断用户意图
            messages = [
                {"role": "system", "content": """你是一个智能确认处理器。分析用户的响应，判断用户的意图：

1. **确认执行**: 用户同意当前计划，可以开始执行
   - 关键词：确认、同意、开始、执行、好的、可以、OK等
   
2. **要求修改**: 用户希望修改计划
   - 包含具体的修改建议或不同意见
   
3. **需要澄清**: 用户有疑问需要解释

请分析用户响应并输出JSON格式：
{
  "intent": "confirm|modify|clarify",
  "confidence": 0.0-1.0,
  "reason": "判断理由",
  "modifications": "如果是修改意图，列出具体修改点"
}"""},
                {"role": "user", "content": f"用户响应：{user_input}"}
            ]
            
            result = self.llm_cell({"messages": messages, "enable_tools": False})
            
            if result["success"]:
                try:
                    # 尝试解析AI的判断结果
                    response_text = result["data"]["response"]
                    # 提取JSON部分
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                    else:
                        json_text = response_text
                    
                    intent_analysis = json.loads(json_text)
                    intent = intent_analysis.get("intent", "clarify")
                    
                except (json.JSONDecodeError, KeyError) as e:
                    # 降级到关键词匹配
                    self.logger.warning(f"JSON parsing failed, using keyword matching: {e}")
                    user_input_lower = user_input.lower()
                    confirm_keywords = ["确认", "同意", "ok", "好的", "开始", "执行", "yes", "y", "可以"]
                    intent = "confirm" if any(keyword in user_input_lower for keyword in confirm_keywords) else "modify"
                
                if intent == "confirm":
                    return await self._execute_confirmed_plan()
                elif intent == "modify":
                    return await self._handle_plan_modification(user_input)
                else:
                    return await self._handle_clarification_request(user_input)
            else:
                # 降级处理
                user_input_lower = user_input.lower()
                confirm_keywords = ["确认", "同意", "ok", "好的", "开始", "执行", "yes", "y", "可以"]
                
                if any(keyword in user_input_lower for keyword in confirm_keywords):
                    return await self._execute_confirmed_plan()
                else:
                    return await self._handle_plan_modification(user_input)
                    
        except Exception as e:
            self.logger.error(f"❌ Error handling confirmation: {e}")
            return f"处理确认时出现错误：{str(e)}"
    
    async def _execute_confirmed_plan(self) -> str:
        """执行已确认的计划"""
        try:
            self.current_phase = "executing"
            self.is_waiting_confirmation = False
            
            self.logger.info("🚀 Starting plan execution phase")
            
            # 从计划中提取智能体设计
            agent_designs = await self._extract_agent_designs_from_plan(self.pending_plan)
            
            if not agent_designs:
                return "❌ 无法从计划中提取智能体设计，请重新开始。"
            
            # 创建智能体并依次执行（保持上下文传递）
            execution_results = []
            previous_results = []  # 存储前面智能体的结果，用于上下文传递
            
            for i, design in enumerate(agent_designs):
                try:
                    self.logger.info(f"🏭 Creating agent: {design.get('name', 'Unknown')}")
                    
                    # 创建智能体
                    agent = await create_agent_from_ai_design(design, self.user_id)
                    agent_id = design.get('agent_id', 'unknown')
                    self.created_agents[agent_id] = agent
                    
                    # 构建包含上下文的任务描述
                    task_description = design.get('task_description', '请完成分配给你的任务')
                    
                    # 如果不是第一个智能体，添加前面智能体的结果作为上下文
                    if previous_results:
                        context_info = self._build_context_for_agent(previous_results, i + 1)
                        full_task_description = f"{task_description}\n\n{context_info}"
                    else:
                        full_task_description = task_description
                    
                    # 执行智能体任务
                    result = await self._execute_agent_task(agent, full_task_description)
                    
                    # 保存当前结果
                    current_result = {
                        'agent_name': design.get('name', 'Unknown'),
                        'agent_id': agent_id,
                        'result': result
                    }
                    
                    execution_results.append(current_result)
                    previous_results.append(current_result)  # 添加到上下文中
                    
                except Exception as e:
                    self.logger.error(f"❌ Agent execution failed: {e}")
                    error_result = {
                        'agent_name': design.get('name', 'Unknown'),
                        'agent_id': design.get('agent_id', 'unknown'),
                        'error': str(e)
                    }
                    execution_results.append(error_result)
                    previous_results.append(error_result)  # 即使失败也要添加到上下文中
            
            # 格式化最终结果
            return self._format_execution_results(execution_results)
            
        except Exception as e:
            self.logger.error(f"❌ Error executing plan: {e}")
            return f"执行计划时出现错误：{str(e)}"
        finally:
            # 重置状态
            self.current_phase = "idle"
            self.pending_plan = None
    
    async def _extract_agent_designs_from_plan(self, plan_text: str) -> List[Dict[str, Any]]:
        """从计划文本中提取智能体设计"""
        try:
            # 使用AI提取智能体设计
            messages = [
                {"role": "system", "content": """你是一个智能体设计提取器。从给定的计划文本中提取所有的智能体设计配置。

请从计划中找到所有的智能体设计（JSON格式），并为每个智能体添加执行任务描述。

输出格式为JSON数组：
[
  {
    "agent_id": "...",
    "name": "...",
    "role": "...",
    "system_prompt": "...",
    "capabilities": [...],
    "required_tools": [...],
    "tool_categories": [...],
    "creativity_level": "...",
    "task_complexity": "...",
    "tool_usage": "...",
    "enable_memory": true,
    "max_memory_items": 100,
    "task_description": "从计划中推断的具体任务描述"
  }
]

如果没有找到有效的智能体设计，返回空数组 []。"""},
                {"role": "user", "content": f"计划文本：\n{plan_text}"}
            ]
            
            result = self.llm_cell({"messages": messages, "enable_tools": False})
            
            if result["success"]:
                response_text = result["data"]["response"]
                
                # 提取JSON数组
                try:
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                    else:
                        json_text = response_text.strip()
                    
                    designs = json.loads(json_text)
                    
                    if isinstance(designs, list):
                        self.logger.info(f"📋 Extracted {len(designs)} agent designs")
                        return designs
                    else:
                        self.logger.warning("Extracted data is not a list")
                        return []
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse agent designs JSON: {e}")
                    return []
            else:
                self.logger.error("Failed to extract agent designs")
                return []
                
        except Exception as e:
            self.logger.error(f"Error extracting agent designs: {e}")
            return []
    
    def _build_context_for_agent(self, previous_results: List[Dict[str, Any]], current_stage: int) -> str:
        """为当前智能体构建包含前面结果的上下文信息"""
        context_parts = [
            "## 前序工作成果",
            "",
            "以下是前面智能体的工作成果，请基于这些信息继续完成您的任务：",
            ""
        ]
        
        for i, result in enumerate(previous_results, 1):
            agent_name = result.get('agent_name', 'Unknown')
            context_parts.append(f"### {i}. {agent_name} 的分析结果：")
            
            if 'error' in result:
                context_parts.append(f"❌ 执行失败: {result['error']}")
            else:
                # 获取实际结果内容
                agent_result = result.get('result', '无结果')
                # 限制长度以避免上下文过长
                if len(agent_result) > 4000:
                    agent_result = agent_result[:4000] + "\n...[内容已截断]"
                context_parts.append(agent_result)
            
            context_parts.append("")  # 空行分隔
        
        context_parts.extend([
            "---",
            f"现在请您作为第 {current_stage} 阶段的智能体，基于以上成果继续工作：",
            ""
        ])
        
        return "\n".join(context_parts)

    async def _execute_agent_task(self, agent: UserAwareAgent, task_description: str) -> str:
        """执行智能体任务"""
        try:
            self.logger.info(f"🎯 Executing task for agent: {getattr(agent, 'name', 'Unknown')}")
            
            # 调用智能体处理任务
            result = await agent.process_message(task_description)
            
            if isinstance(result, dict) and "response" in result:
                return result["response"]
            else:
                return str(result)
                
        except Exception as e:
            self.logger.error(f"❌ Agent task execution error: {e}")
            return f"智能体执行任务时出现错误：{str(e)}"
    
    def _format_execution_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化执行结果"""
        output = ["🎉 **任务执行完成**\n"]
        
        for i, result in enumerate(results, 1):
            agent_name = result.get('agent_name', 'Unknown')
            agent_id = result.get('agent_id', 'unknown')
            
            output.append(f"## {i}. {agent_name} ({agent_id})")
            
            if 'error' in result:
                output.append(f"❌ **执行失败**: {result['error']}")
            else:
                output.append("✅ **执行成功**")
                output.append(f"**完整输出**:")
                output.append(f"```\n{result['result']}\n```")
            
            output.append("")  # 空行分隔
        
        output.append("---")
        output.append(f"📊 **总结**: 共执行 {len(results)} 个智能体任务")
        
        success_count = len([r for r in results if 'error' not in r])
        output.append(f"✅ 成功: {success_count} | ❌ 失败: {len(results) - success_count}")
        
        return "\n".join(output)
    
    async def _handle_plan_modification(self, user_input: str) -> str:
        """处理计划修改请求"""
        try:
            # 基于用户反馈修改计划
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "assistant", "content": self.pending_plan},
                {"role": "user", "content": f"请根据以下反馈修改计划：{user_input}"}
            ]
            
            result = self.llm_cell({"messages": messages, "enable_tools": False})
            
            if result["success"]:
                modified_plan = result["data"]["response"]
                self.pending_plan = modified_plan
                
                return f"📝 **计划已根据您的反馈进行修改**:\n\n{modified_plan}\n\n请确认修改后的计划是否满意。"
            else:
                return f"修改计划时出现错误：{result['error']}"
                
        except Exception as e:
            return f"处理计划修改时出现错误：{str(e)}"
    
    async def _handle_clarification_request(self, user_input: str) -> str:
        """处理澄清请求"""
        try:
            messages = [
                {"role": "system", "content": "你是一个计划解释器。用户对当前计划有疑问，请简洁明了地回答。"},
                {"role": "assistant", "content": f"当前计划:\n{self.pending_plan}"},
                {"role": "user", "content": user_input}
            ]
            
            result = self.llm_cell({"messages": messages, "enable_tools": False})
            
            if result["success"]:
                clarification = result["data"]["response"]
                return f"💡 **计划说明**:\n\n{clarification}\n\n请确认是否可以开始执行计划。"
            else:
                return f"提供说明时出现错误：{result['error']}"
                
        except Exception as e:
            return f"处理澄清请求时出现错误：{str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        return {
            "current_phase": self.current_phase,
            "is_waiting_confirmation": self.is_waiting_confirmation,
            "has_pending_plan": self.pending_plan is not None,
            "created_agents_count": len(self.created_agents),
            "created_agents": list(self.created_agents.keys())
        }
    
    async def reset(self):
        """重置协调器状态"""
        self.current_phase = "idle"
        self.is_waiting_confirmation = False
        self.pending_plan = None
        
        # 清理创建的智能体
        if self.agent_factory:
            await self.agent_factory.cleanup_all_agents()
        
        self.created_agents.clear()
        self.logger.info("🔄 Coordinator reset completed")