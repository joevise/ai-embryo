"""
记忆适配器基类

所有外部记忆服务适配器的基类，定义统一接口和标准化方法。
"""
import hashlib
from typing import Dict, Any, List, Optional
from ..core.cell import Cell


class MemoryAdapter(Cell):
    """记忆适配器基类 - 所有外部记忆服务适配器的基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.adapter_type = self.__class__.__name__
        self.enabled = self.config.get("enabled", True)
        self.priority = self.config.get("priority", 1)  # 优先级，数字越大优先级越高
        self.supported_query_types = self.config.get("supported_query_types", ["all"])
    
    def can_handle(self, query_context: Dict[str, Any]) -> bool:
        """判断是否能处理该查询"""
        if not self.enabled:
            return False
        
        query_type = query_context.get("query_type", "general")
        return "all" in self.supported_query_types or query_type in self.supported_query_types
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理查询请求 - 子类必须实现"""
        raise NotImplementedError("Adapter must implement process method")
    
    def normalize_results(self, raw_results: Any) -> List[Dict[str, Any]]:
        """标准化返回结果格式"""
        if not raw_results:
            return []
        
        # 标准化结果格式
        normalized = []
        if isinstance(raw_results, list):
            for item in raw_results:
                normalized.append(self._normalize_single_result(item))
        else:
            normalized.append(self._normalize_single_result(raw_results))
        
        return normalized
    
    def _normalize_single_result(self, item: Any) -> Dict[str, Any]:
        """标准化单个结果项"""
        if isinstance(item, dict):
            return {
                "id": item.get("id", ""),
                "content": item.get("content", item.get("q", "")),
                "additional_content": item.get("additional_content", item.get("a", "")),
                "score": item.get("score", item.get("similarity", 0.0)),
                "source": item.get("source", self.adapter_type),
                "metadata": item.get("metadata", {}),
                "raw_data": item
            }
        else:
            return {
                "id": hashlib.md5(str(item).encode()).hexdigest()[:12],
                "content": str(item),
                "additional_content": "",
                "score": 0.5,
                "source": self.adapter_type,
                "metadata": {},
                "raw_data": item
            }
    
    def close(self):
        """关闭适配器资源 - 子类可以重写"""
        pass 