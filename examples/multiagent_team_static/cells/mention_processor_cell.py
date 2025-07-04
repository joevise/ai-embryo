"""
@引用处理Cell - 处理系统中的@引用机制

简化实现，提供基本的@引用解析和处理功能
"""

import re
from typing import Dict, Any, List, Optional, Tuple


class MentionProcessorCell:
    """@引用处理Cell"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化@引用处理器"""
        self.config = config or {}
        
        # 注册的@引用对象
        self.registered_mentions = {
            "user-profile": {
                "type": "system",
                "description": "用户画像信息",
                "handler": "get_user_profile"
            },
            "user-memory": {
                "type": "system", 
                "description": "用户记忆内容",
                "handler": "get_user_memory"
            },
            "user-preferences": {
                "type": "system",
                "description": "用户偏好设置",
                "handler": "get_user_preferences"
            }
        }
        
        # 产出物存储
        self.deliverables = {}
        self.deliverable_counter = 0
    
    def extract_mentions(self, text: str) -> List[str]:
        """从文本中提取所有@引用"""
        # 匹配 @xxx 格式的引用
        pattern = r'@([a-zA-Z0-9\-_]+)'
        mentions = re.findall(pattern, text)
        return list(set(mentions))  # 去重
    
    def process_mentions(self, text: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        处理文本中的@引用
        
        Returns:
            Tuple[str, List[Dict]]: (处理后的文本, 引用信息列表)
        """
        mentions = self.extract_mentions(text)
        mention_info = []
        processed_text = text
        
        for mention in mentions:
            info = self.get_mention_info(mention)
            if info:
                mention_info.append(info)
                
                # 如果需要替换内容
                if info.get("replacement"):
                    processed_text = processed_text.replace(
                        f"@{mention}", 
                        info["replacement"]
                    )
        
        return processed_text, mention_info
    
    def get_mention_info(self, mention: str) -> Optional[Dict[str, Any]]:
        """获取@引用的详细信息"""
        # 检查系统引用
        if mention in self.registered_mentions:
            return {
                "mention": f"@{mention}",
                "type": self.registered_mentions[mention]["type"],
                "description": self.registered_mentions[mention]["description"],
                "handler": self.registered_mentions[mention]["handler"]
            }
        
        # 检查产出物引用
        if mention in self.deliverables:
            return {
                "mention": f"@{mention}",
                "type": "deliverable",
                "data": self.deliverables[mention]
            }
        
        # 检查是否是Agent引用
        if mention in ["researcher", "analyst", "writer", "creative", "planner"]:
            return {
                "mention": f"@{mention}",
                "type": "agent",
                "agent_id": mention
            }
        
        return None
    
    def register_deliverable(self, name: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """注册一个产出物"""
        self.deliverable_counter += 1
        deliverable_id = f"deliverable-{self.deliverable_counter}"
        
        self.deliverables[deliverable_id] = {
            "id": deliverable_id,
            "name": name,
            "content": content,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp()
        }
        
        return deliverable_id
    
    def get_deliverable(self, deliverable_id: str) -> Optional[Dict[str, Any]]:
        """获取产出物"""
        return self.deliverables.get(deliverable_id)
    
    def list_deliverables(self) -> List[Dict[str, Any]]:
        """列出所有产出物"""
        return list(self.deliverables.values())
    
    def resolve_mention(self, mention: str, context: Dict[str, Any]) -> Any:
        """解析@引用的实际内容"""
        info = self.get_mention_info(mention)
        if not info:
            return None
        
        mention_type = info.get("type")
        
        if mention_type == "system":
            # 处理系统引用
            handler = info.get("handler")
            if handler == "get_user_profile" and "user_memory" in context:
                return context["user_memory"].get_user_profile()
            elif handler == "get_user_memory" and "user_memory" in context:
                return context["user_memory"].get_user_context_for_agents()
            elif handler == "get_user_preferences" and "user_memory" in context:
                profile = context["user_memory"].get_user_profile()
                return profile.get("preferences", {})
        
        elif mention_type == "deliverable":
            # 返回产出物内容
            return info.get("data", {}).get("content")
        
        elif mention_type == "agent":
            # 返回Agent信息
            return {"agent_id": info.get("agent_id")}
        
        return None
    
    def create_mention_context(self, mentions: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """为提到的@引用创建上下文"""
        mention_context = {}
        
        for mention in mentions:
            resolved = self.resolve_mention(mention, context)
            if resolved is not None:
                mention_context[mention] = resolved
        
        return mention_context
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def clear_deliverables(self):
        """清空所有产出物"""
        self.deliverables = {}
        self.deliverable_counter = 0
    
    def export_data(self) -> Dict[str, Any]:
        """导出数据"""
        return {
            "registered_mentions": self.registered_mentions,
            "deliverables": self.deliverables,
            "deliverable_counter": self.deliverable_counter
        }
    
    def import_data(self, data: Dict[str, Any]):
        """导入数据"""
        if "registered_mentions" in data:
            self.registered_mentions.update(data["registered_mentions"])
        if "deliverables" in data:
            self.deliverables = data["deliverables"]
        if "deliverable_counter" in data:
            self.deliverable_counter = data["deliverable_counter"]