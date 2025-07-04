"""
FastGPT 知识库适配器

连接FastGPT知识库服务的适配器实现。
支持知识库搜索、管理等功能。
"""
from typing import Dict, Any, Optional
from .base_adapter import MemoryAdapter
from ..core.exceptions import CellConfigurationError

try:
    import requests
    HTTP_SUPPORT = True
except ImportError:
    HTTP_SUPPORT = False
    requests = None


class FastGPTAdapter(MemoryAdapter):
    """FastGPT知识库适配器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 检查HTTP支持
        if not HTTP_SUPPORT:
            raise CellConfigurationError("requests library is required for FastGPT adapter")
        
        # FastGPT配置
        self.base_url = self.config.get("base_url", "http://localhost:3000")
        self.api_key = self.config.get("api_key")
        self.dataset_id = self.config.get("dataset_id")
        
        # 搜索配置
        self.default_limit = self.config.get("default_limit", 5000)  # token限制
        self.default_similarity = self.config.get("default_similarity", 0.0)
        self.search_mode = self.config.get("search_mode", "embedding")  # embedding | fullTextRecall | mixedRecall
        self.using_rerank = self.config.get("using_rerank", False)
        
        # 问题优化配置
        self.extension_query = self.config.get("extension_query", True)
        self.extension_model = self.config.get("extension_model", "gpt-4o-mini")
        self.extension_bg = self.config.get("extension_bg", "")
        
        # 验证必要配置
        if not self.api_key:
            raise CellConfigurationError("FastGPT API key is required")
        if not self.dataset_id:
            raise CellConfigurationError("FastGPT dataset_id is required")
        
        self.logger.info(f"FastGPT Adapter initialized: {self.base_url}, dataset: {self.dataset_id}")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理FastGPT知识库查询"""
        action = context.get("action", "search")
        
        if action == "search":
            return self._search_knowledge(context)
        elif action == "get_datasets":
            return self._get_datasets()
        elif action == "get_dataset_detail":
            return self._get_dataset_detail(context)
        else:
            return {
                "success": False,
                "error": f"Unsupported action: {action}",
                "adapter": self.adapter_type
            }
    
    def _search_knowledge(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """搜索知识库"""
        query = context.get("query", "")
        limit = context.get("limit", self.default_limit)
        similarity = context.get("similarity", self.default_similarity)
        search_mode = context.get("search_mode", self.search_mode)
        
        if not query.strip():
            return {
                "success": False,
                "error": "Query is required for search",
                "adapter": self.adapter_type
            }
        
        try:
            # 构建请求
            url = f"{self.base_url}/api/core/dataset/searchTest"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "datasetId": self.dataset_id,
                "text": query,
                "limit": limit,
                "similarity": similarity,
                "searchMode": search_mode,
                "usingReRank": self.using_rerank,
                "datasetSearchUsingExtensionQuery": self.extension_query,
                "datasetSearchExtensionModel": self.extension_model,
                "datasetSearchExtensionBg": self.extension_bg
            }
            
            # 发送请求
            self.logger.info(f"FastGPT API URL: {url}")
            self.logger.info(f"FastGPT payload: {payload}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            self.logger.info(f"FastGPT API response: {result}")
            
            if result.get("code") == 200:
                raw_results = result.get("data", {}).get("list", [])
                normalized_results = self.normalize_results(raw_results)
                
                self.logger.info(f"FastGPT search returned {len(normalized_results)} results for query: '{query}'")
                
                return {
                    "success": True,
                    "data": {
                        "results": normalized_results,
                        "total_found": len(normalized_results),
                        "query": query,
                        "search_mode": search_mode,
                        "adapter": self.adapter_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error from FastGPT"),
                    "adapter": self.adapter_type
                }
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"FastGPT request failed: {e}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "adapter": self.adapter_type
            }
        except Exception as e:
            self.logger.error(f"FastGPT search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "adapter": self.adapter_type
            }
    
    def _get_datasets(self) -> Dict[str, Any]:
        """获取知识库列表"""
        try:
            url = f"{self.base_url}/api/core/dataset/list"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {"parentId": ""}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 200:
                datasets = result.get("data", [])
                return {
                    "success": True,
                    "data": {
                        "datasets": datasets,
                        "adapter": self.adapter_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Failed to get datasets"),
                    "adapter": self.adapter_type
                }
                
        except Exception as e:
            self.logger.error(f"Get datasets error: {e}")
            return {
                "success": False,
                "error": str(e),
                "adapter": self.adapter_type
            }
    
    def _get_dataset_detail(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取知识库详情"""
        dataset_id = context.get("dataset_id", self.dataset_id)
        
        try:
            url = f"{self.base_url}/api/core/dataset/detail"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            params = {"id": dataset_id}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 200:
                dataset_detail = result.get("data", {})
                return {
                    "success": True,
                    "data": {
                        "dataset": dataset_detail,
                        "adapter": self.adapter_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Failed to get dataset detail"),
                    "adapter": self.adapter_type
                }
                
        except Exception as e:
            self.logger.error(f"Get dataset detail error: {e}")
            return {
                "success": False,
                "error": str(e),
                "adapter": self.adapter_type
            }
    
    def query(self, query_text: str) -> str:
        """便捷的查询接口"""
        context = {
            "action": "search",
            "query": query_text
        }
        
        result = self.process(context)
        
        if result.get("success"):
            # 提取并组合所有搜索结果的内容
            data = result.get("data", {})
            results = data.get("results", [])
            
            if not results:
                return "知识库中没有找到相关信息。"
            
            # 组合搜索结果
            combined_content = []
            for item in results[:3]:  # 只取前3个最相关的结果
                content = item.get("content", "")
                additional = item.get("additional_content", "")
                score = item.get("score", 0.0)
                
                if content:
                    # 处理FastGPT的score格式：[{'type': 'embedding', 'value': 0.xx}, ...]
                    if isinstance(score, list) and len(score) > 0:
                        # 取第一个score值，通常是embedding score
                        first_score = score[0]
                        if isinstance(first_score, dict) and 'value' in first_score:
                            score_text = f"{first_score['value']:.2f}"
                        else:
                            score_text = str(score)
                    elif isinstance(score, (int, float)):
                        score_text = f"{score:.2f}"
                    else:
                        score_text = str(score)
                    
                    result_text = f"相关度: {score_text}\n内容: {content}"
                    if additional:
                        result_text += f"\n补充: {additional}"
                    combined_content.append(result_text)
            
            if combined_content:
                return f"从知识库找到 {len(results)} 条相关信息：\n\n" + "\n\n---\n\n".join(combined_content)
            else:
                return "知识库搜索完成，但没有找到有效内容。"
        else:
            error_msg = result.get("error", "Unknown error")
            self.logger.error(f"Knowledge query failed: {error_msg}")
            return f"知识库查询失败: {error_msg}"
    
    def _normalize_single_result(self, item: Any) -> Dict[str, Any]:
        """标准化FastGPT搜索结果"""
        if isinstance(item, dict):
            return {
                "id": item.get("id", ""),
                "content": item.get("q", ""),
                "additional_content": item.get("a", ""),
                "score": item.get("score", 0.0),
                "source": f"FastGPT-{item.get('sourceName', 'Unknown')}",
                "metadata": {
                    "dataset_id": item.get("datasetId", ""),
                    "collection_id": item.get("collectionId", ""),
                    "source_name": item.get("sourceName", ""),
                    "source_id": item.get("sourceId", ""),
                    "chunk_index": item.get("chunkIndex")
                },
                "raw_data": item
            }
        else:
            return super()._normalize_single_result(item) 