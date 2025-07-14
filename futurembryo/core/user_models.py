"""
用户数据模型 - FuturEmbryo框架用户相关数据结构

提供标准化的用户画像、偏好、记忆等数据模型
支持@引用系统和用户感知功能
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class UserProfile:
    """用户画像数据结构"""
    interests: List[str] = field(default_factory=list)           # 兴趣爱好
    expertise_areas: List[str] = field(default_factory=list)     # 专业领域  
    communication_style: str = "friendly"                        # 沟通风格
    detail_preference: str = "balanced"                          # 详细程度偏好: concise/balanced/detailed
    work_patterns: Dict[str, Any] = field(default_factory=dict)  # 工作模式
    demographics: Dict[str, Any] = field(default_factory=dict)   # 人口统计信息
    personality_traits: List[str] = field(default_factory=list)  # 性格特征
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """从字典创建用户画像"""
        return cls(**data)
    
    def update_interest(self, interest: str, add: bool = True):
        """更新兴趣"""
        if add and interest not in self.interests:
            self.interests.append(interest)
        elif not add and interest in self.interests:
            self.interests.remove(interest)
    
    def update_expertise(self, area: str, add: bool = True):
        """更新专业领域"""
        if add and area not in self.expertise_areas:
            self.expertise_areas.append(area)
        elif not add and area in self.expertise_areas:
            self.expertise_areas.remove(area)


@dataclass 
class UserMemoryEntry:
    """用户记忆条目"""
    content: str                                      # 记忆内容
    memory_type: str                                  # 记忆类型: explicit/learned/inferred
    importance: float                                 # 重要性 0-1
    timestamp: datetime                               # 时间戳
    context: Dict[str, Any] = field(default_factory=dict)  # 上下文信息
    tags: List[str] = field(default_factory=list)    # 标签
    access_count: int = 0                             # 访问次数
    last_accessed: Optional[datetime] = None         # 最后访问时间
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 处理datetime对象的序列化
        data['timestamp'] = self.timestamp.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserMemoryEntry':
        """从字典创建记忆条目"""
        # 处理datetime字段
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('last_accessed') and isinstance(data['last_accessed'], str):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)
    
    def access(self):
        """记录访问"""
        self.access_count += 1
        self.last_accessed = datetime.now()


@dataclass
class UserPreferences:
    """用户偏好数据结构"""
    communication_prefs: Dict[str, float] = field(default_factory=dict)  # 沟通偏好及权重
    content_prefs: Dict[str, float] = field(default_factory=dict)        # 内容偏好及权重
    agent_prefs: Dict[str, float] = field(default_factory=dict)          # Agent偏好及权重
    workflow_prefs: Dict[str, float] = field(default_factory=dict)       # 工作流偏好及权重
    output_format_prefs: Dict[str, float] = field(default_factory=dict)  # 输出格式偏好
    
    def learn_preference(self, category: str, preference: str, feedback: float):
        """学习用户偏好
        
        Args:
            category: 偏好类别 (communication/content/agent/workflow/output_format)
            preference: 具体偏好项
            feedback: 反馈值 0-1
        """
        prefs_attr = f"{category}_prefs"
        if not hasattr(self, prefs_attr):
            raise ValueError(f"未知的偏好类别: {category}")
        
        prefs_dict = getattr(self, prefs_attr)
        
        # 使用指数移动平均更新偏好权重
        alpha = 0.1  # 学习率
        current_weight = prefs_dict.get(preference, 0.5)
        new_weight = (1 - alpha) * current_weight + alpha * feedback
        
        # 确保权重在合理范围内
        prefs_dict[preference] = max(0.0, min(1.0, new_weight))
    
    def get_top_preferences(self, category: str, limit: int = 5) -> List[Tuple[str, float]]:
        """获取指定类别的TOP偏好
        
        Args:
            category: 偏好类别
            limit: 返回数量限制
            
        Returns:
            偏好列表，按权重降序排列
        """
        prefs_attr = f"{category}_prefs"
        if not hasattr(self, prefs_attr):
            return []
        
        prefs_dict = getattr(self, prefs_attr)
        sorted_prefs = sorted(prefs_dict.items(), key=lambda x: x[1], reverse=True)
        return sorted_prefs[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """从字典创建用户偏好"""
        return cls(**data)


@dataclass
class UserContext:
    """用户上下文信息聚合"""
    user_id: str
    profile: UserProfile = field(default_factory=UserProfile)
    preferences: UserPreferences = field(default_factory=UserPreferences)
    recent_memories: List[UserMemoryEntry] = field(default_factory=list)
    session_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "profile": self.profile.to_dict(),
            "preferences": self.preferences.to_dict(),
            "recent_memories": [memory.to_dict() for memory in self.recent_memories],
            "session_info": self.session_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserContext':
        """从字典创建用户上下文"""
        return cls(
            user_id=data["user_id"],
            profile=UserProfile.from_dict(data.get("profile", {})),
            preferences=UserPreferences.from_dict(data.get("preferences", {})),
            recent_memories=[
                UserMemoryEntry.from_dict(mem) 
                for mem in data.get("recent_memories", [])
            ],
            session_info=data.get("session_info", {})
        )
    
    def add_memory(self, content: str, memory_type: str = "explicit", 
                   importance: float = 0.5, context: Optional[Dict[str, Any]] = None,
                   tags: Optional[List[str]] = None):
        """添加记忆条目"""
        memory = UserMemoryEntry(
            content=content,
            memory_type=memory_type,
            importance=importance,
            timestamp=datetime.now(),
            context=context or {},
            tags=tags or []
        )
        self.recent_memories.append(memory)
        
        # 保持记忆数量在合理范围内
        if len(self.recent_memories) > 100:
            # 按重要性和时间排序，保留重要记忆
            self.recent_memories.sort(
                key=lambda x: (x.importance, x.timestamp), 
                reverse=True
            )
            self.recent_memories = self.recent_memories[:80]
    
    def get_context_summary(self) -> str:
        """获取用户上下文摘要"""
        summary_parts = []
        
        # 用户画像摘要
        if self.profile.interests:
            summary_parts.append(f"兴趣: {', '.join(self.profile.interests[:3])}")
        
        if self.profile.expertise_areas:
            summary_parts.append(f"专业领域: {', '.join(self.profile.expertise_areas[:3])}")
        
        summary_parts.append(f"沟通风格: {self.profile.communication_style}")
        summary_parts.append(f"详细程度偏好: {self.profile.detail_preference}")
        
        # 重要记忆
        important_memories = [
            mem for mem in self.recent_memories 
            if mem.importance > 0.7
        ][:3]
        
        if important_memories:
            memory_summary = "; ".join([mem.content[:50] + "..." 
                                      if len(mem.content) > 50 
                                      else mem.content 
                                      for mem in important_memories])
            summary_parts.append(f"重要记忆: {memory_summary}")
        
        return " | ".join(summary_parts)


# 工具函数
def create_user_context(user_id: str) -> UserContext:
    """创建新的用户上下文"""
    return UserContext(user_id=user_id)


def merge_user_contexts(primary: UserContext, secondary: UserContext) -> UserContext:
    """合并两个用户上下文"""
    # 合并兴趣和专业领域
    combined_interests = list(set(primary.profile.interests + secondary.profile.interests))
    combined_expertise = list(set(primary.profile.expertise_areas + secondary.profile.expertise_areas))
    
    # 创建合并后的画像
    merged_profile = UserProfile(
        interests=combined_interests,
        expertise_areas=combined_expertise,
        communication_style=primary.profile.communication_style,  # 以主要上下文为准
        detail_preference=primary.profile.detail_preference,
        work_patterns={**secondary.profile.work_patterns, **primary.profile.work_patterns},
        demographics={**secondary.profile.demographics, **primary.profile.demographics},
        personality_traits=list(set(primary.profile.personality_traits + secondary.profile.personality_traits))
    )
    
    # 合并记忆（去重并按时间排序）
    all_memories = primary.recent_memories + secondary.recent_memories
    unique_memories = []
    seen_contents = set()
    
    for memory in sorted(all_memories, key=lambda x: x.timestamp, reverse=True):
        if memory.content not in seen_contents:
            unique_memories.append(memory)
            seen_contents.add(memory.content)
    
    return UserContext(
        user_id=primary.user_id,
        profile=merged_profile,
        preferences=primary.preferences,  # 偏好以主要上下文为准
        recent_memories=unique_memories[:50],  # 保留最近50条
        session_info={**secondary.session_info, **primary.session_info}
    )