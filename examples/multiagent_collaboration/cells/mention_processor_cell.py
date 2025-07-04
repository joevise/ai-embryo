"""
MentionProcessorCell - @引用处理Cell

基于FuturEmbryo的Cell框架，实现@引用的解析、路由和处理
支持@user-profile、@agent、@workflow、@data、@deliverable等对象引用
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple, Union

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from futurembryo.core.cell import Cell
from futurembryo.core.exceptions import CellConfigurationError


class MentionObject:
    """@引用对象的统一表示"""
    
    def __init__(self, mention_id: str, object_type: str, name: str, 
                 description: str = "", handler: callable = None, metadata: Dict[str, Any] = None):
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
    
    def search(self, query: str, object_types: List[str] = None) -> List[MentionObject]:
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
        
        # 执行搜索
        for mention_id in search_ids:
            obj = self.objects[mention_id]
            if (query_lower in mention_id.lower() or 
                query_lower in obj.name.lower() or 
                query_lower in obj.description.lower()):
                results.append(obj)
        
        # 按相关性排序（简单的字符串匹配）
        def relevance_score(obj: MentionObject) -> float:
            score = 0
            if query_lower == obj.mention_id.lower():
                score += 10
            elif obj.mention_id.lower().startswith(query_lower):
                score += 5
            elif query_lower in obj.mention_id.lower():
                score += 3
            
            if query_lower in obj.name.lower():
                score += 2
            if query_lower in obj.description.lower():
                score += 1
            
            return score
        
        results.sort(key=relevance_score, reverse=True)
        return results
    
    def get_by_type(self, object_type: str) -> List[MentionObject]:
        """获取指定类型的所有对象"""
        if object_type in self.type_index:
            return [self.objects[mention_id] for mention_id in self.type_index[object_type]]
        return []
    
    def get_all(self) -> List[MentionObject]:
        """获取所有@引用对象"""
        return list(self.objects.values())


class MentionProcessorCell(Cell):
    """
    @引用处理Cell
    
    功能：
    1. 解析文本中的@引用
    2. 管理@引用对象注册表
    3. 路由@引用到对应处理器
    4. 提供@引用搜索和自动补全
    5. 统计@引用使用情况
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化@引用处理Cell
        
        Args:
            config: 配置字典，包含：
                - mention_pattern: @引用的正则表达式模式
                - max_suggestions: 最大建议数量
                - enable_fuzzy_search: 是否启用模糊搜索
                - auto_register_mentions: 是否自动注册新的@引用
                - builtin_mentions: 内置的@引用对象配置
        """
        super().__init__(config)
        
        # 配置
        self.mention_pattern = self.config.get("mention_pattern", r"@([\w-]+)")
        self.max_suggestions = self.config.get("max_suggestions", 10)
        self.enable_fuzzy_search = self.config.get("enable_fuzzy_search", True)
        self.auto_register_mentions = self.config.get("auto_register_mentions", False)
        
        # @引用注册表
        self.registry = MentionRegistry()
        
        # 注册内置@引用对象
        self._register_builtin_mentions()
        
        self.logger.info("MentionProcessorCell initialized")
    
    def _register_builtin_mentions(self):
        """注册内置@引用对象"""
        builtin_mentions = self.config.get("builtin_mentions", [])
        
        # 默认用户相关@引用
        default_user_mentions = [
            {
                "id": "user-profile",
                "type": "user",
                "name": "用户画像",
                "description": "用户的基本信息、兴趣和专业领域"
            },
            {
                "id": "user-preferences", 
                "type": "user",
                "name": "用户偏好",
                "description": "用户的沟通风格和内容偏好"
            },
            {
                "id": "user-memory",
                "type": "user", 
                "name": "用户记忆",
                "description": "用户明确要求记录的重要信息"
            }
        ]
        
        # 合并配置中的内置@引用
        all_builtin = default_user_mentions + builtin_mentions
        
        for mention_config in all_builtin:
            mention_obj = MentionObject(
                mention_id=mention_config["id"],
                object_type=mention_config["type"],
                name=mention_config["name"],
                description=mention_config.get("description", ""),
                metadata=mention_config.get("metadata", {})
            )
            self.registry.register(mention_obj)
        
        self.logger.info(f"Registered {len(all_builtin)} builtin mentions")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理@引用相关操作
        
        Args:
            context: 包含以下字段：
                - action: 操作类型
                  - parse_mentions: 解析文本中的@引用
                  - search_mentions: 搜索@引用对象
                  - register_mention: 注册新的@引用对象
                  - handle_mention: 处理@引用
                  - get_suggestions: 获取@引用建议
                  - get_all_mentions: 获取所有@引用对象
                - text: 要解析的文本（parse_mentions）
                - query: 搜索查询（search_mentions）
                - mention_config: @引用对象配置（register_mention）
                - mention_id: @引用ID（handle_mention）
                - partial_input: 部分输入（get_suggestions）
                
        Returns:
            Dict: 处理结果
        """
        action = context.get("action", "parse_mentions")
        
        if action == "parse_mentions":
            return self._parse_mentions(context)
        elif action == "search_mentions":
            return self._search_mentions(context)
        elif action == "register_mention":
            return self._register_mention(context)
        elif action == "handle_mention":
            return self._handle_mention(context)
        elif action == "get_suggestions":
            return self._get_suggestions(context)
        elif action == "get_all_mentions":
            return self._get_all_mentions(context)
        else:
            return {
                "success": False,
                "error": f"Unsupported action: {action}"
            }
    
    def _parse_mentions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析文本中的@引用"""
        text = context.get("text", "")
        
        if not text:
            return {
                "success": True,
                "data": {
                    "mentions": [],
                    "mention_objects": [],
                    "processed_text": text
                }
            }
        
        # 使用正则表达式查找@引用
        matches = re.findall(self.mention_pattern, text)
        mentions = list(set(matches))  # 去重
        
        # 解析@引用对象
        mention_objects = []
        valid_mentions = []
        
        for mention in mentions:
            mention_obj = self.registry.get(mention)
            if mention_obj:
                mention_obj.record_mention()
                mention_objects.append(mention_obj.get_display_info())
                valid_mentions.append(mention)
            elif self.auto_register_mentions:
                # 自动注册新的@引用
                auto_obj = MentionObject(
                    mention_id=mention,
                    object_type="auto",
                    name=mention,
                    description=f"Auto-registered mention: {mention}"
                )
                self.registry.register(auto_obj)
                mention_objects.append(auto_obj.get_display_info())
                valid_mentions.append(mention)
        
        # 生成处理后的文本（可选：替换@引用为链接等）
        processed_text = text
        
        return {
            "success": True,
            "data": {
                "mentions": valid_mentions,
                "mention_objects": mention_objects,
                "processed_text": processed_text,
                "total_mentions_found": len(matches),
                "valid_mentions_count": len(valid_mentions)
            }
        }
    
    def _search_mentions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """搜索@引用对象"""
        query = context.get("query", "")
        object_types = context.get("object_types", [])
        limit = context.get("limit", self.max_suggestions)
        
        if not query:
            # 返回所有对象
            results = self.registry.get_all()
        else:
            # 执行搜索
            results = self.registry.search(query, object_types)
        
        # 限制结果数量
        results = results[:limit]
        
        return {
            "success": True,
            "data": {
                "query": query,
                "results": [obj.get_display_info() for obj in results],
                "total_count": len(results)
            }
        }
    
    def _register_mention(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """注册新的@引用对象"""
        mention_config = context.get("mention_config", {})
        
        required_fields = ["id", "type", "name"]
        for field in required_fields:
            if field not in mention_config:
                return {
                    "success": False,
                    "error": f"Missing required field: {field}"
                }
        
        # 检查ID是否已存在
        if self.registry.get(mention_config["id"]):
            return {
                "success": False,
                "error": f"Mention ID already exists: {mention_config['id']}"
            }
        
        try:
            # 创建@引用对象
            mention_obj = MentionObject(
                mention_id=mention_config["id"],
                object_type=mention_config["type"],
                name=mention_config["name"],
                description=mention_config.get("description", ""),
                handler=mention_config.get("handler"),
                metadata=mention_config.get("metadata", {})
            )
            
            # 注册到注册表
            self.registry.register(mention_obj)
            
            return {
                "success": True,
                "data": {
                    "mention_id": mention_obj.mention_id,
                    "mention_info": mention_obj.get_display_info()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to register mention: {str(e)}"
            }
    
    def _handle_mention(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理@引用"""
        mention_id = context.get("mention_id", "")
        mention_context = context.get("mention_context", {})
        
        mention_obj = self.registry.get(mention_id)
        if not mention_obj:
            return {
                "success": False,
                "error": f"Mention not found: @{mention_id}"
            }
        
        # 记录引用
        mention_obj.record_mention()
        
        # 如果有处理函数，调用处理函数
        if mention_obj.handler:
            try:
                result = mention_obj.handler(mention_context)
                return {
                    "success": True,
                    "data": {
                        "mention_id": mention_id,
                        "mention_type": mention_obj.object_type,
                        "handler_result": result
                    }
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Handler failed for @{mention_id}: {str(e)}"
                }
        else:
            # 返回基本信息
            return {
                "success": True,
                "data": {
                    "mention_id": mention_id,
                    "mention_type": mention_obj.object_type,
                    "mention_info": mention_obj.get_display_info(),
                    "metadata": mention_obj.metadata
                }
            }
    
    def _get_suggestions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取@引用建议"""
        partial_input = context.get("partial_input", "")
        object_types = context.get("object_types", [])
        limit = context.get("limit", self.max_suggestions)
        
        # 如果部分输入为空，返回最常用的@引用
        if not partial_input:
            all_objects = self.registry.get_all()
            # 按使用频率排序
            all_objects.sort(key=lambda obj: obj.mention_count, reverse=True)
            suggestions = all_objects[:limit]
        else:
            # 搜索匹配的@引用
            suggestions = self.registry.search(partial_input, object_types)[:limit]
        
        return {
            "success": True,
            "data": {
                "partial_input": partial_input,
                "suggestions": [
                    {
                        **obj.get_display_info(),
                        "mention_count": obj.mention_count,
                        "last_mentioned": obj.last_mentioned.isoformat() if obj.last_mentioned else None
                    }
                    for obj in suggestions
                ]
            }
        }
    
    def _get_all_mentions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取所有@引用对象"""
        object_type = context.get("object_type")
        
        if object_type:
            objects = self.registry.get_by_type(object_type)
        else:
            objects = self.registry.get_all()
        
        # 按类型分组
        grouped_objects = {}
        for obj in objects:
            if obj.object_type not in grouped_objects:
                grouped_objects[obj.object_type] = []
            grouped_objects[obj.object_type].append(obj.get_display_info())
        
        return {
            "success": True,
            "data": {
                "objects_by_type": grouped_objects,
                "total_count": len(objects),
                "types_count": len(grouped_objects)
            }
        }
    
    # 便捷方法
    def register_agent_mention(self, agent_id: str, agent_name: str, 
                              description: str = "", handler: callable = None):
        """便捷方法：注册Agent @引用"""
        return self.process({
            "action": "register_mention",
            "mention_config": {
                "id": agent_id,
                "type": "agent",
                "name": agent_name,
                "description": description,
                "handler": handler
            }
        })
    
    def register_workflow_mention(self, workflow_id: str, workflow_name: str,
                                 description: str = "", handler: callable = None):
        """便捷方法：注册工作流@引用"""
        return self.process({
            "action": "register_mention",
            "mention_config": {
                "id": workflow_id,
                "type": "workflow", 
                "name": workflow_name,
                "description": description,
                "handler": handler
            }
        })
    
    def register_deliverable_mention(self, deliverable_id: str, deliverable_name: str,
                                   file_path: str = "", content_type: str = ""):
        """便捷方法：注册产出物@引用"""
        return self.process({
            "action": "register_mention",
            "mention_config": {
                "id": deliverable_id,
                "type": "deliverable",
                "name": deliverable_name,
                "description": f"Generated deliverable: {deliverable_name}",
                "metadata": {
                    "file_path": file_path,
                    "content_type": content_type,
                    "generated_at": datetime.now().isoformat()
                }
            }
        })
    
    def parse_and_extract_mentions(self, text: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """便捷方法：解析文本并提取@引用信息"""
        result = self.process({
            "action": "parse_mentions",
            "text": text
        })
        
        if result["success"]:
            data = result["data"]
            return data["mentions"], data["mention_objects"]
        else:
            return [], []
    
    def get_mention_suggestions(self, partial: str, max_count: int = 5) -> List[Dict[str, Any]]:
        """便捷方法：获取@引用建议"""
        result = self.process({
            "action": "get_suggestions",
            "partial_input": partial,
            "limit": max_count
        })
        
        if result["success"]:
            return result["data"]["suggestions"]
        else:
            return []