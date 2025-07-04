"""
EmbryoDNA核心类 - AI生命体的遗传密码

从配置文件加载并验证DNA，定义如何从细胞成长为完整智能体
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import asdict

from .genes import PurposeGene, CapabilityGene, StructureGene, BehaviorGene, EvolutionGene
from .exceptions import DNAError, DNAValidationError, DNALoadError, DNAParseError


class EmbryoDNA:
    """AI胚胎的DNA配置 - 定义如何从细胞成长为完整智能体"""
    
    def __init__(self, 
                 name: str = "unnamed_ai",
                 version: str = "1.0.0",
                 description: str = "",
                 purpose: Optional[PurposeGene] = None,
                 capability: Optional[CapabilityGene] = None,
                 structure: Optional[StructureGene] = None,
                 behavior: Optional[BehaviorGene] = None,
                 evolution: Optional[EvolutionGene] = None):
        """
        初始化EmbryoDNA
        
        Args:
            name: AI系统名称
            version: 版本号
            description: 系统描述
            purpose: 目标基因
            capability: 能力基因
            structure: 结构基因
            behavior: 行为基因
            evolution: 进化基因
        """
        self.name = name
        self.version = version
        self.description = description
        
        # 初始化五种基因（如果未提供则使用默认值）
        self.purpose = purpose or PurposeGene(goal="通用AI助手")
        self.capability = capability or CapabilityGene()
        self.structure = structure or StructureGene()
        self.behavior = behavior or BehaviorGene()
        self.evolution = evolution or EvolutionGene()
        
        # 验证DNA完整性
        self.validate()
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'EmbryoDNA':
        """
        从YAML/JSON文件加载DNA配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            EmbryoDNA实例
            
        Raises:
            DNALoadError: 文件加载失败
            DNAParseError: 配置解析失败
            DNAValidationError: 配置验证失败
        """
        config_path = Path(config_path)
        
        # 检查文件是否存在
        if not config_path.exists():
            raise DNALoadError(f"配置文件不存在: {config_path}")
        
        try:
            # 根据文件扩展名选择解析器
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise DNAParseError(f"不支持的文件格式: {config_path.suffix}")
        
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise DNAParseError(f"配置文件解析失败: {e}")
        except Exception as e:
            raise DNALoadError(f"读取配置文件失败: {e}")
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'EmbryoDNA':
        """
        从字典创建DNA配置
        
        Args:
            config_data: 配置字典
            
        Returns:
            EmbryoDNA实例
            
        Raises:
            DNAParseError: 配置解析失败
        """
        try:
            # 基础信息
            name = config_data.get("name", "unnamed_ai")
            version = config_data.get("version", "1.0.0")
            description = config_data.get("description", "")
            
            # 解析各个基因
            purpose_data = config_data.get("purpose", {})
            capability_data = config_data.get("capability", {})
            structure_data = config_data.get("structure", {})
            behavior_data = config_data.get("behavior", {})
            evolution_data = config_data.get("evolution", {})
            
            # 创建基因实例
            purpose = PurposeGene(
                goal=purpose_data.get("goal", "通用AI助手"),
                metrics=purpose_data.get("metrics", []),
                constraints=purpose_data.get("constraints", [])
            )
            
            capability = CapabilityGene(
                skills=capability_data.get("skills"),
                models=capability_data.get("models"),
                tools=capability_data.get("tools")
            )
            
            structure = StructureGene(
                cell_types=structure_data.get("cell_types"),
                architecture=structure_data.get("architecture", "pipeline"),
                max_complexity=structure_data.get("max_complexity", 5),
                auto_scale=structure_data.get("auto_scale", True)
            )
            
            behavior = BehaviorGene(
                personality=behavior_data.get("personality"),
                style=behavior_data.get("style", "friendly_professional"),
                language=behavior_data.get("language", "zh-CN"),
                safety=behavior_data.get("safety"),
                system_prompt=behavior_data.get("system_prompt", ""),
                user_prompt_template=behavior_data.get("user_prompt_template", ""),
                context_prompt=behavior_data.get("context_prompt", ""),
                output_format_prompt=behavior_data.get("output_format_prompt", ""),
                prompt_variables=behavior_data.get("prompt_variables")
            )
            
            evolution = EvolutionGene(
                enabled=evolution_data.get("enabled", True),
                learn_rate=evolution_data.get("learn_rate", 0.5),
                adapt_speed=evolution_data.get("adapt_speed", "normal"),
                mutation_rate=evolution_data.get("mutation_rate", 0.1),
                fitness_focus=evolution_data.get("fitness_focus"),
                auto_evolution=evolution_data.get("auto_evolution", True),
                evolution_interval=evolution_data.get("evolution_interval", 3600)
            )
            
            return cls(
                name=name,
                version=version,
                description=description,
                purpose=purpose,
                capability=capability,
                structure=structure,
                behavior=behavior,
                evolution=evolution
            )
            
        except Exception as e:
            raise DNAParseError(f"DNA配置解析失败: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            配置字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "purpose": asdict(self.purpose),
            "capability": asdict(self.capability),
            "structure": asdict(self.structure),
            "behavior": asdict(self.behavior),
            "evolution": asdict(self.evolution)
        }
    
    def to_yaml(self, output_path: Optional[Union[str, Path]] = None) -> str:
        """
        转换为YAML格式
        
        Args:
            output_path: 可选的输出文件路径
            
        Returns:
            YAML字符串
        """
        yaml_content = yaml.dump(
            self.to_dict(), 
            default_flow_style=False, 
            allow_unicode=True,
            indent=2
        )
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
        
        return yaml_content
    
    def validate(self) -> bool:
        """
        验证DNA配置有效性
        
        Returns:
            验证是否通过
            
        Raises:
            DNAValidationError: 验证失败
        """
        try:
            # 验证基础信息
            if not isinstance(self.name, str) or not self.name.strip():
                raise DNAValidationError("name必须是非空字符串")
            
            if not isinstance(self.version, str) or not self.version.strip():
                raise DNAValidationError("version必须是非空字符串")
            
            # 验证各个基因
            self.purpose.validate()
            self.capability.validate()
            self.structure.validate()
            self.behavior.validate()
            self.evolution.validate()
            
            # 跨基因验证
            self._cross_validate()
            
            return True
            
        except Exception as e:
            if isinstance(e, DNAValidationError):
                raise e
            else:
                raise DNAValidationError(f"DNA验证失败: {e}")
    
    def _cross_validate(self):
        """跨基因验证 - 检查基因间的一致性"""
        
        # 验证技能和Cell类型的一致性
        skills = set(self.capability.skills)
        
        # 如果有search技能，建议包含SearchCell
        if "search" in skills and "SearchCell" not in self.structure.cell_types:
            # 这里不抛出错误，而是记录警告
            pass
        
        # 如果有knowledge技能，建议包含StateMemoryCell
        if "knowledge" in skills and "StateMemoryCell" not in self.structure.cell_types:
            pass
        
        # 验证架构复杂度
        if len(self.structure.cell_types) > self.structure.max_complexity:
            raise DNAValidationError(
                f"Cell类型数量({len(self.structure.cell_types)}) "
                f"超过最大复杂度({self.structure.max_complexity})"
            )
    
    def summary(self) -> str:
        """
        生成DNA摘要信息
        
        Returns:
            摘要字符串
        """
        return f"""
🧬 EmbryoDNA摘要：{self.name} v{self.version}

📋 目标：{self.purpose.goal}
🎯 指标：{len(self.purpose.metrics)}个性能指标
⚠️  约束：{len(self.purpose.constraints)}个约束条件

🛠️  技能：{', '.join(self.capability.skills)}
🤖 模型：{self.capability.models.get('llm', '未指定')}
🔧 工具：{len(self.capability.tools)}个工具

🏗️  架构：{self.structure.architecture}
📦 细胞：{len(self.structure.cell_types)}种类型
📊 复杂度：{self.structure.max_complexity}

😊 性格：{', '.join(self.behavior.personality)}
🗣️  风格：{self.behavior.style}
🌐 语言：{self.behavior.language}

🧬 进化：{'启用' if self.evolution.enabled else '禁用'}
⚡ 学习率：{self.evolution.learn_rate}
🎯 优化重点：{', '.join(self.evolution.fitness_focus)}
        """.strip()
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"EmbryoDNA(name='{self.name}', version='{self.version}')"
    
    def __repr__(self) -> str:
        """详细表示"""
        return f"EmbryoDNA(name='{self.name}', version='{self.version}', skills={self.capability.skills})" 