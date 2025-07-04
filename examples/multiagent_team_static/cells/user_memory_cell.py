"""
用户记忆Cell - 管理用户相关记忆和学习

简化实现，提供基本的用户记忆管理功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class UserMemoryCell:
    """用户记忆管理Cell"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化用户记忆Cell"""
        self.config = config or {}
        self.user_profile = {
            "interests": [],
            "communication_style": "未设置",
            "preferences": {},
            "skills": [],
            "goals": []
        }
        self.memories = []
        self.max_memories = self.config.get("max_memories", 100)
        
    def add_memory(self, content: str, context: Optional[Dict[str, Any]] = None):
        """添加记忆"""
        memory = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "id": f"mem_{len(self.memories) + 1}"
        }
        self.memories.append(memory)
        
        # 保持记忆数量限制
        if len(self.memories) > self.max_memories:
            self.memories = self.memories[-self.max_memories:]
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索记忆"""
        # 简单的关键词匹配
        results = []
        query_lower = query.lower()
        
        for memory in reversed(self.memories):  # 从最新的开始搜索
            if query_lower in memory["content"].lower():
                results.append(memory)
                if len(results) >= limit:
                    break
        
        return results
    
    def update_user_profile(self, updates: Dict[str, Any]):
        """更新用户画像"""
        for key, value in updates.items():
            if key == "interests" and isinstance(value, list):
                # 合并兴趣列表，去重
                current_interests = self.user_profile.get("interests", [])
                new_interests = list(set(current_interests + value))
                self.user_profile["interests"] = new_interests
            elif key == "preferences" and isinstance(value, dict):
                # 合并偏好设置
                current_prefs = self.user_profile.get("preferences", {})
                current_prefs.update(value)
                self.user_profile["preferences"] = current_prefs
            else:
                # 直接更新其他字段
                self.user_profile[key] = value
    
    def get_user_context_for_agents(self) -> Dict[str, Any]:
        """获取用户上下文信息供Agent使用"""
        return {
            "user_profile": self.user_profile.copy(),
            "recent_memories": self.memories[-10:] if self.memories else [],
            "memory_count": len(self.memories)
        }
    
    def get_user_profile(self) -> Dict[str, Any]:
        """获取用户画像"""
        return self.user_profile.copy()
    
    def learn_from_interaction(self, user_input: str, agent_response: str) -> Dict[str, Any]:
        """从交互中学习"""
        learning_result = {
            "profile_updated": False,
            "preferences_learned": False,
            "new_interests": []
        }
        
        # 简单的兴趣提取
        interest_keywords = ["喜欢", "感兴趣", "研究", "学习", "了解"]
        for keyword in interest_keywords:
            if keyword in user_input:
                # 提取可能的兴趣点
                words = user_input.split()
                for i, word in enumerate(words):
                    if keyword in word and i + 1 < len(words):
                        potential_interest = words[i + 1]
                        if potential_interest not in self.user_profile["interests"]:
                            self.user_profile["interests"].append(potential_interest)
                            learning_result["new_interests"].append(potential_interest)
                            learning_result["profile_updated"] = True
        
        # 添加到记忆
        self.add_memory(
            f"用户: {user_input}",
            {"type": "user_input", "timestamp": datetime.now().isoformat()}
        )
        self.add_memory(
            f"系统: {agent_response}",
            {"type": "agent_response", "timestamp": datetime.now().isoformat()}
        )
        
        return learning_result
    
    def clear_memories(self):
        """清空记忆"""
        self.memories = []
    
    def export_data(self) -> Dict[str, Any]:
        """导出数据"""
        return {
            "user_profile": self.user_profile,
            "memories": self.memories,
            "export_time": datetime.now().isoformat()
        }
    
    def import_data(self, data: Dict[str, Any]):
        """导入数据"""
        if "user_profile" in data:
            self.user_profile = data["user_profile"]
        if "memories" in data:
            self.memories = data["memories"]