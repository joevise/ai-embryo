"""
StateMemoryCell 适配器架构测试

测试重构后的StateMemoryCell的基本功能
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from futurembryo.cells.state_memory_cell import StateMemoryCell, MemoryAdapter, FastGPTAdapter


class MockAdapter(MemoryAdapter):
    """模拟适配器用于测试"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.call_count = 0
    
    def process(self, context):
        self.call_count += 1
        query = context.get("query", "")
        
        # 模拟搜索结果
        mock_results = [
            {
                "id": f"mock_{i}",
                "content": f"Mock result {i} for query: {query}",
                "additional_content": f"Additional content {i}",
                "score": 0.9 - i * 0.1,
                "source": "MockAdapter",
                "metadata": {"mock": True},
                "raw_data": {"original": f"data_{i}"}
            }
            for i in range(3)
        ]
        
        return {
            "success": True,
            "data": {
                "results": mock_results,
                "total_found": len(mock_results),
                "query": query,
                "adapter": self.adapter_type
            }
        }


class TestStateMemoryCellAdapter(unittest.TestCase):
    """StateMemoryCell适配器架构测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            "routing_strategy": "priority",
            "result_aggregation": "merge",
            "enable_caching": True,
            "cache_ttl": 60,
            "adapters": [
                {
                    "type": "MockAdapter",
                    "name": "mock_adapter_1",
                    "config": {
                        "priority": 10,
                        "enabled": True,
                        "supported_query_types": ["all"]
                    }
                }
            ]
        }
    
    def test_initialization(self):
        """测试初始化"""
        # 由于MockAdapter不在_init_adapters中注册，我们手动创建
        memory_cell = StateMemoryCell({
            "routing_strategy": "priority",
            "result_aggregation": "merge",
            "enable_caching": True
        })
        
        # 手动添加模拟适配器
        mock_adapter = MockAdapter({"priority": 10, "enabled": True})
        memory_cell.add_adapter("mock_adapter", mock_adapter)
        
        self.assertEqual(len(memory_cell.adapters), 1)
        self.assertIn("mock_adapter", memory_cell.adapters)
        self.assertEqual(memory_cell.routing_strategy, "priority")
        self.assertEqual(memory_cell.result_aggregation, "merge")
        self.assertTrue(memory_cell.enable_caching)
    
    def test_adapter_management(self):
        """测试适配器管理"""
        memory_cell = StateMemoryCell({})
        
        # 添加适配器
        adapter1 = MockAdapter({"priority": 10})
        adapter2 = MockAdapter({"priority": 5})
        
        memory_cell.add_adapter("adapter1", adapter1)
        memory_cell.add_adapter("adapter2", adapter2)
        
        self.assertEqual(len(memory_cell.adapters), 2)
        
        # 获取适配器信息
        info = memory_cell.process({"action": "get_adapters"})
        self.assertTrue(info["success"])
        self.assertEqual(info["data"]["total_count"], 2)
        
        # 移除适配器
        memory_cell.remove_adapter("adapter1")
        self.assertEqual(len(memory_cell.adapters), 1)
        self.assertNotIn("adapter1", memory_cell.adapters)
    
    def test_search_functionality(self):
        """测试搜索功能"""
        memory_cell = StateMemoryCell({})
        mock_adapter = MockAdapter({"priority": 10, "enabled": True})
        memory_cell.add_adapter("mock_adapter", mock_adapter)
        
        # 测试搜索
        results = memory_cell.search("test query", limit=5)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(mock_adapter.call_count, 1)
        
        # 验证结果格式
        for result in results:
            self.assertIn("id", result)
            self.assertIn("content", result)
            self.assertIn("score", result)
            self.assertIn("source", result)
    
    def test_routing_strategies(self):
        """测试路由策略"""
        memory_cell = StateMemoryCell({"routing_strategy": "parallel"})
        
        # 添加多个适配器
        adapter1 = MockAdapter({"priority": 10, "enabled": True})
        adapter2 = MockAdapter({"priority": 5, "enabled": True})
        
        memory_cell.add_adapter("adapter1", adapter1)
        memory_cell.add_adapter("adapter2", adapter2)
        
        # 测试并行路由
        result = memory_cell.process({
            "action": "search",
            "query": "test parallel",
            "routing_strategy": "parallel",
            "limit": 5
        })
        
        self.assertTrue(result["success"])
        self.assertGreater(len(result["data"]["results"]), 0)
        
        # 验证两个适配器都被调用
        self.assertEqual(adapter1.call_count, 1)
        self.assertEqual(adapter2.call_count, 1)
    
    def test_session_state(self):
        """测试会话状态管理"""
        memory_cell = StateMemoryCell({})
        
        # 设置状态
        memory_cell.set_state("test_key", "test_value")
        
        # 获取状态
        value = memory_cell.get_state_value("test_key")
        self.assertEqual(value, "test_value")
        
        # 获取不存在的键
        default_value = memory_cell.get_state_value("nonexistent", "default")
        self.assertEqual(default_value, "default")
        
        # 获取完整状态
        state = memory_cell.process({"action": "get_state"})
        self.assertTrue(state["success"])
        self.assertIn("test_key", state["data"]["session_state"])
    
    def test_caching(self):
        """测试缓存功能"""
        memory_cell = StateMemoryCell({"enable_caching": True, "cache_ttl": 60})
        mock_adapter = MockAdapter({"priority": 10, "enabled": True})
        memory_cell.add_adapter("mock_adapter", mock_adapter)
        
        # 第一次搜索
        results1 = memory_cell.search("cache test", limit=3)
        call_count_1 = mock_adapter.call_count
        
        # 第二次相同搜索（应该从缓存返回）
        results2 = memory_cell.search("cache test", limit=3)
        call_count_2 = mock_adapter.call_count
        
        # 验证缓存工作
        self.assertEqual(len(results1), len(results2))
        self.assertEqual(call_count_1, call_count_2)  # 适配器没有被再次调用
    
    def test_result_aggregation(self):
        """测试结果聚合"""
        memory_cell = StateMemoryCell({"result_aggregation": "merge"})
        
        # 添加多个适配器
        adapter1 = MockAdapter({"priority": 10, "enabled": True})
        adapter2 = MockAdapter({"priority": 5, "enabled": True})
        
        memory_cell.add_adapter("adapter1", adapter1)
        memory_cell.add_adapter("adapter2", adapter2)
        
        # 测试合并聚合
        result = memory_cell.process({
            "action": "search",
            "query": "aggregation test",
            "routing_strategy": "parallel",
            "limit": 10
        })
        
        self.assertTrue(result["success"])
        results = result["data"]["results"]
        
        # 验证结果被合并且去重
        self.assertGreater(len(results), 0)
        
        # 验证结果按分数排序
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_error_handling(self):
        """测试错误处理"""
        memory_cell = StateMemoryCell({})
        
        # 测试无适配器的情况
        result = memory_cell.process({
            "action": "search",
            "query": "test",
            "limit": 5
        })
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        
        # 测试空查询
        mock_adapter = MockAdapter({"priority": 10, "enabled": True})
        memory_cell.add_adapter("mock_adapter", mock_adapter)
        
        result = memory_cell.process({
            "action": "search",
            "query": "",
            "limit": 5
        })
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_adapter_selection(self):
        """测试适配器选择"""
        memory_cell = StateMemoryCell({})
        
        # 创建支持不同查询类型的适配器
        tech_adapter = MockAdapter({
            "priority": 10,
            "enabled": True,
            "supported_query_types": ["technical"]
        })
        
        general_adapter = MockAdapter({
            "priority": 5,
            "enabled": True,
            "supported_query_types": ["general"]
        })
        
        memory_cell.add_adapter("tech_adapter", tech_adapter)
        memory_cell.add_adapter("general_adapter", general_adapter)
        
        # 测试技术查询
        result = memory_cell.process({
            "action": "search",
            "query": "technical question",
            "query_type": "technical",
            "limit": 5
        })
        
        self.assertTrue(result["success"])
        # 技术适配器应该被选中
        self.assertEqual(tech_adapter.call_count, 1)
        self.assertEqual(general_adapter.call_count, 0)


class TestMemoryAdapter(unittest.TestCase):
    """MemoryAdapter基类测试"""
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        config = {
            "enabled": True,
            "priority": 5,
            "supported_query_types": ["test"]
        }
        
        adapter = MockAdapter(config)
        
        self.assertTrue(adapter.enabled)
        self.assertEqual(adapter.priority, 5)
        self.assertEqual(adapter.supported_query_types, ["test"])
        self.assertEqual(adapter.adapter_type, "MockAdapter")
    
    def test_can_handle(self):
        """测试查询处理能力判断"""
        adapter = MockAdapter({
            "enabled": True,
            "supported_query_types": ["technical", "factual"]
        })
        
        # 测试支持的查询类型
        self.assertTrue(adapter.can_handle({"query_type": "technical"}))
        self.assertTrue(adapter.can_handle({"query_type": "factual"}))
        
        # 测试不支持的查询类型
        self.assertFalse(adapter.can_handle({"query_type": "general"}))
        
        # 测试禁用的适配器
        adapter.enabled = False
        self.assertFalse(adapter.can_handle({"query_type": "technical"}))
    
    def test_normalize_results(self):
        """测试结果标准化"""
        adapter = MockAdapter({})
        
        # 测试字典结果
        raw_results = [
            {"id": "1", "content": "test", "score": 0.9},
            {"q": "question", "a": "answer", "similarity": 0.8}
        ]
        
        normalized = adapter.normalize_results(raw_results)
        
        self.assertEqual(len(normalized), 2)
        for result in normalized:
            self.assertIn("id", result)
            self.assertIn("content", result)
            self.assertIn("score", result)
            self.assertIn("source", result)
        
        # 测试字符串结果
        string_result = "simple text result"
        normalized = adapter.normalize_results(string_result)
        
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["content"], string_result)


@patch('requests.post')
class TestFastGPTAdapter(unittest.TestCase):
    """FastGPTAdapter测试（模拟HTTP请求）"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            "base_url": "https://api.fastgpt.in",
            "api_key": "test-api-key",
            "dataset_id": "test-dataset-id",
            "search_mode": "embedding",
            "priority": 10
        }
    
    def test_fastgpt_adapter_initialization(self, mock_post):
        """测试FastGPT适配器初始化"""
        adapter = FastGPTAdapter(self.config)
        
        self.assertEqual(adapter.base_url, "https://api.fastgpt.in")
        self.assertEqual(adapter.api_key, "test-api-key")
        self.assertEqual(adapter.dataset_id, "test-dataset-id")
        self.assertEqual(adapter.search_mode, "embedding")
    
    def test_fastgpt_search(self, mock_post):
        """测试FastGPT搜索功能"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "data": [
                {
                    "id": "test-id",
                    "q": "test question",
                    "a": "test answer",
                    "score": 0.95,
                    "sourceName": "test source"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        adapter = FastGPTAdapter(self.config)
        
        result = adapter.process({
            "action": "search",
            "query": "test query",
            "limit": 5
        })
        
        self.assertTrue(result["success"])
        self.assertIn("results", result["data"])
        self.assertEqual(len(result["data"]["results"]), 1)
        
        # 验证API调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("api/core/dataset/searchTest", call_args[1]["url"])
    
    def test_fastgpt_error_handling(self, mock_post):
        """测试FastGPT错误处理"""
        # 模拟API错误
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 400,
            "message": "Invalid request"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        adapter = FastGPTAdapter(self.config)
        
        result = adapter.process({
            "action": "search",
            "query": "test query"
        })
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2) 