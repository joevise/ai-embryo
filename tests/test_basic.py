"""
FuturEmbryo基础功能测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from futurembryo import (
        Cell, CellState, LLMCell, GlobalConfig,
        setup_futurx_api, CellConfigurationError
    )
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


class TestCell(Cell):
    """测试用的简单Cell实现"""
    
    def process(self, context):
        input_text = context.get("input", "")
        return {
            "output": f"Processed: {input_text}",
            "length": len(input_text)
        }


def test_cell_state_enum():
    """测试CellState枚举"""
    # 测试状态值
    assert CellState.IDLE.value == "idle"
    assert CellState.PROCESSING.value == "processing"
    assert CellState.COMPLETED.value == "completed"
    
    # 测试活跃状态判断
    assert CellState.PROCESSING.is_active()
    assert not CellState.COMPLETED.is_active()
    
    # 测试最终状态判断
    assert CellState.COMPLETED.is_final()
    assert not CellState.PROCESSING.is_final()


def test_global_config():
    """测试全局配置"""
    config = GlobalConfig()
    
    # 测试设置和获取配置
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"
    
    # 测试默认值
    assert config.get("non_existent", "default") == "default"
    
    # 测试FuturX API设置
    setup_futurx_api("test_key", "https://test.example.com")
    assert config.get_api_key("openai") == "test_key"
    assert config.get_api_base_url("openai") == "https://test.example.com"


def test_cell_basic_functionality():
    """测试Cell基础功能"""
    cell = TestCell()
    
    # 测试初始状态
    assert cell.state == CellState.IDLE
    assert cell.execution_count == 0
    
    # 测试执行
    result = cell({"input": "Hello World"})
    
    # 验证返回格式
    assert result["success"] is True
    assert "data" in result
    assert "metadata" in result
    
    # 验证数据内容
    data = result["data"]
    assert data["output"] == "Processed: Hello World"
    assert data["length"] == 11
    
    # 验证状态变化
    assert cell.state == CellState.COMPLETED
    assert cell.execution_count == 1


def test_cell_error_handling():
    """测试Cell错误处理"""
    
    class ErrorCell(Cell):
        def process(self, context):
            raise ValueError("Test error")
    
    cell = ErrorCell()
    result = cell({"input": "test"})
    
    # 验证错误处理
    assert result["success"] is False
    assert result["error"] is not None
    assert cell.state == CellState.ERROR


def test_cell_input_validation():
    """测试Cell输入验证"""
    cell = TestCell()
    
    # 测试非字典输入
    result = cell("not a dict")
    assert result["success"] is False
    assert "Input context must be a dict" in result["error"]


def test_cell_status_and_reset():
    """测试Cell状态查询和重置"""
    cell = TestCell()
    
    # 执行几次
    cell({"input": "test1"})
    cell({"input": "test2"})
    
    # 检查状态
    status = cell.get_status()
    assert status["execution_count"] == 2
    assert status["cell_name"] == "TestCell"
    
    # 重置
    cell.reset()
    assert cell.state == CellState.IDLE
    assert cell.execution_count == 0


def test_cell_clone():
    """测试Cell克隆"""
    original = TestCell({"custom_param": "value"})
    clone = original.clone()
    
    # 验证克隆
    assert clone.cell_id != original.cell_id
    assert clone.config == original.config
    assert clone.__class__ == original.__class__


def test_llm_cell_initialization():
    """测试LLMCell初始化（不进行实际API调用）"""
    # 设置测试配置
    setup_futurx_api("test_key", "https://test.example.com")
    
    # 测试LLMCell创建
    llm = LLMCell("gpt-3.5-turbo")
    
    assert llm.model_name == "gpt-3.5-turbo"
    assert llm.api_key == "test_key"
    assert llm.base_url == "https://test.example.com"
    
    # 测试状态
    status = llm.get_status()
    assert status["model_name"] == "gpt-3.5-turbo"
    assert status["api_configured"] is True


def test_llm_cell_without_api_key():
    """测试没有API密钥时的LLMCell创建"""
    # 清除配置
    config = GlobalConfig()
    config._config["api_keys"] = {}
    
    # 应该抛出配置错误
    with pytest.raises(CellConfigurationError):
        LLMCell()


if __name__ == "__main__":
    # 运行测试
    print("🧬 运行FuturEmbryo基础测试...")
    
    # 手动运行测试函数
    test_functions = [
        test_cell_state_enum,
        test_global_config,
        test_cell_basic_functionality,
        test_cell_error_handling,
        test_cell_input_validation,
        test_cell_status_and_reset,
        test_cell_clone,
        test_llm_cell_initialization,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            print(f"运行 {test_func.__name__}...", end=" ")
            test_func()
            print("✅ 通过")
            passed += 1
        except Exception as e:
            print(f"❌ 失败: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print(f"\n测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败")
        sys.exit(1) 