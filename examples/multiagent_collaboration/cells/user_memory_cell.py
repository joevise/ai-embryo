"""
UserMemoryCell - 用户记忆Cell

基于FuturEmbryo的StateMemoryCell扩展，添加用户画像、偏好学习、显式记忆等功能
支持@user-profile、@user-memory、@user-preferences等对象引用
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from futurembryo.core.cell import Cell
from futurembryo.core.exceptions import CellConfigurationError


@dataclass
class UserProfile:
    """用户画像数据结构"""
    interests: List[str] = None           # 兴趣爱好
    expertise_areas: List[str] = None     # 专业领域  
    communication_style: str = "friendly" # 沟通风格
    detail_preference: str = "balanced"   # 详细程度偏好: concise/balanced/detailed
    work_patterns: Dict[str, Any] = None  # 工作模式
    demographics: Dict[str, Any] = None   # 人口统计信息
    personality_traits: List[str] = None  # 性格特征
    
    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.expertise_areas is None:
            self.expertise_areas = []
        if self.work_patterns is None:
            self.work_patterns = {}
        if self.demographics is None:
            self.demographics = {}
        if self.personality_traits is None:
            self.personality_traits = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class UserMemoryEntry:
    """用户记忆条目"""
    content: str                      # 记忆内容
    memory_type: str                  # 记忆类型: explicit/learned/inferred
    importance: float                 # 重要性 0-1
    timestamp: datetime               # 时间戳
    context: Dict[str, Any]           # 上下文信息
    tags: List[str] = None            # 标签
    access_count: int = 0             # 访问次数
    last_accessed: datetime = None    # 最后访问时间
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = self.timestamp


@dataclass
class UserPreferences:
    """用户偏好数据结构"""
    communication_prefs: Dict[str, float] = None  # 沟通偏好及权重
    content_prefs: Dict[str, float] = None        # 内容偏好及权重
    agent_prefs: Dict[str, float] = None          # Agent偏好及权重
    workflow_prefs: Dict[str, float] = None       # 工作流偏好及权重
    output_format_prefs: Dict[str, float] = None  # 输出格式偏好
    
    def __post_init__(self):
        if self.communication_prefs is None:
            self.communication_prefs = {}
        if self.content_prefs is None:
            self.content_prefs = {}
        if self.agent_prefs is None:
            self.agent_prefs = {}
        if self.workflow_prefs is None:
            self.workflow_prefs = {}
        if self.output_format_prefs is None:
            self.output_format_prefs = {}
    
    def learn_preference(self, category: str, preference: str, feedback: float):
        """学习用户偏好"""
        prefs_dict = getattr(self, f"{category}_prefs", {})
        
        # 使用指数移动平均更新偏好权重
        alpha = 0.1  # 学习率
        current_weight = prefs_dict.get(preference, 0.5)
        new_weight = (1 - alpha) * current_weight + alpha * feedback
        
        # 确保权重在合理范围内
        prefs_dict[preference] = max(0.0, min(1.0, new_weight))
        setattr(self, f"{category}_prefs", prefs_dict)
    
    def get_preference_score(self, category: str, preference: str) -> float:
        """获取偏好分数"""
        prefs_dict = getattr(self, f"{category}_prefs", {})
        return prefs_dict.get(preference, 0.5)  # 默认中性偏好
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UserMemoryCell(Cell):
    """
    用户记忆Cell - 扩展StateMemoryCell
    
    新增功能：
    1. 用户画像管理 (@user-profile)
    2. 显式记忆存储 (@user-memory) 
    3. 偏好学习系统 (@user-preferences)
    4. @引用处理机制
    5. 自动上下文感知
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化用户记忆Cell
        
        Args:
            config: 配置字典，在StateMemoryCell基础上新增：
                - user_profile_collection: 用户画像集合名
                - user_memory_collection: 用户记忆集合名  
                - user_preferences_collection: 用户偏好集合名
                - auto_learning: 是否自动学习用户偏好
                - explicit_memory_keywords: 触发显式记忆的关键词
                - profile_update_threshold: 画像更新阈值
                - memory_retention_days: 记忆保留天数
        """
        # 准备基础Cell配置，暂时不继承StateMemoryCell以避免适配器依赖
        if config is None:
            config = {}
        
        # 初始化为基础Cell而不是StateMemoryCell，避免适配器配置问题
        Cell.__init__(self, config)
        
        # 简单的本地存储字典，用于演示
        self.local_storage = {
            "user_profile": {},
            "user_preferences": {},
            "user_memories": []
        }
        
        # 用户记忆相关配置
        self.user_profile_collection = self.config.get("user_profile_collection", "user_profile")
        self.user_memory_collection = self.config.get("user_memory_collection", "user_memory") 
        self.user_preferences_collection = self.config.get("user_preferences_collection", "user_preferences")
        
        self.auto_learning = self.config.get("auto_learning", True)
        self.explicit_memory_keywords = self.config.get("explicit_memory_keywords", [
            "记住", "记录", "重要", "注意", "保存", "记下来"
        ])
        self.profile_update_threshold = self.config.get("profile_update_threshold", 0.1)
        self.memory_retention_days = self.config.get("memory_retention_days", 365)
        
        # 用户数据
        self.user_profile = UserProfile()
        self.user_preferences = UserPreferences()
        self.user_memories: List[UserMemoryEntry] = []
        
        # 加载已有用户数据
        self._load_user_data()
        
        self.logger.info("UserMemoryCell initialized with user-aware capabilities")
    
    def _load_user_data(self):
        """加载已有的用户数据（使用简单本地存储）"""
        try:
            # 从本地存储加载用户画像
            if self.local_storage["user_profile"]:
                profile_data = self.local_storage["user_profile"]
                self.user_profile = UserProfile(**profile_data)
            
            # 从本地存储加载用户偏好
            if self.local_storage["user_preferences"]:
                prefs_data = self.local_storage["user_preferences"]
                self.user_preferences = UserPreferences(**prefs_data)
            
            # 从本地存储加载用户记忆
            for memory_data in self.local_storage["user_memories"]:
                memory_entry = UserMemoryEntry(
                    content=memory_data.get("content", ""),
                    memory_type=memory_data.get("memory_type", "learned"),
                    importance=memory_data.get("importance", 0.5),
                    timestamp=datetime.fromisoformat(memory_data.get("timestamp", datetime.now().isoformat())),
                    context=memory_data.get("context", {}),
                    tags=memory_data.get("tags", [])
                )
                self.user_memories.append(memory_entry)
                
            self.logger.info(f"Loaded user data: profile={bool(self.local_storage['user_profile'])}, "
                           f"preferences={bool(self.local_storage['user_preferences'])}, "
                           f"memories={len(self.user_memories)}")
                           
        except Exception as e:
            self.logger.warning(f"Failed to load existing user data: {e}")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户记忆操作，扩展StateMemoryCell的process方法
        
        新增action类型：
        - get_user_profile: 获取用户画像
        - update_user_profile: 更新用户画像
        - get_user_preferences: 获取用户偏好
        - learn_preference: 学习用户偏好
        - add_user_memory: 添加用户记忆
        - get_user_memories: 获取用户记忆
        - process_user_input: 处理用户输入（自动学习）
        - handle_mention: 处理@引用
        """
        action = context.get("action", "search")
        
        # 用户记忆相关操作
        if action == "get_user_profile":
            return self._get_user_profile(context)
        elif action == "update_user_profile":
            return self._update_user_profile(context)
        elif action == "get_user_preferences":
            return self._get_user_preferences(context)
        elif action == "learn_preference":
            return self._learn_preference(context)
        elif action == "add_user_memory":
            return self._add_user_memory(context)
        elif action == "get_user_memories":
            return self._get_user_memories(context)
        elif action == "process_user_input":
            return self._process_user_input(context)
        elif action == "handle_mention":
            return self._handle_mention(context)
        else:
            # 调用父类的process方法处理其他操作
            return super().process(context)
    
    def _get_user_profile(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户画像"""
        return {
            "success": True,
            "data": {
                "profile": self.user_profile.to_dict(),
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _update_user_profile(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户画像"""
        updates = context.get("updates", {})
        
        try:
            # 更新画像字段
            for field, value in updates.items():
                if hasattr(self.user_profile, field):
                    if isinstance(getattr(self.user_profile, field), list):
                        # 列表字段：合并去重
                        current_list = getattr(self.user_profile, field)
                        if isinstance(value, list):
                            new_list = list(set(current_list + value))
                        else:
                            new_list = list(set(current_list + [value]))
                        setattr(self.user_profile, field, new_list)
                    else:
                        # 其他字段：直接设置
                        setattr(self.user_profile, field, value)
            
            # 保存到记忆库
            self._save_user_profile()
            
            return {
                "success": True,
                "data": {
                    "updated_fields": list(updates.keys()),
                    "profile": self.user_profile.to_dict()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update user profile: {str(e)}"
            }
    
    def _get_user_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户偏好"""
        category = context.get("category")  # 可选：指定偏好类别
        
        if category:
            prefs_dict = getattr(self.user_preferences, f"{category}_prefs", {})
            return {
                "success": True,
                "data": {
                    "category": category,
                    "preferences": prefs_dict
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "preferences": self.user_preferences.to_dict()
                }
            }
    
    def _learn_preference(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """学习用户偏好"""
        category = context.get("category")  # 偏好类别
        preference = context.get("preference")  # 偏好项
        feedback = context.get("feedback", 0.7)  # 反馈分数 0-1
        
        if not category or not preference:
            return {
                "success": False,
                "error": "Category and preference are required"
            }
        
        try:
            # 学习偏好
            self.user_preferences.learn_preference(category, preference, feedback)
            
            # 保存偏好
            self._save_user_preferences()
            
            return {
                "success": True,
                "data": {
                    "category": category,
                    "preference": preference,
                    "new_score": self.user_preferences.get_preference_score(category, preference)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to learn preference: {str(e)}"
            }
    
    def _add_user_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """添加用户记忆"""
        content = context.get("content")
        memory_type = context.get("memory_type", "learned")  # explicit/learned/inferred
        importance = context.get("importance", 0.5)
        memory_context = context.get("context", {})
        tags = context.get("tags", [])
        
        if not content:
            return {
                "success": False,
                "error": "Content is required"
            }
        
        try:
            # 创建记忆条目
            memory_entry = UserMemoryEntry(
                content=content,
                memory_type=memory_type,
                importance=importance,
                timestamp=datetime.now(),
                context=memory_context,
                tags=tags
            )
            
            # 添加到内存
            self.user_memories.append(memory_entry)
            
            # 保存到记忆库
            self._save_user_memory(memory_entry)
            
            return {
                "success": True,
                "data": {
                    "memory_id": len(self.user_memories) - 1,
                    "content": content,
                    "memory_type": memory_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add user memory: {str(e)}"
            }
    
    def _get_user_memories(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户记忆"""
        memory_type = context.get("memory_type")  # 可选：筛选记忆类型
        tags = context.get("tags", [])  # 可选：按标签筛选
        limit = context.get("limit", 20)
        
        # 筛选记忆
        filtered_memories = self.user_memories
        
        if memory_type:
            filtered_memories = [m for m in filtered_memories if m.memory_type == memory_type]
        
        if tags:
            filtered_memories = [m for m in filtered_memories 
                               if any(tag in m.tags for tag in tags)]
        
        # 按重要性和时间排序
        filtered_memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        # 限制数量
        filtered_memories = filtered_memories[:limit]
        
        return {
            "success": True,
            "data": {
                "memories": [
                    {
                        "content": m.content,
                        "memory_type": m.memory_type,
                        "importance": m.importance,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags
                    }
                    for m in filtered_memories
                ],
                "total_count": len(self.user_memories),
                "filtered_count": len(filtered_memories)
            }
        }
    
    def _process_user_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户输入，自动学习用户信息"""
        user_input = context.get("user_input", "")
        conversation_context = context.get("conversation_context", {})
        
        results = {
            "profile_updates": [],
            "new_memories": [],
            "learned_preferences": []
        }
        
        try:
            # 1. 检测显式记忆请求
            if self._detect_explicit_memory_request(user_input):
                memory_content = self._extract_memory_content(user_input)
                if memory_content:
                    memory_result = self._add_user_memory({
                        "content": memory_content,
                        "memory_type": "explicit",
                        "importance": 0.9,
                        "context": conversation_context
                    })
                    if memory_result["success"]:
                        results["new_memories"].append(memory_content)
            
            # 2. 分析并更新用户画像
            profile_updates = self._analyze_user_input_for_profile(user_input)
            if profile_updates:
                update_result = self._update_user_profile({"updates": profile_updates})
                if update_result["success"]:
                    results["profile_updates"] = list(profile_updates.keys())
            
            # 3. 如果启用自动学习，分析用户偏好
            if self.auto_learning:
                preference_signals = self._analyze_preference_signals(user_input, conversation_context)
                for signal in preference_signals:
                    pref_result = self._learn_preference(signal)
                    if pref_result["success"]:
                        results["learned_preferences"].append(signal)
            
            return {
                "success": True,
                "data": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process user input: {str(e)}",
                "data": results
            }
    
    def _handle_mention(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理@引用"""
        mention = context.get("mention", "")
        mention_context = context.get("context", {})
        
        # 支持的@引用类型
        if mention in ["user-profile", "profile"]:
            return self._get_user_profile(mention_context)
        elif mention in ["user-preferences", "preferences"]:
            return self._get_user_preferences(mention_context)
        elif mention in ["user-memory", "memory"]:
            return self._get_user_memories(mention_context)
        elif mention.startswith("user-memory-"):
            # 特定类型的记忆：@user-memory-explicit
            memory_type = mention.split("-")[-1]
            return self._get_user_memories({**mention_context, "memory_type": memory_type})
        else:
            return {
                "success": False,
                "error": f"Unsupported mention: @{mention}"
            }
    
    # 辅助方法
    def _detect_explicit_memory_request(self, text: str) -> bool:
        """检测用户是否明确要求记录信息"""
        return any(keyword in text for keyword in self.explicit_memory_keywords)
    
    def _extract_memory_content(self, text: str) -> str:
        """提取需要记录的内容"""
        # 简单的内容提取逻辑，可以改进为更智能的NLP处理
        for keyword in self.explicit_memory_keywords:
            if keyword in text:
                parts = text.split(keyword, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return text
    
    def _analyze_user_input_for_profile(self, text: str) -> Dict[str, Any]:
        """分析用户输入，提取画像信息"""
        updates = {}
        
        # 检测兴趣关键词
        interest_patterns = [
            r"我(对|喜欢|感兴趣)(.+?)(?:很|非常|特别)?(感兴趣|喜欢|关注)",
            r"我(关注|研究|从事)(.+?)领域",
            r"我是(.+?)方面的专家",
        ]
        
        for pattern in interest_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    interest = match[1].strip()
                    if interest and len(interest) < 20:  # 避免过长的匹配
                        if "interests" not in updates:
                            updates["interests"] = []
                        updates["interests"].append(interest)
        
        # 检测沟通风格偏好
        style_patterns = {
            "简洁": ["简洁", "简单", "直接", "不要太详细"],
            "详细": ["详细", "具体", "深入", "全面"],
            "友好": ["友好", "亲切", "温和"],
            "专业": ["专业", "正式", "严谨"]
        }
        
        for style, keywords in style_patterns.items():
            if any(keyword in text for keyword in keywords):
                updates["communication_style"] = style.lower()
                break
        
        return updates
    
    def _analyze_preference_signals(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析偏好信号"""
        signals = []
        
        # 检测满意度信号
        positive_signals = ["很好", "不错", "满意", "喜欢", "正是我要的"]
        negative_signals = ["太复杂", "太简单", "不够", "太多", "不喜欢"]
        
        for signal in positive_signals:
            if signal in text:
                signals.append({
                    "category": "communication",
                    "preference": context.get("last_style", "balanced"),
                    "feedback": 0.8
                })
                break
        
        for signal in negative_signals:
            if signal in text:
                signals.append({
                    "category": "communication", 
                    "preference": context.get("last_style", "balanced"),
                    "feedback": 0.2
                })
                break
        
        return signals
    
    def _save_user_profile(self):
        """保存用户画像到本地存储"""
        try:
            self.local_storage["user_profile"] = self.user_profile.to_dict()
            self.logger.debug("User profile saved to local storage")
        except Exception as e:
            self.logger.error(f"Failed to save user profile: {e}")
    
    def _save_user_preferences(self):
        """保存用户偏好到本地存储"""
        try:
            self.local_storage["user_preferences"] = self.user_preferences.to_dict()
            self.logger.debug("User preferences saved to local storage")
        except Exception as e:
            self.logger.error(f"Failed to save user preferences: {e}")
    
    def _save_user_memory(self, memory_entry: UserMemoryEntry):
        """保存单个用户记忆到本地存储"""
        try:
            memory_data = {
                "content": memory_entry.content,
                "memory_type": memory_entry.memory_type,
                "importance": memory_entry.importance,
                "timestamp": memory_entry.timestamp.isoformat(),
                "context": memory_entry.context,
                "tags": memory_entry.tags
            }
            
            self.local_storage["user_memories"].append(memory_data)
            self.logger.debug("User memory saved to local storage")
        except Exception as e:
            self.logger.error(f"Failed to save user memory: {e}")
    
    # 便捷方法
    def get_user_context_for_agents(self) -> Dict[str, Any]:
        """为其他Agent提供用户上下文"""
        return {
            "user_profile": self.user_profile.to_dict(),
            "user_preferences": self.user_preferences.to_dict(),
            "recent_memories": [
                {
                    "content": m.content,
                    "importance": m.importance,
                    "tags": m.tags
                }
                for m in sorted(self.user_memories, key=lambda x: x.timestamp, reverse=True)[:5]
            ]
        }
    
    def is_user_interested_in(self, topic: str) -> float:
        """检查用户对某个话题的兴趣程度"""
        # 检查用户画像中的兴趣
        for interest in self.user_profile.interests:
            if topic.lower() in interest.lower() or interest.lower() in topic.lower():
                return 0.8
        
        # 检查用户记忆中的相关内容
        relevant_memories = [m for m in self.user_memories 
                           if topic.lower() in m.content.lower()]
        
        if relevant_memories:
            # 根据记忆数量和重要性计算兴趣程度
            avg_importance = sum(m.importance for m in relevant_memories) / len(relevant_memories)
            return min(0.7, avg_importance + 0.1 * len(relevant_memories))
        
        return 0.3  # 默认中性兴趣