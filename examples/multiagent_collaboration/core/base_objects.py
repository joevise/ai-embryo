"""
基础对象模型 - 所有可@引用对象的基类

实现统一的对象引用系统，支持五大对象类型：
1. 用户对象 (User Objects) - 用户画像、记忆、偏好
2. 智能体对象 (Agent Objects) - 独立的AI智能体
3. 工作流对象 (Workflow Objects) - 可执行的协作流程
4. 数据对象 (Data Objects) - 文件、知识库等数据
5. 产出物对象 (Deliverable Objects) - AI生成的成果
"""

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


class ObjectType(Enum):
    """对象类型枚举"""
    USER = "user"           # 用户对象
    AGENT = "agent"         # 智能体对象
    WORKFLOW = "workflow"   # 工作流对象
    DATA = "data"           # 数据对象
    DELIVERABLE = "deliverable"  # 产出物对象


@dataclass
class BaseObject(ABC):
    """所有可@引用对象的基类"""
    
    id: str                           # @引用ID (唯一标识)
    name: str                         # 显示名称
    description: str                  # 描述信息
    object_type: ObjectType           # 对象类型
    created_at: datetime              # 创建时间
    updated_at: datetime              # 更新时间
    metadata: Dict[str, Any]          # 扩展元数据
    tags: List[str]                   # 标签列表
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = self._generate_id()
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()
        if not self.metadata:
            self.metadata = {}
        if not self.tags:
            self.tags = []
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"{self.object_type.value}_{uuid.uuid4().hex[:8]}"
    
    def to_mention_format(self) -> str:
        """转换为@引用格式"""
        return f"@{self.id}"
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取显示信息（用于@提及时的展示）"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.object_type.value,
            "mention": self.to_mention_format(),
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "object_type": self.object_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "tags": self.tags
        }
    
    def update_metadata(self, key: str, value: Any):
        """更新元数据"""
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str):
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str):
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def matches_search(self, query: str) -> bool:
        """检查是否匹配搜索查询"""
        query_lower = query.lower()
        return (
            query_lower in self.id.lower() or
            query_lower in self.name.lower() or
            query_lower in self.description.lower() or
            any(query_lower in tag.lower() for tag in self.tags)
        )
    
    @abstractmethod
    def handle_mention(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理被@引用时的行为
        
        Args:
            context: 引用上下文，包含：
                - user_input: 用户输入
                - conversation_history: 对话历史
                - mentioned_objects: 本次提及的其他对象
                - platform: 协作平台实例
                
        Returns:
            Dict: 处理结果，包含：
                - success: 是否成功
                - data: 返回数据
                - message: 状态消息
                - generated_objects: 新生成的对象（如产出物）
        """
        pass
    
    @abstractmethod
    def get_context_info(self) -> Dict[str, Any]:
        """
        获取上下文信息（供其他对象使用）
        
        Returns:
            Dict: 上下文信息
        """
        pass
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        验证对象有效性
        
        Returns:
            tuple: (是否有效, 错误消息列表)
        """
        errors = []
        
        if not self.id or not self.id.strip():
            errors.append("ID不能为空")
            
        if not self.name or not self.name.strip():
            errors.append("名称不能为空")
            
        return len(errors) == 0, errors


class ObjectMetrics:
    """对象度量信息"""
    
    def __init__(self, obj: BaseObject):
        self.object_id = obj.id
        self.mention_count = 0          # 被@引用次数
        self.last_mentioned = None      # 最后被引用时间
        self.success_rate = 1.0         # 成功处理率
        self.avg_response_time = 0.0    # 平均响应时间
        self.user_satisfaction = 0.0    # 用户满意度
        
    def record_mention(self, success: bool = True, response_time: float = 0.0):
        """记录一次引用"""
        self.mention_count += 1
        self.last_mentioned = datetime.now()
        
        # 更新成功率（简单移动平均）
        if self.mention_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            alpha = 0.1  # 平滑因子
            self.success_rate = (1 - alpha) * self.success_rate + alpha * (1.0 if success else 0.0)
        
        # 更新响应时间
        if response_time > 0:
            if self.avg_response_time == 0:
                self.avg_response_time = response_time
            else:
                alpha = 0.1
                self.avg_response_time = (1 - alpha) * self.avg_response_time + alpha * response_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "object_id": self.object_id,
            "mention_count": self.mention_count,
            "last_mentioned": self.last_mentioned.isoformat() if self.last_mentioned else None,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "user_satisfaction": self.user_satisfaction
        }


# 便捷函数
def create_base_object(obj_type: ObjectType, name: str, description: str = "", 
                      obj_id: str = None, tags: List[str] = None) -> Dict[str, Any]:
    """创建基础对象配置"""
    return {
        "id": obj_id or f"{obj_type.value}_{uuid.uuid4().hex[:8]}",
        "name": name,
        "description": description,
        "object_type": obj_type,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "metadata": {},
        "tags": tags or []
    }