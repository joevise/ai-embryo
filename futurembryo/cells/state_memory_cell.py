"""
StateMemoryCell - 记忆连接器/适配器管理器 (模块化版本)

核心定位：
- 不是本地记忆存储系统
- 是多源记忆服务的统一接口和适配器管理器
- 支持动态加载和管理各种外部记忆服务适配器

架构特点：
1. 统一前端接口 - 为项目内部提供标准化的查询接口
2. 动态适配器加载 - 通过配置文件和类路径字符串加载适配器
3. 服务发现和路由 - 根据查询类型自动选择合适的外部服务
4. 结果聚合器 - 整合多个外部服务的返回结果
5. 格式转换器 - 适配不同外部服务的接口格式
6. 插拔式扩展 - 无需修改核心代码即可添加新适配器

工作流程：
内部查询 → StateMemoryCell → [动态加载适配器] → 外部服务调用 → 结果整合 → 标准化输出 → Agent上下文
"""
import json
import time
import hashlib
import importlib
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core.cell import Cell
from ..core.exceptions import CellConfigurationError
from ..adapters.base_adapter import MemoryAdapter


class StateMemoryCell(Cell):
    """状态和记忆管理Cell - 模块化适配器管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化StateMemoryCell (模块化版本)
        
        架构特点：
        1. 统一前端接口 - 标准化查询接口
        2. 动态适配器加载 - 通过类路径字符串加载适配器
        3. 智能路由 - 根据查询类型选择适配器
        4. 结果聚合 - 整合多源结果
        5. 格式标准化 - 统一返回格式
        6. 插拔式扩展 - 无需修改核心代码即可添加新适配器
        
        Args:
            config: 配置字典，可包含：
                - adapters: 适配器配置列表，每个包含：
                  - name: 适配器名称
                  - class_path: 适配器类的完整路径 (如 "futurembryo.adapters.fastgpt_adapter.FastGPTAdapter")
                  - config: 适配器配置
                - routing_strategy: 路由策略 ("priority", "parallel", "fallback")
                - result_aggregation: 结果聚合策略 ("merge", "best", "weighted")
                - max_results_per_adapter: 每个适配器最大结果数
                - enable_caching: 是否启用查询缓存
                - cache_ttl: 缓存存活时间（秒）
        """
        super().__init__(config)
        
        # 基础配置
        self.routing_strategy = self.config.get("routing_strategy", "priority")  # priority, parallel, fallback
        self.result_aggregation = self.config.get("result_aggregation", "merge")  # merge, best, weighted
        self.max_results_per_adapter = self.config.get("max_results_per_adapter", 10)
        self.enable_caching = self.config.get("enable_caching", True)
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5分钟
        
        # 会话状态
        self.session_state: Dict[str, Any] = {}
        
        # 查询缓存
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        
        # 适配器注册表
        self.adapters: Dict[str, MemoryAdapter] = {}
        self.adapter_registry: Dict[str, str] = {}  # name -> class_path
        
        # 初始化适配器
        self._init_adapters()
        
        # 线程池用于并行查询
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        self.logger.info(f"StateMemoryCell (模块化) initialized with {len(self.adapters)} adapters, "
                        f"routing: {self.routing_strategy}, aggregation: {self.result_aggregation}")
    
    def _init_adapters(self):
        """动态初始化适配器"""
        adapters_config = self.config.get("adapters", [])
        
        if not adapters_config:
            self.logger.warning("No adapters configured")
            return
        
        for adapter_config in adapters_config:
            try:
                adapter_name = adapter_config.get("name")
                class_path = adapter_config.get("class_path")
                adapter_config_data = adapter_config.get("config", {})
                
                if not adapter_name or not class_path:
                    self.logger.error(f"Invalid adapter config: missing name or class_path: {adapter_config}")
                    continue
                
                # 动态加载适配器
                adapter = self._load_adapter(class_path, adapter_config_data)
                if adapter:
                    self.adapters[adapter_name] = adapter
                    self.adapter_registry[adapter_name] = class_path
                    self.logger.info(f"Loaded adapter: {adapter_name} ({class_path})")
                else:
                    self.logger.error(f"Failed to load adapter: {adapter_name} ({class_path})")
            
            except Exception as e:
                self.logger.error(f"Failed to initialize adapter {adapter_config}: {e}")
    
    def _load_adapter(self, class_path: str, config: Dict[str, Any]) -> Optional[MemoryAdapter]:
        """动态加载适配器类"""
        try:
            # 解析类路径
            module_path, class_name = class_path.rsplit('.', 1)
            
            # 导入模块
            module = importlib.import_module(module_path)
            
            # 获取类
            adapter_class = getattr(module, class_name)
            
            # 验证是否是MemoryAdapter的子类
            if not issubclass(adapter_class, MemoryAdapter):
                self.logger.error(f"Class {class_path} is not a subclass of MemoryAdapter")
                return None
            
            # 实例化适配器
            adapter = adapter_class(config)
            return adapter
            
        except ImportError as e:
            self.logger.error(f"Failed to import adapter module {class_path}: {e}")
            return None
        except AttributeError as e:
            self.logger.error(f"Failed to find adapter class {class_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to instantiate adapter {class_path}: {e}")
            return None
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理记忆操作 (适配器架构版本)
        
        Args:
            context: 包含以下字段：
                - action: 操作类型 ("search", "get_adapters", "set_state", "get_state", 
                         "get_user_profile", "update_user_profile", "get_user_preferences", 
                         "learn_preference", "add_user_memory", "get_user_memories", 
                         "process_user_input", "handle_mention")
                - query: 搜索查询
                - query_type: 查询类型 ("general", "factual", "procedural", "user_profile", 
                             "user_preferences", "user_memory", "personal", "context", "learning")
                - limit: 结果限制
                - adapters: 指定使用的适配器列表
                - routing_strategy: 临时路由策略
                - key/value: 会话状态操作
                - user_id: 用户ID (用户相关操作)
                - updates: 用户画像更新数据
                - category: 偏好类别
                - preference: 偏好项
                - feedback: 偏好反馈分数
                - content: 记忆内容
                - memory_type: 记忆类型
                - importance: 重要性
                - tags: 标签
                - mention: @引用ID
                - user_input: 用户输入文本
                
        Returns:
            Dict包含操作结果
        """
        action = context.get("action", "search")
        
        try:
            # 核心记忆操作
            if action == "search":
                return self._search_memory(context)
            elif action == "get_adapters":
                return self._get_adapters_info()
            elif action == "set_state":
                return self._set_session_state(context)
            elif action == "get_state":
                return self._get_state(context)
            elif action == "clear_cache":
                return self._clear_cache()
            
            # 用户感知操作 - 优先路由到用户画像适配器
            elif action in ["get_user_profile", "update_user_profile", "get_user_preferences", 
                           "learn_preference", "add_user_memory", "get_user_memories", 
                           "process_user_input", "handle_mention"]:
                return self._handle_user_aware_action(context)
            
            else:
                # 转发到适配器
                return self._forward_to_adapters(context)
                
        except Exception as e:
            self.logger.error(f"Error processing action '{action}': {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    def _search_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """搜索记忆"""
        query = context.get("query", "")
        query_type = context.get("query_type", "general")
        limit = context.get("limit", 10)
        specified_adapters = context.get("adapters", [])
        routing_strategy = context.get("routing_strategy", self.routing_strategy)
        
        if not query.strip():
            return {
                "success": False,
                "error": "Query is required for search"
            }
        
        # 检查缓存
        if self.enable_caching:
            cache_key = self._generate_cache_key(query, query_type, limit)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.info(f"Returning cached result for query: '{query}'")
                return cached_result
        
        # 选择适配器
        selected_adapters = self._select_adapters(query_type, specified_adapters)
        
        if not selected_adapters:
            return {
                "success": False,
                "error": "No suitable adapters found for this query"
            }
        
        # 执行搜索
        search_context = {
            **context,
            "action": "search"
        }
        
        if routing_strategy == "parallel":
            results = self._parallel_search(selected_adapters, search_context)
        elif routing_strategy == "fallback":
            results = self._fallback_search(selected_adapters, search_context)
        else:  # priority
            results = self._priority_search(selected_adapters, search_context)
        
        # 聚合结果
        aggregated_results = self._aggregate_results(results, limit)
        
        # 构建最终结果
        final_result = {
            "success": True,
            "data": {
                "results": aggregated_results,
                "total_found": len(aggregated_results),
                "query": query,
                "query_type": query_type,
                "adapters_used": [adapter.adapter_type for adapter in selected_adapters],
                "routing_strategy": routing_strategy
            }
        }
        
        # 缓存结果
        if self.enable_caching:
            self._cache_result(cache_key, final_result)
        
        self.logger.info(f"Search completed: query='{query}', results={len(aggregated_results)}, "
                        f"adapters={len(selected_adapters)}")
        
        return final_result
    
    def _select_adapters(self, query_type: str, specified_adapters: List[str]) -> List[MemoryAdapter]:
        """选择适合的适配器"""
        if specified_adapters:
            # 使用指定的适配器
            selected = []
            for adapter_name in specified_adapters:
                if adapter_name in self.adapters:
                    adapter = self.adapters[adapter_name]
                    if adapter.can_handle({"query_type": query_type}):
                        selected.append(adapter)
            return selected
        else:
            # 自动选择适配器
            suitable_adapters = []
            for adapter in self.adapters.values():
                if adapter.can_handle({"query_type": query_type}):
                    suitable_adapters.append(adapter)
            
            # 按优先级排序
            suitable_adapters.sort(key=lambda a: a.priority, reverse=True)
            return suitable_adapters
    
    def _parallel_search(self, adapters: List[MemoryAdapter], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """并行搜索"""
        futures = []
        
        for adapter in adapters:
            future = self.executor.submit(adapter.process, context)
            futures.append((adapter, future))
        
        results = []
        for adapter, future in futures:
            try:
                result = future.result(timeout=30)  # 30秒超时
                if result.get("success"):
                    results.append(result)
                else:
                    self.logger.warning(f"Adapter {adapter.adapter_type} failed: {result.get('error')}")
            except Exception as e:
                self.logger.error(f"Adapter {adapter.adapter_type} error: {e}")
        
        return results
    
    def _fallback_search(self, adapters: List[MemoryAdapter], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """回退搜索 - 按优先级依次尝试，直到成功"""
        for adapter in adapters:
            try:
                result = adapter.process(context)
                if result.get("success") and result.get("data", {}).get("results"):
                    return [result]
            except Exception as e:
                self.logger.error(f"Adapter {adapter.adapter_type} failed: {e}")
                continue
        
        return []
    
    def _priority_search(self, adapters: List[MemoryAdapter], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """优先级搜索 - 使用最高优先级的适配器"""
        if not adapters:
            return []
        
        highest_priority_adapter = adapters[0]  # 已按优先级排序
        
        try:
            result = highest_priority_adapter.process(context)
            if result.get("success"):
                return [result]
        except Exception as e:
            self.logger.error(f"Priority adapter {highest_priority_adapter.adapter_type} failed: {e}")
        
        return []
    
    def _aggregate_results(self, results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """聚合搜索结果"""
        if not results:
            return []
        
        if self.result_aggregation == "best":
            return self._get_best_results(results, limit)
        elif self.result_aggregation == "weighted":
            return self._get_weighted_results(results, limit)
        else:  # merge
            return self._merge_results(results, limit)
    
    def _merge_results(self, results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """合并结果"""
        all_results = []
        
        for result in results:
            adapter_results = result.get("data", {}).get("results", [])
            all_results.extend(adapter_results)
        
        # 去重（基于内容hash）
        seen_hashes = set()
        unique_results = []
        
        for item in all_results:
            content_hash = hashlib.md5(item.get("content", "").encode()).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(item)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return unique_results[:limit]
    
    def _get_best_results(self, results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """获取最佳结果 - 选择分数最高的适配器结果"""
        if not results:
            return []
        
        best_result = max(results, key=lambda r: self._calculate_result_score(r))
        return best_result.get("data", {}).get("results", [])[:limit]
    
    def _get_weighted_results(self, results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """加权结果 - 根据适配器优先级加权"""
        weighted_results = []
        
        for result in results:
            adapter_results = result.get("data", {}).get("results", [])
            adapter_name = result.get("data", {}).get("adapter", "unknown")
            
            # 获取适配器优先级
            adapter_priority = 1
            for adapter in self.adapters.values():
                if adapter.adapter_type == adapter_name:
                    adapter_priority = adapter.priority
                    break
            
            # 应用权重
            for item in adapter_results:
                weighted_score = item.get("score", 0) * (adapter_priority / 10)
                item["weighted_score"] = weighted_score
                weighted_results.append(item)
        
        # 按加权分数排序
        weighted_results.sort(key=lambda x: x.get("weighted_score", 0), reverse=True)
        
        return weighted_results[:limit]
    
    def _calculate_result_score(self, result: Dict[str, Any]) -> float:
        """计算结果分数"""
        adapter_results = result.get("data", {}).get("results", [])
        if not adapter_results:
            return 0.0
        
        # 计算平均分数
        total_score = sum(item.get("score", 0) for item in adapter_results)
        return total_score / len(adapter_results)
    
    def _forward_to_adapters(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """转发请求到适配器"""
        specified_adapters = context.get("adapters", [])
        
        if specified_adapters:
            # 转发到指定适配器
            if len(specified_adapters) == 1:
                adapter_name = specified_adapters[0]
                if adapter_name in self.adapters:
                    return self.adapters[adapter_name].process(context)
                else:
                    return {
                        "success": False,
                        "error": f"Adapter '{adapter_name}' not found"
                    }
            else:
                # 多个适配器并行处理
                results = []
                for adapter_name in specified_adapters:
                    if adapter_name in self.adapters:
                        result = self.adapters[adapter_name].process(context)
                        results.append(result)
                
                return {
                    "success": True,
                    "data": {
                        "results": results
                    }
                }
        else:
            return {
                "success": False,
                "error": "No adapters specified for forwarding"
            }
    
    def _handle_user_aware_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户感知操作 - 智能路由到用户画像适配器"""
        action = context.get("action")
        
        # 查找用户画像适配器
        user_profile_adapter = None
        for adapter_name, adapter in self.adapters.items():
            if hasattr(adapter, 'adapter_type') and adapter.adapter_type == "user_profile":
                user_profile_adapter = adapter
                break
        
        if not user_profile_adapter:
            # 如果没有用户画像适配器，尝试查找任何支持用户操作的适配器
            for adapter_name, adapter in self.adapters.items():
                if adapter.can_handle(context):
                    user_profile_adapter = adapter
                    break
        
        if user_profile_adapter:
            try:
                return user_profile_adapter.process(context)
            except Exception as e:
                self.logger.error(f"User-aware action '{action}' failed on adapter: {e}")
                return {
                    "success": False,
                    "error": f"User-aware action failed: {str(e)}",
                    "action": action,
                    "adapter_type": getattr(user_profile_adapter, 'adapter_type', 'unknown')
                }
        else:
            return {
                "success": False,
                "error": f"No suitable adapter found for user-aware action: {action}",
                "action": action,
                "suggestion": "Consider adding a UserProfileAdapter to handle user-aware operations"
            }
    
    def _get_adapters_info(self) -> Dict[str, Any]:
        """获取适配器信息"""
        adapters_info = []
        
        for name, adapter in self.adapters.items():
            adapters_info.append({
                "name": name,
                "type": adapter.adapter_type,
                "enabled": adapter.enabled,
                "priority": adapter.priority,
                "supported_query_types": adapter.supported_query_types
            })
        
        return {
            "success": True,
            "data": {
                "adapters": adapters_info,
                "total_count": len(self.adapters),
                "enabled_count": sum(1 for a in self.adapters.values() if a.enabled)
            }
        }
    
    def _set_session_state(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """设置会话状态"""
        key = context.get("key")
        value = context.get("value")
        
        if key is None:
            raise CellConfigurationError("Key is required for set_state action")
        
        self.session_state[key] = value
        
        return {
            "success": True,
            "data": {
                "key": key,
                "value": value
            }
        }
    
    def _get_state(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取状态信息"""
        include_adapters = context.get("include_adapters", True)
        
        state = {
            "session_state": self.session_state,
            "configuration": {
                "routing_strategy": self.routing_strategy,
                "result_aggregation": self.result_aggregation,
                "max_results_per_adapter": self.max_results_per_adapter,
                "enable_caching": self.enable_caching,
                "cache_ttl": self.cache_ttl
            },
            "cache_stats": {
                "cached_queries": len(self.query_cache),
                "cache_enabled": self.enable_caching
            }
        }
        
        if include_adapters:
            adapters_info = self._get_adapters_info()
            state["adapters"] = adapters_info["data"]["adapters"]
        
        return {
            "success": True,
            "data": state
        }
    
    def _clear_cache(self) -> Dict[str, Any]:
        """清理查询缓存"""
        cleared_count = len(self.query_cache)
        self.query_cache.clear()
        
        return {
            "success": True,
            "data": {
                "cleared_count": cleared_count
            }
        }
    
    def _generate_cache_key(self, query: str, query_type: str, limit: int) -> str:
        """生成缓存键"""
        key_data = f"{query}|{query_type}|{limit}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        if cache_key in self.query_cache:
            cached_data = self.query_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["result"]
            else:
                # 清理过期缓存
                del self.query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """缓存结果"""
        self.query_cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
        
        # 限制缓存大小
        if len(self.query_cache) > 100:
            # 删除最旧的缓存项
            oldest_key = min(self.query_cache.keys(), 
                           key=lambda k: self.query_cache[k]["timestamp"])
            del self.query_cache[oldest_key]
    
    # 便捷方法
    def search(self, query: str, query_type: str = "general", limit: int = 10, 
              adapters: List[str] = None) -> List[Dict[str, Any]]:
        """便捷的搜索方法"""
        result = self.process({
            "action": "search",
            "query": query,
            "query_type": query_type,
            "limit": limit,
            "adapters": adapters or []
        })
        
        if result["success"]:
            return result["data"]["results"]
        else:
            raise Exception(f"Search failed: {result.get('error', 'Unknown error')}")
    
    def set_state(self, key: str, value: Any):
        """便捷的状态设置方法"""
        result = self.process({
            "action": "set_state",
            "key": key,
            "value": value
        })
        if not result["success"]:
            raise Exception(f"Failed to set state: {result.get('error', 'Unknown error')}")
    
    def get_state_value(self, key: str, default: Any = None) -> Any:
        """便捷的状态获取方法"""
        return self.session_state.get(key, default)
    
    # 用户感知便捷方法
    def get_user_profile(self, user_id: str = None) -> Dict[str, Any]:
        """便捷的用户画像获取方法"""
        result = self.process({
            "action": "get_user_profile",
            "user_id": user_id
        })
        if result["success"]:
            return result["data"]
        else:
            raise Exception(f"Get user profile failed: {result.get('error', 'Unknown error')}")
    
    def update_user_profile(self, updates: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """便捷的用户画像更新方法"""
        result = self.process({
            "action": "update_user_profile",
            "updates": updates,
            "user_id": user_id
        })
        if result["success"]:
            return result["data"]
        else:
            raise Exception(f"Update user profile failed: {result.get('error', 'Unknown error')}")
    
    def get_user_preferences(self, category: str = None, user_id: str = None) -> Dict[str, Any]:
        """便捷的用户偏好获取方法"""
        context = {
            "action": "get_user_preferences",
            "user_id": user_id
        }
        if category:
            context["category"] = category
        
        result = self.process(context)
        if result["success"]:
            return result["data"]
        else:
            raise Exception(f"Get user preferences failed: {result.get('error', 'Unknown error')}")
    
    def learn_user_preference(self, category: str, preference: str, feedback: float, user_id: str = None) -> Dict[str, Any]:
        """便捷的用户偏好学习方法"""
        result = self.process({
            "action": "learn_preference",
            "category": category,
            "preference": preference,
            "feedback": feedback,
            "user_id": user_id
        })
        if result["success"]:
            return result["data"]
        else:
            raise Exception(f"Learn user preference failed: {result.get('error', 'Unknown error')}")
    
    def add_user_memory(self, content: str, memory_type: str = "learned", importance: float = 0.5,
                       tags: List[str] = None, context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
        """便捷的用户记忆添加方法"""
        request_context = {
            "action": "add_user_memory",
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "user_id": user_id
        }
        if tags:
            request_context["tags"] = tags
        if context:
            request_context["context"] = context
        
        result = self.process(request_context)
        if result["success"]:
            return result["data"]
        else:
            raise Exception(f"Add user memory failed: {result.get('error', 'Unknown error')}")
    
    def get_user_memories(self, memory_type: str = None, tags: List[str] = None, 
                         limit: int = 10, user_id: str = None) -> List[Dict[str, Any]]:
        """便捷的用户记忆获取方法"""
        context = {
            "action": "get_user_memories",
            "limit": limit,
            "user_id": user_id
        }
        if memory_type:
            context["memory_type"] = memory_type
        if tags:
            context["tags"] = tags
        
        result = self.process(context)
        if result["success"]:
            return result["data"]["results"]
        else:
            raise Exception(f"Get user memories failed: {result.get('error', 'Unknown error')}")
    
    def process_user_input(self, user_input: str, conversation_context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
        """便捷的用户输入处理方法"""
        context = {
            "action": "process_user_input",
            "user_input": user_input,
            "user_id": user_id
        }
        if conversation_context:
            context["conversation_context"] = conversation_context
        
        result = self.process(context)
        if result["success"]:
            return result["data"]
        else:
            raise Exception(f"Process user input failed: {result.get('error', 'Unknown error')}")
    
    def handle_mention(self, mention: str, mention_context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
        """便捷的@引用处理方法"""
        context = {
            "action": "handle_mention",
            "mention": mention,
            "user_id": user_id
        }
        if mention_context:
            context["context"] = mention_context
        
        result = self.process(context)
        if result["success"]:
            return result["data"]
        else:
            raise Exception(f"Handle mention failed: {result.get('error', 'Unknown error')}")
    
    def add_adapter(self, name: str, class_path: str, config: Dict[str, Any] = None):
        """动态添加适配器"""
        if config is None:
            config = {}
        
        adapter = self._load_adapter(class_path, config)
        if adapter:
            self.adapters[name] = adapter
            self.adapter_registry[name] = class_path
            self.logger.info(f"Added adapter: {name} ({class_path})")
            return True
        else:
            self.logger.error(f"Failed to add adapter: {name} ({class_path})")
            return False
    
    def add_adapter_instance(self, name: str, adapter: MemoryAdapter):
        """直接添加适配器实例"""
        self.adapters[name] = adapter
        self.adapter_registry[name] = f"{adapter.__class__.__module__}.{adapter.__class__.__name__}"
        self.logger.info(f"Added adapter instance: {name} ({adapter.adapter_type})")
    
    def remove_adapter(self, name: str):
        """移除适配器"""
        if name in self.adapters:
            # 关闭适配器资源
            adapter = self.adapters[name]
            if hasattr(adapter, 'close'):
                adapter.close()
            
            del self.adapters[name]
            if name in self.adapter_registry:
                del self.adapter_registry[name]
            
            self.logger.info(f"Removed adapter: {name}")
            return True
        else:
            self.logger.warning(f"Adapter not found: {name}")
            return False
    
    def reload_adapter(self, name: str):
        """重新加载适配器"""
        if name not in self.adapter_registry:
            self.logger.error(f"Cannot reload adapter {name}: not found in registry")
            return False
        
        class_path = self.adapter_registry[name]
        
        # 获取当前配置
        current_adapter = self.adapters.get(name)
        config = current_adapter.config if current_adapter else {}
        
        # 移除当前适配器
        self.remove_adapter(name)
        
        # 重新加载
        return self.add_adapter(name, class_path, config)
    
    def list_available_adapters(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用的适配器"""
        available_adapters = {}
        
        for name, adapter in self.adapters.items():
            available_adapters[name] = {
                "class_path": self.adapter_registry.get(name, "unknown"),
                "adapter_type": adapter.adapter_type,
                "enabled": adapter.enabled,
                "priority": adapter.priority,
                "supported_query_types": adapter.supported_query_types
            }
        
        return available_adapters
    
    def close(self):
        """关闭资源"""
        try:
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=True)
                self.logger.info("Thread pool executor closed")
            
            # 关闭适配器
            for adapter in self.adapters.values():
                if hasattr(adapter, 'close'):
                    adapter.close()
            
            self.logger.info("StateMemoryCell (适配器架构) closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing StateMemoryCell: {e}")
    
    def __del__(self):
        """析构函数"""
        self.close()


# 为了向后兼容，保留MemoryEntry类
class MemoryEntry:
    """记忆条目类 - 向后兼容"""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None, 
                 memory_type: str = "general", importance: float = 1.0):
        self.content = content
        self.metadata = metadata or {}
        self.memory_type = memory_type
        self.importance = importance
        self.timestamp = datetime.now()
        self.access_count = 0
        self.last_accessed = self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """从字典创建"""
        entry = cls(
            content=data["content"],
            metadata=data.get("metadata", {}),
            memory_type=data.get("memory_type", "general"),
            importance=data.get("importance", 1.0)
        )
        
        if "timestamp" in data:
            entry.timestamp = datetime.fromisoformat(data["timestamp"])
        if "access_count" in data:
            entry.access_count = data["access_count"]
        if "last_accessed" in data:
            entry.last_accessed = datetime.fromisoformat(data["last_accessed"])
        
        return entry 