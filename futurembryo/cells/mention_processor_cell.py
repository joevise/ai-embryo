"""
MentionProcessorCell - @引用处理Cell

基于FuturEmbryo的Cell框架，实现@引用的解析、路由和处理
支持@user-profile、@agent、@workflow、@data、@deliverable等对象引用
"""

import re
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple, Union, Callable

from futurembryo.core.cell import Cell
from futurembryo.core.exceptions import CellConfigurationError


class MentionObject:
    """@引用对象的统一表示"""
    
    def __init__(self, mention_id: str, object_type: str, name: str, 
                 description: str = "", handler: Optional[Callable] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.mention_id = mention_id          # @引用ID
        self.object_type = object_type        # 对象类型: user/agent/workflow/data/deliverable
        self.name = name                      # 显示名称
        self.description = description        # 描述
        self.handler = handler                # 处理函数
        self.metadata = metadata or {}        # 元数据
        self.created_at = datetime.now()      # 创建时间
        self.mention_count = 0                # 被引用次数
        self.last_mentioned = None            # 最后引用时间
    
    def to_mention_format(self) -> str:
        """转换为@引用格式"""
        return f"@{self.mention_id}"
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取显示信息"""
        return {
            "id": self.mention_id,
            "name": self.name,
            "description": self.description,
            "type": self.object_type,
            "mention": self.to_mention_format(),
            "metadata": self.metadata
        }
    
    def record_mention(self):
        """记录一次@引用"""
        self.mention_count += 1
        self.last_mentioned = datetime.now()


class MentionRegistry:
    """@引用对象注册表"""
    
    def __init__(self):
        self.objects: Dict[str, MentionObject] = {}
        self.type_index: Dict[str, Set[str]] = {
            "user": set(),
            "agent": set(), 
            "workflow": set(),
            "data": set(),
            "deliverable": set()
        }
    
    def register(self, mention_obj: MentionObject):
        """注册@引用对象"""
        self.objects[mention_obj.mention_id] = mention_obj
        if mention_obj.object_type in self.type_index:
            self.type_index[mention_obj.object_type].add(mention_obj.mention_id)
    
    def unregister(self, mention_id: str):
        """注销@引用对象"""
        if mention_id in self.objects:
            obj = self.objects[mention_id]
            del self.objects[mention_id]
            if obj.object_type in self.type_index:
                self.type_index[obj.object_type].discard(mention_id)
    
    def get(self, mention_id: str) -> Optional[MentionObject]:
        """获取@引用对象"""
        return self.objects.get(mention_id)
    
    def search(self, query: str, object_types: Optional[List[str]] = None) -> List[MentionObject]:
        """搜索@引用对象"""
        query_lower = query.lower()
        results = []
        
        # 确定搜索范围
        search_ids = set()
        if object_types:
            for obj_type in object_types:
                if obj_type in self.type_index:
                    search_ids.update(self.type_index[obj_type])
        else:
            search_ids = set(self.objects.keys())
        
        # 搜索匹配项
        for mention_id in search_ids:
            obj = self.objects[mention_id]
            if (query_lower in mention_id.lower() or 
                query_lower in obj.name.lower() or 
                query_lower in obj.description.lower()):
                results.append(obj)
        
        # 按相关性排序
        results.sort(key=lambda x: x.mention_count, reverse=True)
        return results
    
    def get_by_type(self, object_type: str) -> List[MentionObject]:
        """按类型获取@引用对象"""
        if object_type not in self.type_index:
            return []
        
        return [self.objects[mention_id] for mention_id in self.type_index[object_type]]
    
    def get_all(self) -> List[MentionObject]:
        """获取所有@引用对象"""
        return list(self.objects.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_mentions = sum(obj.mention_count for obj in self.objects.values())
        type_counts = {obj_type: len(ids) for obj_type, ids in self.type_index.items()}
        
        return {
            "total_objects": len(self.objects),
            "total_mentions": total_mentions,
            "type_counts": type_counts,
            "most_mentioned": sorted(
                self.objects.values(), 
                key=lambda x: x.mention_count, 
                reverse=True
            )[:5]
        }


class MentionProcessorCell(Cell):
    """@引用处理Cell"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化@引用处理Cell
        
        Args:
            config: 配置信息
                - enable_auto_complete: 是否启用自动补全 (default: True)
                - max_deliverables: 最大产出物数量 (default: 50)
                - mention_pattern: @引用匹配模式
        """
        super().__init__(config)
        
        # 配置参数
        self.enable_auto_complete = self.config.get("enable_auto_complete", True)
        self.max_deliverables = self.config.get("max_deliverables", 50)
        self.mention_pattern = self.config.get(
            "mention_pattern", 
            r'@([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)*)'
        )
        
        # @引用注册表
        self.registry = MentionRegistry()
        
        # 编译正则表达式
        self.mention_regex = re.compile(self.mention_pattern)
        
        # 初始化默认@引用对象
        self._register_default_mentions()
    
    def _register_default_mentions(self):
        """注册默认的@引用对象"""
        default_mentions = [
            MentionObject(
                "user-profile", "user", "用户画像",
                "用户的兴趣、专业领域、沟通风格等画像信息"
            ),
            MentionObject(
                "user-memory", "user", "用户记忆", 
                "用户的历史对话记忆和重要信息"
            ),
            MentionObject(
                "user-preferences", "user", "用户偏好",
                "用户的行为偏好和个性化设置"
            )
        ]
        
        for mention_obj in default_mentions:
            self.registry.register(mention_obj)
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理@引用
        
        Args:
            context: 输入上下文
                - text: 包含@引用的文本
                - action: 处理动作 (extract/resolve/suggest/register/unregister)
                
        Returns:
            处理结果
        """
        try:
            text = context.get("text", "")
            action = context.get("action", "extract")
            
            if action == "extract":
                return self._extract_mentions(text)
            elif action == "resolve":
                return self._resolve_mentions(text, context)
            elif action == "suggest":
                return self._suggest_mentions(context.get("query", ""))
            elif action == "register":
                return self._register_mention(context)
            elif action == "unregister":
                return self._unregister_mention(context.get("mention_id", ""))
            elif action == "get_statistics":
                return self._get_statistics()
            else:
                raise ValueError(f"未知的处理动作: {action}")
                
        except Exception as e:
            return {
                "success": False,
                "error": f"@引用处理失败: {str(e)}",
                "mentions": []
            }
    
    async def process_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步处理@引用
        
        Args:
            context: 输入上下文
                - text: 包含@引用的文本
                - action: 处理动作 (extract/resolve/suggest/register/unregister)
                
        Returns:
            处理结果
        """
        # 对于当前实现，直接调用同步方法
        # 未来可以优化为真正的异步实现
        return self.process(context)
    
    def _extract_mentions(self, text: str) -> Dict[str, Any]:
        """提取文本中的@引用"""
        mentions = self.mention_regex.findall(text)
        
        extracted_mentions = []
        for mention_id in set(mentions):  # 去重
            mention_obj = self.registry.get(mention_id)
            if mention_obj:
                mention_obj.record_mention()
                extracted_mentions.append(mention_obj.get_display_info())
            else:
                # 未注册的@引用
                extracted_mentions.append({
                    "id": mention_id,
                    "name": mention_id,
                    "description": "未注册的@引用",
                    "type": "unknown",
                    "mention": f"@{mention_id}",
                    "registered": False
                })
        
        return {
            "success": True,
            "mentions": extracted_mentions,
            "total_count": len(mentions),
            "unique_count": len(extracted_mentions)
        }
    
    def _resolve_mentions(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析@引用并获取对象内容"""
        mentions = self.mention_regex.findall(text)
        resolved_mentions = []
        
        for mention_id in set(mentions):
            mention_obj = self.registry.get(mention_id)
            if mention_obj and mention_obj.handler:
                try:
                    # 调用处理函数
                    result = mention_obj.handler(context)
                    # 如果是协程，在同步上下文中执行
                    if hasattr(result, '__await__'):
                        import asyncio
                        loop = asyncio.new_event_loop()
                        result = loop.run_until_complete(result)
                        loop.close()
                    
                    resolved_mentions.append({
                        "mention": f"@{mention_id}",
                        "object": mention_obj.get_display_info(),
                        "content": result,
                        "resolved": True
                    })
                    mention_obj.record_mention()
                except Exception as e:
                    resolved_mentions.append({
                        "mention": f"@{mention_id}",
                        "object": mention_obj.get_display_info(),
                        "error": str(e),
                        "resolved": False
                    })
            else:
                resolved_mentions.append({
                    "mention": f"@{mention_id}",
                    "object": None,
                    "error": "未找到处理函数或对象未注册",
                    "resolved": False
                })
        
        return {
            "success": True,
            "resolved_mentions": resolved_mentions,
            "total_mentions": len(mentions)
        }
    
    def _suggest_mentions(self, query: str) -> Dict[str, Any]:
        """建议@引用"""
        if not self.enable_auto_complete:
            return {"success": True, "suggestions": []}
        
        suggestions = self.registry.search(query)
        
        return {
            "success": True,
            "suggestions": [obj.get_display_info() for obj in suggestions[:10]],
            "query": query
        }
    
    def _register_mention(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """注册新的@引用对象"""
        try:
            mention_obj = MentionObject(
                mention_id=context["mention_id"],
                object_type=context["object_type"],
                name=context["name"],
                description=context.get("description", ""),
                handler=context.get("handler"),
                metadata=context.get("metadata", {})
            )
            
            self.registry.register(mention_obj)
            
            return {
                "success": True,
                "message": f"@引用对象 @{mention_obj.mention_id} 注册成功",
                "object": mention_obj.get_display_info()
            }
            
        except KeyError as e:
            return {
                "success": False,
                "error": f"缺少必要参数: {str(e)}"
            }
    
    def _unregister_mention(self, mention_id: str) -> Dict[str, Any]:
        """注销@引用对象"""
        if mention_id in self.registry.objects:
            self.registry.unregister(mention_id)
            return {
                "success": True,
                "message": f"@引用对象 @{mention_id} 注销成功"
            }
        else:
            return {
                "success": False,
                "error": f"@引用对象 @{mention_id} 不存在"
            }
    
    def _get_statistics(self) -> Dict[str, Any]:
        """获取@引用统计信息"""
        stats = self.registry.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    
    def extract_mentions(self, text: str) -> List[str]:
        """同步方法：提取@引用列表"""
        return self.mention_regex.findall(text)
    
    def register_mention(self, mention_id: str, object_type: str, name: str,
                        description: str = "", handler: Optional[Callable] = None,
                        metadata: Optional[Dict[str, Any]] = None):
        """同步方法：注册@引用对象"""
        mention_obj = MentionObject(
            mention_id=mention_id,
            object_type=object_type,
            name=name,
            description=description,
            handler=handler,
            metadata=metadata
        )
        self.registry.register(mention_obj)
    
    def get_mention(self, mention_id: str) -> Optional[MentionObject]:
        """同步方法：获取@引用对象"""
        return self.registry.get(mention_id)
    
    def get_all_mentions(self) -> List[MentionObject]:
        """同步方法：获取所有@引用对象"""
        return self.registry.get_all()


# 便捷函数
def create_mention_processor(config: Optional[Dict[str, Any]] = None) -> MentionProcessorCell:
    """创建@引用处理Cell"""
    return MentionProcessorCell(config)


def extract_mentions(text: str, pattern: Optional[str] = None) -> List[str]:
    """提取文本中的@引用（独立函数）"""
    if pattern is None:
        pattern = r'@([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)*)'
    
    return re.findall(pattern, text)