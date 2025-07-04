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
        AI生命体的思考过程
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            思考结果
        """
        try:
            if self.pipeline:
                # 使用Pipeline组织的复杂思考
                return self._pipeline_thinking(input_data, context)
            else:
                # 单Cell的简单思考
                return self._simple_thinking(input_data, context)
                
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
        result = main_cell.process({"input": complete_prompt})
        
        # 应用prompt变量插值
        if result.get("success", False):
            response_data = result.get("data", {})
            if "response" in response_data:
                response = behavior.interpolate_variables(response_data["response"])
                result["data"]["response"] = response
        
        return result
    
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
        from ..core.config import get_api_key, get_api_base_url
        
        return StateMemoryCell(
            config={
                "user_namespace": f"{dna.name.lower()}_knowledge",
                "openai_api_key": dna.capability.models.get("api_key") or get_api_key("openai"),
                "openai_base_url": dna.capability.models.get("base_url") or get_api_base_url("openai"),
                "embedding_model": dna.capability.models.get("embed", "text-embedding-3-large")
            }
        )
    
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
    
    def _create_llm_cell(self, dna: EmbryoDNA) -> LLMCell:
        """创建通用LLMCell"""
        behavior = dna.behavior
        system_prompt = behavior.system_prompt or behavior._generate_default_system_prompt()
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config={
                "system_prompt": system_prompt,
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
    
    def _create_memory_cell(self, dna: EmbryoDNA) -> StateMemoryCell:
        """创建记忆Cell"""
        from ..core.config import get_api_key, get_api_base_url
        
        return StateMemoryCell(
            config={
                "user_namespace": f"{dna.name.lower()}_memory",
                "openai_api_key": dna.capability.models.get("api_key") or get_api_key("openai"),
                "openai_base_url": dna.capability.models.get("base_url") or get_api_base_url("openai"),
                "embedding_model": dna.capability.models.get("embed", "text-embedding-3-large")
            }
        )
    
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
        
        # 记录日志
        self._logger.info(f"生命体 {life_form.dna.name} 初始化完成")
    
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
        return ["LLMCell", "StateMemoryCell"]
    
    def get_supported_architectures(self) -> List[str]:
        """获取支持的架构列表"""
        return ["pipeline", "parallel"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取培养器统计信息"""
        return {
            "total_growths": self.grown_count,
            "success_rate": self.success_rate,
            "supported_skills": self.get_supported_skills(),
            "supported_cell_types": self.get_supported_cell_types(),
            "supported_architectures": self.get_supported_architectures()
        } 