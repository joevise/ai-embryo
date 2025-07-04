"""
基因类型定义 - 定义AI生命体的五种基因

每种基因负责AI生命体的不同方面：
- PurposeGene: 目标基因 - 定义AI要解决什么问题
- CapabilityGene: 能力基因 - 定义AI需要什么技能
- StructureGene: 结构基因 - 定义AI如何组织
- BehaviorGene: 行为基因 - 定义AI如何表现
- EvolutionGene: 进化基因 - 定义AI如何改进
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .exceptions import GeneError


@dataclass
class PurposeGene:
    """目标基因 - 定义AI的目标和约束"""
    
    goal: str  # 主要目标描述
    metrics: List[str] = None  # 成功指标列表
    constraints: List[str] = None  # 约束条件列表
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.goal or not self.goal.strip():
            raise GeneError("目标基因必须包含明确的goal")
        
        self.metrics = self.metrics or []
        self.constraints = self.constraints or []
    
    def validate(self) -> bool:
        """验证基因有效性"""
        if not isinstance(self.goal, str) or len(self.goal.strip()) < 5:
            raise GeneError("goal必须是至少5个字符的字符串")
        
        if not isinstance(self.metrics, list):
            raise GeneError("metrics必须是列表类型")
            
        if not isinstance(self.constraints, list):
            raise GeneError("constraints必须是列表类型")
        
        return True


@dataclass 
class CapabilityGene:
    """能力基因 - 定义AI的技能和工具"""
    
    skills: List[str] = None  # 技能列表：["chat", "search", "analyze"]
    models: Dict[str, str] = None  # 模型配置：{"llm": "gpt-4", "embed": "text-ada"}
    tools: List[str] = None  # 工具列表：["web_search", "calculator"]
    
    def __post_init__(self):
        """初始化后验证"""
        self.skills = self.skills or ["chat"]  # 默认至少有对话能力
        self.models = self.models or {"llm": "gpt-3.5-turbo"}  # 默认模型
        self.tools = self.tools or []
    
    def validate(self) -> bool:
        """验证基因有效性"""
        if not isinstance(self.skills, list) or len(self.skills) == 0:
            raise GeneError("skills必须是非空列表")
        
        if not isinstance(self.models, dict) or "llm" not in self.models:
            raise GeneError("models必须是包含'llm'键的字典")
            
        if not isinstance(self.tools, list):
            raise GeneError("tools必须是列表类型")
        
        # 验证技能有效性
        valid_skills = {"chat", "search", "analyze", "generate", "knowledge", "tool_use"}
        for skill in self.skills:
            if skill not in valid_skills:
                raise GeneError(f"未知技能: {skill}。有效技能: {valid_skills}")
        
        return True


@dataclass
class StructureGene:
    """结构基因 - 定义AI的组织架构"""
    
    cell_types: List[str] = None  # 细胞类型：["ChatCell", "SearchCell"]
    architecture: str = "pipeline"  # 架构模式：pipeline/parallel/tree/hybrid
    max_complexity: int = 5  # 最大复杂度等级
    auto_scale: bool = True  # 是否自动扩缩容
    
    def __post_init__(self):
        """初始化后验证"""
        if self.cell_types is None:
            # 根据技能自动推断Cell类型
            self.cell_types = ["LLMCell"]
    
    def validate(self) -> bool:
        """验证基因有效性"""
        if not isinstance(self.cell_types, list) or len(self.cell_types) == 0:
            raise GeneError("cell_types必须是非空列表")
        
        valid_architectures = {"pipeline", "parallel", "tree", "hybrid"}
        if self.architecture not in valid_architectures:
            raise GeneError(f"未知架构: {self.architecture}。有效架构: {valid_architectures}")
        
        if not isinstance(self.max_complexity, int) or self.max_complexity < 1:
            raise GeneError("max_complexity必须是大于0的整数")
        
        if not isinstance(self.auto_scale, bool):
            raise GeneError("auto_scale必须是布尔值")
        
        return True


@dataclass
class BehaviorGene:
    """行为基因 - 定义AI的行为特征"""
    
    personality: List[str] = None  # 性格特征：["helpful", "professional", "patient"]
    style: str = "friendly_professional"  # 交互风格
    language: str = "zh-CN"  # 主要语言
    safety: Dict[str, Any] = None  # 安全策略
    
    # 新增：Prompt配置系统
    system_prompt: str = ""  # 系统提示词
    user_prompt_template: str = ""  # 用户提示词模板
    context_prompt: str = ""  # 上下文提示词
    output_format_prompt: str = ""  # 输出格式提示词
    prompt_variables: Dict[str, str] = None  # 提示词变量
    
    def __post_init__(self):
        """初始化后验证"""
        self.personality = self.personality or ["helpful", "professional"]
        self.safety = self.safety or {
            "content_filter": True,
            "privacy_protection": True,
            "rate_limit": "100/hour"
        }
        self.prompt_variables = self.prompt_variables or {}
        
        # 如果没有设置系统提示词，根据personality自动生成基础版本
        if not self.system_prompt:
            self.system_prompt = self._generate_default_system_prompt()
    
    def _generate_default_system_prompt(self) -> str:
        """根据性格特征生成默认系统提示词"""
        personality_desc = "、".join(self.personality)
        
        return f"""你是一个{personality_desc}的AI助手。

你的交互风格是{self.style}，主要使用{self.language}进行交流。

请始终保持你的核心特质：
{chr(10).join(f"- {trait}" for trait in self.personality)}

在回答问题时，请：
1. 仔细理解用户的需求
2. 提供准确、有用的信息
3. 保持友好和专业的态度
4. 根据上下文调整回应方式
"""
    
    def get_complete_prompt(self, user_input: str = "", context: str = "") -> str:
        """
        构建完整的提示词
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            完整的提示词
        """
        parts = []
        
        # 系统提示词
        if self.system_prompt:
            parts.append(f"系统提示：\n{self.system_prompt}")
        
        # 上下文提示词
        if self.context_prompt and context:
            formatted_context = self.context_prompt.format(context=context)
            parts.append(f"上下文：\n{formatted_context}")
        
        # 用户提示词模板
        if self.user_prompt_template and user_input:
            formatted_user = self.user_prompt_template.format(user_input=user_input)
            parts.append(f"用户请求：\n{formatted_user}")
        elif user_input:
            parts.append(f"用户请求：\n{user_input}")
        
        # 输出格式提示词
        if self.output_format_prompt:
            parts.append(f"输出格式：\n{self.output_format_prompt}")
        
        return "\n\n".join(parts)
    
    def interpolate_variables(self, text: str) -> str:
        """
        插值提示词变量
        
        Args:
            text: 包含变量的文本
            
        Returns:
            插值后的文本
        """
        for var_name, var_value in self.prompt_variables.items():
            text = text.replace(f"{{{var_name}}}", var_value)
        return text
    
    def validate(self) -> bool:
        """验证基因有效性"""
        if not isinstance(self.personality, list):
            raise GeneError("personality必须是列表类型")
        
        valid_styles = {"formal", "casual", "friendly_professional", "professional", "technical", "creative"}
        if self.style not in valid_styles:
            raise GeneError(f"未知风格: {self.style}。有效风格: {valid_styles}")
        
        if not isinstance(self.language, str):
            raise GeneError("language必须是字符串类型")
        
        if not isinstance(self.safety, dict):
            raise GeneError("safety必须是字典类型")
        
        # 验证新增的prompt字段
        if not isinstance(self.system_prompt, str):
            raise GeneError("system_prompt必须是字符串类型")
        
        if not isinstance(self.user_prompt_template, str):
            raise GeneError("user_prompt_template必须是字符串类型")
        
        if not isinstance(self.context_prompt, str):
            raise GeneError("context_prompt必须是字符串类型")
        
        if not isinstance(self.output_format_prompt, str):
            raise GeneError("output_format_prompt必须是字符串类型")
        
        if not isinstance(self.prompt_variables, dict):
            raise GeneError("prompt_variables必须是字典类型")
        
        return True


@dataclass
class EvolutionGene:
    """进化基因 - 定义AI的进化和优化策略"""
    
    enabled: bool = True  # 是否启用进化
    learn_rate: float = 0.5  # 学习速度 0.0-1.0
    adapt_speed: str = "normal"  # 适应速度：slow/normal/fast
    mutation_rate: float = 0.1  # 变异概率 0.0-1.0
    fitness_focus: List[str] = None  # 优化重点
    auto_evolution: bool = True  # 自动进化
    evolution_interval: int = 3600  # 进化间隔(秒)
    
    def __post_init__(self):
        """初始化后验证"""
        self.fitness_focus = self.fitness_focus or ["accuracy", "speed"]
    
    def validate(self) -> bool:
        """验证基因有效性"""
        if not isinstance(self.enabled, bool):
            raise GeneError("enabled必须是布尔值")
        
        if not (0.0 <= self.learn_rate <= 1.0):
            raise GeneError("learn_rate必须在0.0-1.0之间")
        
        valid_speeds = {"slow", "normal", "fast"}
        if self.adapt_speed not in valid_speeds:
            raise GeneError(f"未知适应速度: {self.adapt_speed}。有效值: {valid_speeds}")
        
        if not (0.0 <= self.mutation_rate <= 1.0):
            raise GeneError("mutation_rate必须在0.0-1.0之间")
        
        if not isinstance(self.fitness_focus, list):
            raise GeneError("fitness_focus必须是列表类型")
        
        valid_focus = {"accuracy", "speed", "cost", "user_satisfaction", "stability", "prompt_effectiveness"}
        for focus in self.fitness_focus:
            if focus not in valid_focus:
                raise GeneError(f"未知优化重点: {focus}。有效值: {valid_focus}")
        
        if not isinstance(self.auto_evolution, bool):
            raise GeneError("auto_evolution必须是布尔值")
        
        if not isinstance(self.evolution_interval, int) or self.evolution_interval < 1:
            raise GeneError("evolution_interval必须是大于0的整数")
        
        return True 