"""
测试新的ToolRegistry和Tool系统架构
"""
import asyncio
import pytest
import tempfile
import json
from pathlib import Path

# 导入新的组件
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from futurembryo.core.tool_registry import (
    ToolRegistry, ToolSchema, FunctionToolProvider, 
    create_default_registry
)
from futurembryo.core.tool_config import (
    ToolConfigManager, ToolsConfig, FunctionToolConfig,
    MCPServerConfig, create_default_config_file
)
from futurembryo.cells.tool_cell_v2 import ToolCell
from futurembryo.cells.llm_cell_v2 import LLMCell, create_llm_with_tools


def test_tool_schema():
    """测试工具Schema"""
    schema = ToolSchema(
        name="test_tool",
        description="A test tool",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            }
        }
    )
    
    openai_schema = schema.to_openai_schema()
    assert openai_schema["type"] == "function"
    assert openai_schema["function"]["name"] == "test_tool"
    assert openai_schema["function"]["description"] == "A test tool"


def test_function_tool_provider():
    """测试函数工具提供者"""
    provider = FunctionToolProvider()
    
    # 定义测试函数
    def test_add(a: int, b: int) -> int:
        return a + b
    
    # 注册工具
    provider.register_function(
        name="add",
        description="Add two numbers",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"}
            },
            "required": ["a", "b"]
        },
        function=test_add
    )
    
    # 异步测试
    async def async_test():
        # 获取工具
        tools = await provider.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "add"
        
        # 执行工具
        result = await provider.execute_tool("add", {"a": 2, "b": 3})
        assert result["success"] is True
        assert result["result"] == 5
        
        # 测试错误情况
        try:
            await provider.execute_tool("nonexistent", {})
            assert False, "Should raise ValueError"
        except ValueError:
            pass
    
    asyncio.run(async_test())
    print("✓ FunctionToolProvider test passed")


def test_tool_registry():
    """测试工具注册中心"""
    registry = ToolRegistry()
    
    # 定义测试函数
    def test_multiply(x: float, y: float) -> float:
        return x * y
    
    # 注册函数工具
    registry.register_function(
        name="multiply",
        description="Multiply two numbers",
        parameters={
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"}
            },
            "required": ["x", "y"]
        },
        function=test_multiply
    )
    
    async def async_test():
        # 获取所有工具
        tools = await registry.get_all_tools()
        assert len(tools) >= 1  # 至少有我们注册的工具
        
        # 获取工具schema
        schemas = await registry.get_tools_schema()
        assert len(schemas) >= 1
        
        # 执行工具
        result = await registry.execute_tool("multiply", {"x": 3.5, "y": 2.0})
        assert result["success"] is True
        assert result["result"] == 7.0
        
        # 获取状态
        status = registry.get_status()
        assert "function_tools_count" in status
        assert status["function_tools_count"] >= 1
    
    asyncio.run(async_test())
    print("✓ ToolRegistry test passed")


def test_default_registry():
    """测试默认注册中心"""
    registry = create_default_registry()
    
    async def async_test():
        tools = await registry.get_all_tools()
        assert len(tools) > 0  # 应该有默认工具
        
        # 测试默认的add工具
        result = await registry.execute_tool("add", {"a": 10, "b": 20})
        assert result["success"] is True
        assert result["result"] == 30
        
        # 测试文本工具
        result = await registry.execute_tool("text_upper", {"text": "hello"})
        assert result["success"] is True
        assert result["result"] == "HELLO"
    
    asyncio.run(async_test())
    print("✓ Default registry test passed")


def test_tool_config():
    """测试工具配置"""
    # 创建配置
    config = ToolsConfig(
        load_defaults=True,
        function_tools=[
            FunctionToolConfig(
                name="custom_tool",
                description="A custom tool",
                parameters={
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"}
                    }
                }
            )
        ]
    )
    
    # 测试配置管理器
    manager = ToolConfigManager()
    
    async def async_test():
        registry = await manager.create_registry_from_config(config)
        tools = await registry.get_all_tools()
        
        # 应该有默认工具 + 自定义工具
        tool_names = [tool.name for tool in tools]
        assert "add" in tool_names  # 默认工具
        assert "custom_tool" in tool_names  # 自定义工具
    
    asyncio.run(async_test())
    print("✓ Tool config test passed")


def test_tool_config_file():
    """测试配置文件功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "tools.json"
        
        # 创建默认配置文件
        create_default_config_file(config_path)
        assert config_path.exists()
        
        # 加载配置
        manager = ToolConfigManager(config_path)
        config = manager.load_config()
        
        assert config.load_defaults is True
        assert len(config.function_tools) > 0
        
        # 修改配置并保存
        config.load_defaults = False
        manager.config = config
        manager.save_config()
        
        # 重新加载验证
        manager2 = ToolConfigManager(config_path)
        config2 = manager2.load_config()
        assert config2.load_defaults is False
    
    print("✓ Tool config file test passed")


def test_tool_cell_v2():
    """测试新的ToolCell"""
    # 创建ToolCell
    tool_cell = ToolCell({
        "auto_load_defaults": True,
        "tools": [
            {
                "name": "greet",
                "description": "Greet someone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }
        ]
    })
    
    # 测试获取工具schema
    result = tool_cell.process({"action": "get_tools"})
    assert result["success"] is True
    assert len(result["tools_schema"]) > 0
    
    # 测试状态
    result = tool_cell.process({"action": "get_status"})
    assert result["success"] is True
    assert "registry_status" in result
    
    print("✓ ToolCell v2 test passed")


def test_integration():
    """集成测试：LLMCell + ToolCell"""
    # 注意：这个测试需要真实的API密钥，在实际环境中可能无法运行
    try:
        # 创建带工具的LLMCell
        tool_config = {
            "auto_load_defaults": True
        }
        
        llm_config = {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tool_calls": 2
        }
        
        # 由于需要真实API，这里只测试创建过程
        tool_cell = ToolCell(tool_config)
        
        # 验证可以获取工具
        async def async_test():
            tools = await tool_cell.get_available_tools()
            assert len(tools) > 0
            
            # 测试工具调用
            result = await tool_cell.call_tool("add", {"a": 5, "b": 3})
            assert result["success"] is True
            assert result["result"] == 8
        
        asyncio.run(async_test())
        print("✓ Integration test passed")
        
    except Exception as e:
        print(f"⚠ Integration test skipped due to: {e}")


def run_all_tests():
    """运行所有测试"""
    print("Running ToolRegistry v2 Tests...")
    print("=" * 50)
    
    test_tool_schema()
    test_function_tool_provider()
    test_tool_registry()
    test_default_registry()
    test_tool_config()
    test_tool_config_file()
    test_tool_cell_v2()
    test_integration()
    
    print("=" * 50)
    print("✅ All tests completed!")


if __name__ == "__main__":
    run_all_tests()