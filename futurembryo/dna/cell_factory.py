"""
DNACellFactory - DNA驱动的Cell工厂

根据DNA配置动态创建和配置Cell组件
"""

import logging
from typing import Dict, List, Optional, Type, Any

from .embryo_dna import EmbryoDNA
from .exceptions import DNAError

# 导入核心Cell类型
from ..core.cell import Cell
from ..cells.llm_cell import LLMCell
from ..cells.state_memory_cell import StateMemoryCell


class DNACellFactory:
    """DNA驱动的Cell工厂类"""
    
    def __init__(self):
        """初始化Cell工厂"""
        self._logger = logging.getLogger("DNACellFactory")
        
        # Cell类型注册表
        self._cell_registry: Dict[str, Type[Cell]] = {
            "LLMCell": LLMCell,
            "StateMemoryCell": StateMemoryCell,
        }
        
        # 技能到Cell类型的映射
        self._skill_mapping = {
            "chat": "LLMCell",
            "knowledge": "StateMemoryCell", 
            "analyze": "LLMCell",
            "generate": "LLMCell",
            "search": "LLMCell",
            "tool_use": "LLMCell"
        }
    
    def register_cell_type(self, name: str, cell_class: Type[Cell]):
        """
        注册新的Cell类型
        
        Args:
            name: Cell类型名称
            cell_class: Cell类
        """
        self._cell_registry[name] = cell_class
        self._logger.info(f"注册Cell类型: {name}")
    
    def create_cell_from_skill(self, skill: str, dna: EmbryoDNA) -> Optional[Cell]:
        """
        根据技能创建Cell
        
        Args:
            skill: 技能名称
            dna: DNA配置
            
        Returns:
            创建的Cell实例
        """
        cell_type = self._skill_mapping.get(skill)
        if not cell_type:
            self._logger.warning(f"未知技能: {skill}")
            return None
        
        return self.create_cell(cell_type, dna, skill_context=skill)
    
    def create_cell(self, cell_type: str, dna: EmbryoDNA, skill_context: str = None) -> Optional[Cell]:
        """
        创建指定类型的Cell
        
        Args:
            cell_type: Cell类型名称
            dna: DNA配置
            skill_context: 技能上下文（可选）
            
        Returns:
            创建的Cell实例
        """
        cell_class = self._cell_registry.get(cell_type)
        if not cell_class:
            self._logger.warning(f"未注册的Cell类型: {cell_type}")
            return None
        
        try:
            # 根据Cell类型创建实例
            if cell_type == "LLMCell":
                return self._create_llm_cell(dna, skill_context)
            elif cell_type == "StateMemoryCell":
                return self._create_memory_cell(dna, skill_context)
            else:
                # 通用创建方法
                return self._create_generic_cell(cell_class, dna, skill_context)
                
        except Exception as e:
            self._logger.error(f"创建Cell失败 ({cell_type}): {e}")
            return None
    
    def _create_llm_cell(self, dna: EmbryoDNA, skill_context: str = None) -> LLMCell:
        """创建LLMCell"""
        behavior = dna.behavior
        
        # 根据技能上下文选择合适的系统提示词
        if skill_context:
            system_prompt = self._get_skill_prompt(skill_context, dna)
        else:
            system_prompt = behavior.system_prompt or behavior._generate_default_system_prompt()
        
        # 根据技能调整参数
        temperature, max_tokens = self._get_skill_parameters(skill_context)
        
        return LLMCell(
            model_name=dna.capability.models.get("llm", "gpt-3.5-turbo"),
            config={
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
    
    def _create_memory_cell(self, dna: EmbryoDNA, skill_context: str = None) -> StateMemoryCell:
        """创建StateMemoryCell"""
        namespace = f"{dna.name.lower()}_{skill_context or 'memory'}"
        
        return StateMemoryCell(
            config={
                "user_namespace": namespace,
                "openai_api_key": dna.capability.models.get("api_key"),
                "openai_base_url": dna.capability.models.get("base_url"),
                "embedding_model": dna.capability.models.get("embed", "text-embedding-3-large")
            }
        )
    
    def _create_generic_cell(self, cell_class: Type[Cell], dna: EmbryoDNA, skill_context: str = None) -> Cell:
        """创建通用Cell"""
        # 基础参数
        cell_params = {
            "name": f"{dna.name}_{skill_context or cell_class.__name__}"
        }
        
        # 根据Cell类型添加特定参数
        if hasattr(cell_class, "model"):
            cell_params["model"] = dna.capability.models.get("llm", "gpt-3.5-turbo")
        
        return cell_class(**cell_params)
    
    def _get_skill_prompt(self, skill: str, dna: EmbryoDNA) -> str:
        """根据技能获取专用提示词"""
        skill_prompts = {
            "chat": f"""你是{dna.name}，一个专业的对话助手。

核心特质：
- 性格特点：{', '.join(dna.behavior.personality)}
- 沟通风格：{dna.behavior.style}
- 使用语言：{dna.behavior.language}

请友好、专业地与用户对话，提供有价值的帮助。""",

            "analyze": f"""你是{dna.name}的分析专家，专门负责深度分析和洞察。

核心能力：
- 数据分析和模式识别
- 逻辑推理和因果分析  
- 趋势预测和建议生成

请以{dna.behavior.style}的风格进行分析，使用{dna.behavior.language}回答。""",

            "generate": f"""你是{dna.name}的创意生成专家，专门负责内容创作。

核心能力：
- 创意文案生成
- 结构化内容创作
- 多格式内容适配

风格特点：{', '.join(dna.behavior.personality)}
请以{dna.behavior.style}的风格创作，使用{dna.behavior.language}。""",

            "search": f"""你是{dna.name}的信息搜索专家，专门负责信息检索和整理。

核心能力：
- 信息搜索和过滤
- 结果排序和筛选
- 摘要生成和提取

请以{dna.behavior.style}的风格整理信息，使用{dna.behavior.language}。""",

            "tool_use": f"""你是{dna.name}的工具调用专家，专门负责工具集成和调用。

核心能力：
- 工具选择和调用
- 参数构建和验证
- 结果解析和整合

可用工具：{', '.join(dna.capability.tools)}
请以{dna.behavior.style}的风格使用工具，用{dna.behavior.language}解释结果。""",

            "knowledge": f"""你是{dna.name}的知识管理专家，专门负责知识存储和检索。

核心能力：
- 知识结构化存储
- 相似性检索和匹配
- 知识图谱构建

请以{dna.behavior.style}的风格管理知识，使用{dna.behavior.language}回答。"""
        }
        
        # 优先使用DNA配置的系统提示词，否则使用技能专用提示词
        if dna.behavior.system_prompt:
            return dna.behavior.system_prompt
        
        return skill_prompts.get(skill, dna.behavior._generate_default_system_prompt())
    
    def _get_skill_parameters(self, skill: str) -> tuple[float, int]:
        """根据技能获取模型参数"""
        skill_params = {
            "chat": (0.7, 2000),      # 平衡创造性和稳定性
            "analyze": (0.3, 3000),   # 更稳定，更长输出
            "generate": (0.8, 2500),  # 更有创造性
            "search": (0.2, 2000),    # 更精确
            "tool_use": (0.1, 1500),  # 最精确
            "knowledge": (0.5, 2000)  # 平衡
        }
        
        return skill_params.get(skill, (0.7, 2000))
    
    def get_supported_skills(self) -> List[str]:
        """获取支持的技能列表"""
        return list(self._skill_mapping.keys())
    
    def get_supported_cell_types(self) -> List[str]:
        """获取支持的Cell类型列表"""
        return list(self._cell_registry.keys())
    
    def get_factory_info(self) -> Dict[str, Any]:
        """获取工厂信息"""
        return {
            "supported_skills": self.get_supported_skills(),
            "supported_cell_types": self.get_supported_cell_types(),
            "skill_to_cell_mapping": self._skill_mapping
        } 