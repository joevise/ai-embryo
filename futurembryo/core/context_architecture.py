"""
上下文工程系统 - 数字生命的核心交互基础

所有系统交互的本质都是上下文的组装、传递和处理
"""

from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import uuid


class ContextType(Enum):
    """上下文类型"""
    IDENTITY = "identity"           # 身份相关上下文
    TASK = "task"                  # 任务相关上下文  
    USER = "user"                  # 用户相关上下文
    MEMORY = "memory"              # 记忆相关上下文
    COLLABORATION = "collaboration" # 协作相关上下文
    THINKING = "thinking"          # 思维相关上下文
    TOOL = "tool"                  # 工具相关上下文


@dataclass
class ContextUnit:
    """上下文单元 - 最小的上下文组成部分"""
    
    type: ContextType
    content: Any
    priority: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "content": self.content,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class AttentionController:
    """注意力控制器 - 管理注意力聚焦"""
    
    def __init__(self):
        self.focus_areas: List[str] = []
        self.priority_weights: Dict[str, float] = {}
        self.attention_history: List[Dict[str, Any]] = []
    
    def focus_on(self, areas: Union[str, List[str]], weights: Optional[Dict[str, float]] = None):
        """聚焦到特定区域"""
        if isinstance(areas, str):
            areas = [areas]
        
        self.focus_areas = areas
        if weights:
            self.priority_weights.update(weights)
        
        # 记录注意力变化
        self.attention_history.append({
            "timestamp": time.time(),
            "focus_areas": areas.copy(),
            "weights": weights.copy() if weights else {}
        })
    
    def calculate_attention_score(self, context_type: str, content: Any) -> float:
        """计算注意力分数"""
        base_score = 0.5
        
        # 如果在关注区域内，提高分数
        if context_type in self.focus_areas:
            base_score += 0.3
        
        # 应用权重
        weight = self.priority_weights.get(context_type, 1.0)
        return min(base_score * weight, 1.0)
    
    def get_current_focus(self) -> Dict[str, Any]:
        """获取当前注意力焦点"""
        return {
            "focus_areas": self.focus_areas.copy(),
            "priority_weights": self.priority_weights.copy(),
            "last_update": self.attention_history[-1]["timestamp"] if self.attention_history else None
        }


class ContextStructure:
    """可调整的上下文结构体 - 系统的核心"""
    
    def __init__(self, max_units: int = 100):
        """初始化上下文结构"""
        self.max_units = max_units
        self.units: Dict[str, ContextUnit] = {}
        self.structure_id = str(uuid.uuid4())
        self.created_at = time.time()
        self.last_modified = time.time()
        
        # 注意力控制
        self.attention_controller = AttentionController()
        
        # 结构化组织
        self.categories: Dict[ContextType, List[str]] = {
            context_type: [] for context_type in ContextType
        }
    
    def add_unit(self, unit_id: str, unit: ContextUnit):
        """添加上下文单元"""
        self.units[unit_id] = unit
        self.categories[unit.type].append(unit_id)
        self.last_modified = time.time()
        
        # 如果超出最大限制，移除最旧的
        if len(self.units) > self.max_units:
            self._cleanup_old_units()
    
    def remove_unit(self, unit_id: str):
        """移除上下文单元"""
        if unit_id in self.units:
            unit = self.units[unit_id]
            del self.units[unit_id]
            if unit_id in self.categories[unit.type]:
                self.categories[unit.type].remove(unit_id)
            self.last_modified = time.time()
    
    def get_unit(self, unit_id: str) -> Optional[ContextUnit]:
        """获取上下文单元"""
        return self.units.get(unit_id)
    
    def get_units_by_type(self, context_type: ContextType) -> List[ContextUnit]:
        """按类型获取上下文单元"""
        unit_ids = self.categories.get(context_type, [])
        return [self.units[uid] for uid in unit_ids if uid in self.units]
    
    def assemble(self, input_data: Any, assembly_strategy: str = "intelligent") -> Dict[str, Any]:
        """智能组装上下文"""
        
        if assembly_strategy == "intelligent":
            return self._intelligent_assembly(input_data)
        elif assembly_strategy == "priority_based":
            return self._priority_based_assembly(input_data)
        else:
            return self._simple_assembly(input_data)
    
    def _intelligent_assembly(self, input_data: Any) -> Dict[str, Any]:
        """智能组装策略"""
        assembled_context = {
            "input": input_data,
            "structure_id": self.structure_id,
            "assembled_at": time.time(),
            "components": {}
        }
        
        # 根据输入类型分析需要的上下文
        required_types = self._analyze_required_context_types(input_data)
        
        # 为每种类型收集相关上下文
        for context_type in required_types:
            units = self.get_units_by_type(context_type)
            if units:
                # 按优先级和注意力分数排序
                scored_units = []
                for unit in units:
                    attention_score = self.attention_controller.calculate_attention_score(
                        context_type.value, unit.content
                    )
                    total_score = (unit.priority + attention_score) / 2
                    scored_units.append((total_score, unit))
                
                # 取分数最高的单元
                scored_units.sort(key=lambda x: x[0], reverse=True)
                if scored_units:
                    best_unit = scored_units[0][1]
                    assembled_context["components"][context_type.value] = {
                        "content": best_unit.content,
                        "metadata": best_unit.metadata,
                        "score": scored_units[0][0]
                    }
        
        return assembled_context
    
    def _priority_based_assembly(self, input_data: Any) -> Dict[str, Any]:
        """基于优先级的组装策略"""
        assembled_context = {
            "input": input_data,
            "structure_id": self.structure_id,
            "assembled_at": time.time(),
            "components": {}
        }
        
        # 按优先级排序所有单元
        all_units = [(unit.priority, unit_id, unit) for unit_id, unit in self.units.items()]
        all_units.sort(key=lambda x: x[0], reverse=True)
        
        # 取前N个高优先级单元
        top_units = all_units[:10]  # 限制数量
        
        for priority, unit_id, unit in top_units:
            if unit.type.value not in assembled_context["components"]:
                assembled_context["components"][unit.type.value] = []
            
            assembled_context["components"][unit.type.value].append({
                "content": unit.content,
                "metadata": unit.metadata,
                "priority": priority
            })
        
        return assembled_context
    
    def _simple_assembly(self, input_data: Any) -> Dict[str, Any]:
        """简单组装策略"""
        return {
            "input": input_data,
            "structure_id": self.structure_id,
            "assembled_at": time.time(),
            "all_units": [unit.to_dict() for unit in self.units.values()]
        }
    
    def _analyze_required_context_types(self, input_data: Any) -> List[ContextType]:
        """分析输入需要哪些类型的上下文"""
        required_types = [ContextType.TASK]  # 任务上下文总是需要的
        
        # 简单的启发式分析
        if isinstance(input_data, dict):
            if "user" in str(input_data).lower():
                required_types.append(ContextType.USER)
            if "memory" in str(input_data).lower() or "remember" in str(input_data).lower():
                required_types.append(ContextType.MEMORY)
            if "think" in str(input_data).lower() or "analyze" in str(input_data).lower():
                required_types.append(ContextType.THINKING)
            if "tool" in str(input_data).lower() or "function" in str(input_data).lower():
                required_types.append(ContextType.TOOL)
        
        return required_types
    
    def restructure(self, mind_guidance: Dict[str, Any]):
        """根据思维系统指导重组上下文"""
        
        # 更新注意力焦点
        if "focus_areas" in mind_guidance:
            focus_areas = mind_guidance["focus_areas"]
            weights = mind_guidance.get("attention_weights", {})
            self.attention_controller.focus_on(focus_areas, weights)
        
        # 调整单元优先级
        if "priority_adjustments" in mind_guidance:
            for unit_id, new_priority in mind_guidance["priority_adjustments"].items():
                if unit_id in self.units:
                    self.units[unit_id].priority = new_priority
        
        # 移除不相关的单元
        if "remove_irrelevant" in mind_guidance and mind_guidance["remove_irrelevant"]:
            self._remove_low_priority_units()
        
        self.last_modified = time.time()
    
    def _remove_low_priority_units(self, threshold: float = 0.2):
        """移除低优先级单元"""
        to_remove = []
        for unit_id, unit in self.units.items():
            if unit.priority < threshold:
                to_remove.append(unit_id)
        
        for unit_id in to_remove:
            self.remove_unit(unit_id)
    
    def _cleanup_old_units(self):
        """清理旧的单元"""
        # 按时间戳排序，移除最旧的单元
        units_by_time = [(unit.timestamp, unit_id) for unit_id, unit in self.units.items()]
        units_by_time.sort()
        
        # 移除最旧的单元，直到数量在限制内
        while len(self.units) > self.max_units and units_by_time:
            _, unit_id = units_by_time.pop(0)
            self.remove_unit(unit_id)
    
    def merge_context(self, other_context: Dict[str, Any]):
        """合并外部上下文"""
        if "components" in other_context:
            for context_type, content in other_context["components"].items():
                unit_id = f"merged_{context_type}_{int(time.time())}"
                unit = ContextUnit(
                    type=ContextType(context_type),
                    content=content,
                    priority=0.7,  # 合并的上下文给予中等优先级
                    metadata={"source": "external_merge"}
                )
                self.add_unit(unit_id, unit)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取上下文结构摘要"""
        type_counts = {}
        for context_type in ContextType:
            count = len(self.categories[context_type])
            if count > 0:
                type_counts[context_type.value] = count
        
        return {
            "structure_id": self.structure_id,
            "total_units": len(self.units),
            "type_distribution": type_counts,
            "attention_focus": self.attention_controller.get_current_focus(),
            "created_at": self.created_at,
            "last_modified": self.last_modified
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "structure_id": self.structure_id,
            "units": {uid: unit.to_dict() for uid, unit in self.units.items()},
            "categories": {ct.value: uids for ct, uids in self.categories.items()},
            "attention_focus": self.attention_controller.get_current_focus(),
            "created_at": self.created_at,
            "last_modified": self.last_modified
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"ContextStructure(units={len(self.units)}, focus={self.attention_controller.focus_areas})"


class ContextArchitectureManager:
    """上下文架构管理器 - 管理多个上下文结构"""
    
    def __init__(self):
        self.structures: Dict[str, ContextStructure] = {}
        self.default_structure_id: Optional[str] = None
    
    def create_structure(self, structure_id: Optional[str] = None, max_units: int = 100) -> str:
        """创建新的上下文结构"""
        if structure_id is None:
            structure_id = f"context_{int(time.time())}_{len(self.structures)}"
        
        structure = ContextStructure(max_units)
        self.structures[structure_id] = structure
        
        if self.default_structure_id is None:
            self.default_structure_id = structure_id
        
        return structure_id
    
    def get_structure(self, structure_id: Optional[str] = None) -> Optional[ContextStructure]:
        """获取上下文结构"""
        if structure_id is None:
            structure_id = self.default_structure_id
        
        return self.structures.get(structure_id)
    
    def remove_structure(self, structure_id: str):
        """移除上下文结构"""
        if structure_id in self.structures:
            del self.structures[structure_id]
            
            if self.default_structure_id == structure_id:
                self.default_structure_id = next(iter(self.structures.keys())) if self.structures else None
    
    def get_all_structures(self) -> Dict[str, ContextStructure]:
        """获取所有上下文结构"""
        return self.structures.copy()
    
    def get_manager_summary(self) -> Dict[str, Any]:
        """获取管理器摘要"""
        return {
            "total_structures": len(self.structures),
            "default_structure": self.default_structure_id,
            "structures": {sid: struct.get_summary() for sid, struct in self.structures.items()}
        }