"""
UserProfileAdapter - 用户画像记忆适配器

将用户记忆功能包装为StateMemoryCell适配器，支持：
- 用户画像管理 (@user-profile)
- 用户偏好学习 (@user-preferences)  
- 显式记忆存储 (@user-memory)
- 用户上下文感知

基于demo中的UserMemoryCell逻辑实现
"""

import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from ..adapters.base_adapter import MemoryAdapter
from ..core.user_models import UserProfile, UserMemoryEntry, UserPreferences, UserContext


class UserProfileAdapter(MemoryAdapter):
    """用户画像记忆适配器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化用户画像适配器
        
        Args:
            config: 配置字典，包含：
                - user_id: 用户ID
                - auto_learning: 是否自动学习用户偏好
                - explicit_memory_keywords: 触发显式记忆的关键词
                - profile_update_threshold: 画像更新阈值
                - memory_retention_days: 记忆保留天数
                - max_memories: 最大记忆数量
        """
        super().__init__(config)
        
        # 适配器信息
        self.adapter_type = "user_profile"
        self.priority = 8  # 高优先级，用户上下文很重要
        self.enabled = True
        self.supported_query_types = [
            "user_profile", "user_preferences", "user_memory", 
            "personal", "context", "learning"
        ]
        
        # 用户配置
        self.user_id = self.config.get("user_id", "default_user")
        self.auto_learning = self.config.get("auto_learning", True)
        self.explicit_memory_keywords = self.config.get("explicit_memory_keywords", [
            "记住", "记录", "重要", "注意", "保存", "记下来"
        ])
        self.profile_update_threshold = self.config.get("profile_update_threshold", 0.1)
        self.memory_retention_days = self.config.get("memory_retention_days", 365)
        self.max_memories = self.config.get("max_memories", 100)
        
        # 用户上下文
        self.user_context = UserContext(user_id=self.user_id)
        
        # 简单的本地存储（实际应该连接外部存储系统）
        self.storage = {
            "user_context": self.user_context.to_dict(),
            "sessions": {}  # 会话级数据
        }
        
        self.logger.info(f"UserProfileAdapter initialized for user: {self.user_id}")
    
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """检查是否能处理请求"""
        query_type = context.get("query_type", "general")
        action = context.get("action", "search")
        
        # 支持用户相关的查询类型
        if query_type in self.supported_query_types:
            return True
        
        # 支持用户特定操作
        user_actions = [
            "get_user_profile", "update_user_profile", 
            "get_user_preferences", "learn_preference",
            "add_user_memory", "get_user_memories",
            "process_user_input", "handle_mention"
        ]
        if action in user_actions:
            return True
        
        # 检查是否包含用户相关关键词
        query = context.get("query", "")
        user_keywords = ["用户", "我", "偏好", "记住", "profile", "preference", "memory"]
        if any(keyword in query.lower() for keyword in user_keywords):
            return True
        
        return False
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户记忆相关请求"""
        action = context.get("action", "search")
        
        try:
            # 用户画像操作
            if action == "get_user_profile":
                return self._get_user_profile(context)
            elif action == "update_user_profile":
                return self._update_user_profile(context)
            
            # 用户偏好操作
            elif action == "get_user_preferences":
                return self._get_user_preferences(context)
            elif action == "learn_preference":
                return self._learn_preference(context)
            
            # 用户记忆操作
            elif action == "add_user_memory":
                return self._add_user_memory(context)
            elif action == "get_user_memories":
                return self._get_user_memories(context)
            
            # 智能处理操作
            elif action == "process_user_input":
                return self._process_user_input(context)
            elif action == "handle_mention":
                return self._handle_mention(context)
            
            # 通用搜索操作
            elif action == "search":
                return self._search_user_context(context)
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported action: {action}",
                    "adapter": self.adapter_type
                }
                
        except Exception as e:
            self.logger.error(f"Error processing action '{action}': {e}")
            return {
                "success": False,
                "error": str(e),
                "adapter": self.adapter_type
            }
    
    async def process_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """异步处理用户记忆相关请求"""
        # 对于当前实现，直接调用同步方法
        # 未来可以优化为真正的异步实现
        return self.process(context)
    
    def _get_user_profile(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户画像"""
        return {
            "success": True,
            "data": {
                "results": [{
                    "content": f"用户画像信息: {self.user_context.get_context_summary()}",
                    "metadata": {
                        "type": "user_profile",
                        "user_id": self.user_id,
                        "profile": self.user_context.profile.to_dict()
                    },
                    "score": 1.0,
                    "source": "user_profile"
                }],
                "adapter": self.adapter_type
            }
        }
    
    def _update_user_profile(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户画像"""
        updates = context.get("updates", {})
        
        try:
            # 更新画像字段
            for field, value in updates.items():
                if hasattr(self.user_context.profile, field):
                    if isinstance(getattr(self.user_context.profile, field), list):
                        # 列表字段：合并去重
                        current_list = getattr(self.user_context.profile, field)
                        if isinstance(value, list):
                            new_list = list(set(current_list + value))
                        else:
                            new_list = list(set(current_list + [value]))
                        setattr(self.user_context.profile, field, new_list)
                    else:
                        # 其他字段：直接设置
                        setattr(self.user_context.profile, field, value)
            
            # 保存更新
            self._save_user_context()
            
            return {
                "success": True,
                "data": {
                    "results": [{
                        "content": f"用户画像已更新: {', '.join(updates.keys())}",
                        "metadata": {
                            "type": "profile_update",
                            "updated_fields": list(updates.keys()),
                            "profile": self.user_context.profile.to_dict()
                        },
                        "score": 1.0,
                        "source": "profile_update"
                    }],
                    "adapter": self.adapter_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update user profile: {str(e)}",
                "adapter": self.adapter_type
            }
    
    def _get_user_preferences(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户偏好"""
        category = context.get("category")
        
        if category:
            prefs = self.user_context.preferences.get_top_preferences(category, 10)
            content = f"{category}偏好: " + ", ".join([f"{pref}({score:.2f})" for pref, score in prefs])
        else:
            content = f"用户偏好概览: {self.user_context.preferences.to_dict()}"
        
        return {
            "success": True,
            "data": {
                "results": [{
                    "content": content,
                    "metadata": {
                        "type": "user_preferences",
                        "category": category,
                        "preferences": self.user_context.preferences.to_dict()
                    },
                    "score": 1.0,
                    "source": "user_preferences"
                }],
                "adapter": self.adapter_type
            }
        }
    
    def _learn_preference(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """学习用户偏好"""
        category = context.get("category")
        preference = context.get("preference") 
        feedback = context.get("feedback", 0.7)
        
        if not category or not preference:
            return {
                "success": False,
                "error": "Category and preference are required",
                "adapter": self.adapter_type
            }
        
        try:
            # 学习偏好
            self.user_context.preferences.learn_preference(category, preference, feedback)
            
            # 保存更新
            self._save_user_context()
            
            new_score = self.user_context.preferences.get_top_preferences(category, 1)
            score_info = new_score[0] if new_score else (preference, feedback)
            
            return {
                "success": True,
                "data": {
                    "results": [{
                        "content": f"已学习偏好: {category}/{preference} = {score_info[1]:.2f}",
                        "metadata": {
                            "type": "preference_learning",
                            "category": category,
                            "preference": preference,
                            "new_score": score_info[1]
                        },
                        "score": 1.0,
                        "source": "preference_learning"
                    }],
                    "adapter": self.adapter_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to learn preference: {str(e)}",
                "adapter": self.adapter_type
            }
    
    def _add_user_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """添加用户记忆"""
        content = context.get("content")
        memory_type = context.get("memory_type", "learned")
        importance = context.get("importance", 0.5)
        memory_context = context.get("context", {})
        tags = context.get("tags", [])
        
        if not content:
            return {
                "success": False,
                "error": "Content is required",
                "adapter": self.adapter_type
            }
        
        try:
            # 添加记忆
            self.user_context.add_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                context=memory_context,
                tags=tags
            )
            
            # 保存更新
            self._save_user_context()
            
            return {
                "success": True,
                "data": {
                    "results": [{
                        "content": f"已添加用户记忆: {content[:50]}{'...' if len(content) > 50 else ''}",
                        "metadata": {
                            "type": "user_memory",
                            "memory_type": memory_type,
                            "importance": importance,
                            "tags": tags,
                            "timestamp": datetime.now().isoformat()
                        },
                        "score": importance,
                        "source": "user_memory"
                    }],
                    "adapter": self.adapter_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add user memory: {str(e)}",
                "adapter": self.adapter_type
            }
    
    def _get_user_memories(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户记忆"""
        memory_type = context.get("memory_type")
        tags = context.get("tags", [])
        limit = context.get("limit", 10)
        
        # 筛选记忆
        memories = self.user_context.recent_memories
        
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]
        
        if tags:
            memories = [m for m in memories if any(tag in m.tags for tag in tags)]
        
        # 按重要性和时间排序
        memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        memories = memories[:limit]
        
        results = []
        for memory in memories:
            results.append({
                "content": memory.content,
                "metadata": {
                    "type": "user_memory",
                    "memory_type": memory.memory_type,
                    "importance": memory.importance,
                    "timestamp": memory.timestamp.isoformat(),
                    "tags": memory.tags,
                    "access_count": memory.access_count
                },
                "score": memory.importance,
                "source": "user_memory"
            })
            # 记录访问
            memory.access()
        
        return {
            "success": True,
            "data": {
                "results": results,
                "total_memories": len(self.user_context.recent_memories),
                "filtered_count": len(memories),
                "adapter": self.adapter_type
            }
        }
    
    def _process_user_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """智能处理用户输入，自动学习用户信息"""
        user_input = context.get("user_input", "")
        conversation_context = context.get("conversation_context", {})
        
        results = []
        
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
                        results.extend(memory_result["data"]["results"])
            
            # 2. 分析并更新用户画像
            profile_updates = self._analyze_user_input_for_profile(user_input)
            if profile_updates:
                update_result = self._update_user_profile({"updates": profile_updates})
                if update_result["success"]:
                    results.extend(update_result["data"]["results"])
            
            # 3. 分析用户偏好信号
            if self.auto_learning:
                preference_signals = self._analyze_preference_signals(user_input, conversation_context)
                for signal in preference_signals:
                    pref_result = self._learn_preference(signal)
                    if pref_result["success"]:
                        results.extend(pref_result["data"]["results"])
            
            return {
                "success": True,
                "data": {
                    "results": results,
                    "processing_summary": {
                        "explicit_memories": len([r for r in results if r["metadata"].get("type") == "user_memory"]),
                        "profile_updates": len([r for r in results if r["metadata"].get("type") == "profile_update"]),
                        "preference_learning": len([r for r in results if r["metadata"].get("type") == "preference_learning"])
                    },
                    "adapter": self.adapter_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process user input: {str(e)}",
                "adapter": self.adapter_type
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
                "error": f"Unsupported mention: @{mention}",
                "adapter": self.adapter_type
            }
    
    def _search_user_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """搜索用户上下文"""
        query = context.get("query", "").lower()
        limit = context.get("limit", 10)
        
        results = []
        
        # 搜索用户画像
        profile_data = self.user_context.profile.to_dict()
        for field, value in profile_data.items():
            if isinstance(value, list):
                for item in value:
                    if query in str(item).lower():
                        results.append({
                            "content": f"用户{field}: {item}",
                            "metadata": {
                                "type": "profile_match",
                                "field": field,
                                "value": item
                            },
                            "score": 0.8,
                            "source": "user_profile"
                        })
            elif query in str(value).lower():
                results.append({
                    "content": f"用户{field}: {value}",
                    "metadata": {
                        "type": "profile_match",
                        "field": field,
                        "value": value
                    },
                    "score": 0.7,
                    "source": "user_profile"
                })
        
        # 搜索用户记忆
        for memory in self.user_context.recent_memories:
            if query in memory.content.lower():
                results.append({
                    "content": memory.content,
                    "metadata": {
                        "type": "memory_match",
                        "memory_type": memory.memory_type,
                        "importance": memory.importance,
                        "timestamp": memory.timestamp.isoformat(),
                        "tags": memory.tags
                    },
                    "score": memory.importance,
                    "source": "user_memory"
                })
                memory.access()  # 记录访问
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "results": results[:limit],
                "total_found": len(results),
                "query": query,
                "adapter": self.adapter_type
            }
        }
    
    # 辅助方法
    def _detect_explicit_memory_request(self, text: str) -> bool:
        """检测用户是否明确要求记录信息"""
        return any(keyword in text for keyword in self.explicit_memory_keywords)
    
    def _extract_memory_content(self, text: str) -> str:
        """提取需要记录的内容"""
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
                    if interest and len(interest) < 20:
                        if "interests" not in updates:
                            updates["interests"] = []
                        updates["interests"].append(interest)
        
        # 检测沟通风格偏好
        style_patterns = {
            "concise": ["简洁", "简单", "直接", "不要太详细"],
            "detailed": ["详细", "具体", "深入", "全面"],
            "friendly": ["友好", "亲切", "温和"],
            "professional": ["专业", "正式", "严谨"]
        }
        
        for style, keywords in style_patterns.items():
            if any(keyword in text for keyword in keywords):
                updates["communication_style"] = style
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
    
    def _save_user_context(self):
        """保存用户上下文"""
        try:
            self.storage["user_context"] = self.user_context.to_dict()
            self.logger.debug(f"User context saved for user: {self.user_id}")
        except Exception as e:
            self.logger.error(f"Failed to save user context: {e}")
    
    # 便捷方法
    def get_user_context_summary(self) -> str:
        """获取用户上下文摘要"""
        return self.user_context.get_context_summary()
    
    def is_user_interested_in(self, topic: str) -> float:
        """检查用户对某个话题的兴趣程度"""
        # 检查用户画像中的兴趣
        for interest in self.user_context.profile.interests:
            if topic.lower() in interest.lower() or interest.lower() in topic.lower():
                return 0.8
        
        # 检查用户记忆中的相关内容
        relevant_memories = [
            m for m in self.user_context.recent_memories
            if topic.lower() in m.content.lower()
        ]
        
        if relevant_memories:
            # 根据记忆数量和重要性计算兴趣程度
            avg_importance = sum(m.importance for m in relevant_memories) / len(relevant_memories)
            return min(0.7, avg_importance + 0.1 * len(relevant_memories))
        
        return 0.3  # 默认中性兴趣
    
    def get_user_preferences_for_category(self, category: str, limit: int = 5) -> List[Tuple[str, float]]:
        """获取指定类别的用户偏好"""
        return self.user_context.preferences.get_top_preferences(category, limit)
    
    def close(self):
        """关闭适配器资源"""
        # 保存用户上下文
        self._save_user_context()
        self.logger.info(f"UserProfileAdapter closed for user: {self.user_id}")


# 便捷函数
def create_user_profile_adapter(user_id: str, config: Optional[Dict[str, Any]] = None) -> UserProfileAdapter:
    """创建用户画像适配器"""
    if config is None:
        config = {}
    config["user_id"] = user_id
    return UserProfileAdapter(config)