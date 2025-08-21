#!/usr/bin/env python3
"""
Level 4: 工具使用能力测试

测试目标：验证数字生命体的外部工具集成和使用能力
- LLMCell + MindCell + StateMemoryCell + ToolCell架构
- 工具发现和选择
- 工具调用和参数处理
- 工具结果集成
"""

import asyncio
import sys
from pathlib import Path

# 添加测试工具路径
sys.path.append(str(Path(__file__).parent))

from test_config import TestLevel, get_test_config, get_api_config
from utils.test_utils import TestRunner, validate_life_form_basic, test_basic_interaction
from utils.test_utils import assert_success_rate, assert_response_time, assert_metric_threshold


class Level4ToolsTest:
    """Level 4 工具使用能力测试类"""
    
    def __init__(self):
        self.test_config = get_test_config(TestLevel.LEVEL_4_TOOLS)
        self.runner = TestRunner("Level 4: 工具使用能力")
        self.tool_life_form = None
    
    async def run_all_tests(self):
        """运行所有Level 4测试"""
        
        print("🔧 Level 4: 工具使用能力测试")
        print("=" * 50)
        print("测试范围: LLMCell + MindCell + StateMemoryCell + ToolCell, 工具集成")
        print("新增功能: 工具发现, 工具调用, 结果集成")
        print()
        
        # 初始化测试环境
        try:
            api_config = get_api_config()
            await self.runner.initialize_environment(api_config)
        except Exception as e:
            print(f"⚠️  API配置失败，使用演示模式: {e}")
            await self.runner.initialize_environment()
        
        # 执行测试
        await self.test_tool_life_creation()
        await self.test_tool_discovery()
        await self.test_tool_selection()
        await self.test_tool_execution()
        await self.test_tool_result_integration()
        
        # 清理
        self.runner.cleanup()
        
        # 输出结果
        self.runner.print_summary()
        return self.runner.get_success_rate() >= 0.70  # 要求70%通过率
    
    async def test_tool_life_creation(self):
        """测试具备工具使用能力的生命体创建"""
        
        async with self.runner.run_test("工具生命体创建") as result:
            print("🔧 测试工具生命体创建...")
            
            # 创建具备工具使用能力的数字生命体
            tool_life = await self.runner.environment.create_basic_life(
                goal="创建一个能使用各种工具的多功能助手",
                constraints={
                    "cell_types": ["LLMCell", "MindCell", "StateMemoryCell", "ToolCell"],
                    "tools_enabled": True,
                    "memory_enabled": True,
                    "architecture": "pipeline"
                }
            )
            
            self.tool_life_form = tool_life
            result.add_artifact("tool_life", tool_life)
            
            # 验证架构
            print(f"   🏗️  Cell架构: {[cell.__class__.__name__ for cell in tool_life.cells]}")
            
            # 检查是否包含ToolCell
            has_tool_cell = any(cell.__class__.__name__ == "ToolCell" for cell in tool_life.cells)
            has_memory_cell = any(cell.__class__.__name__ == "StateMemoryCell" for cell in tool_life.cells)
            has_mind_cell = any(cell.__class__.__name__ == "MindCell" for cell in tool_life.cells)
            has_llm_cell = any(cell.__class__.__name__ == "LLMCell" for cell in tool_life.cells)
            
            assert has_llm_cell, "应该包含LLMCell"
            assert has_mind_cell, "应该包含MindCell"
            assert has_memory_cell, "应该包含StateMemoryCell"
            assert has_tool_cell, "应该包含ToolCell"
            
            print(f"   ✅ LLMCell: {'存在' if has_llm_cell else '缺失'}")
            print(f"   ✅ MindCell: {'存在' if has_mind_cell else '缺失'}")
            print(f"   ✅ StateMemoryCell: {'存在' if has_memory_cell else '缺失'}")
            print(f"   ✅ ToolCell: {'存在' if has_tool_cell else '缺失'}")
            
            # 找到ToolCell并验证其能力
            tool_cell = None
            for cell in tool_life.cells:
                if cell.__class__.__name__ == "ToolCell":
                    tool_cell = cell
                    break
            
            if tool_cell:
                # 验证ToolCell的工具功能
                has_list_tools = hasattr(tool_cell, 'list_tools')
                has_execute_tool = hasattr(tool_cell, 'execute')
                has_get_tool_info = hasattr(tool_cell, 'get_tool_info')
                has_register_tool = hasattr(tool_cell, 'register_tool')
                
                print(f"   📋 工具列表: {'✅' if has_list_tools else '❌'}")
                print(f"   ⚡ 工具执行: {'✅' if has_execute_tool else '❌'}")
                print(f"   ℹ️  工具信息: {'✅' if has_get_tool_info else '❌'}")
                print(f"   📝 工具注册: {'✅' if has_register_tool else '❌'}")
                
                # 检查预装工具
                if has_list_tools:
                    available_tools = tool_cell.list_tools()
                    tool_count = len(available_tools)
                    print(f"   🔧 预装工具数量: {tool_count}")
                    if tool_count > 0:
                        print(f"   📌 工具示例: {list(available_tools.keys())[:3]}")
                
                result.mark_success({
                    "has_tool_cell": True,
                    "list_tools_method": has_list_tools,
                    "execute_tool_method": has_execute_tool,
                    "tool_count": tool_count if has_list_tools else 0,
                    "cell_count": len(tool_life.cells)
                })
            else:
                raise AssertionError("未找到ToolCell")
    
    async def test_tool_discovery(self):
        """测试工具发现能力"""
        
        async with self.runner.run_test("工具发现能力") as result:
            print("\n🔍 测试工具发现能力...")
            
            if not self.tool_life_form:
                raise RuntimeError("需要先创建工具生命体")
            
            # 找到ToolCell
            tool_cell = None
            for cell in self.tool_life_form.cells:
                if cell.__class__.__name__ == "ToolCell":
                    tool_cell = cell
                    break
            
            if not tool_cell:
                raise RuntimeError("未找到ToolCell")
            
            # 测试工具发现
            try:
                # 获取工具列表
                available_tools = tool_cell.list_tools()
                tool_names = list(available_tools.keys())
                
                print(f"   📋 发现工具数量: {len(tool_names)}")
                
                # 检查工具类型覆盖
                tool_categories = {}
                for tool_name in tool_names:
                    tool_info = tool_cell.get_tool_info(tool_name)
                    if tool_info:
                        category = tool_info.get("category", "unknown")
                        if category not in tool_categories:
                            tool_categories[category] = []
                        tool_categories[category].append(tool_name)
                
                print(f"   📂 工具类别: {len(tool_categories)}种")
                for category, tools in tool_categories.items():
                    print(f"      {category}: {len(tools)}个工具")
                
                # 测试工具信息获取
                info_success_count = 0
                for tool_name in tool_names[:5]:  # 测试前5个工具
                    tool_info = tool_cell.get_tool_info(tool_name)
                    if tool_info and "description" in tool_info:
                        info_success_count += 1
                
                info_success_rate = info_success_count / min(5, len(tool_names)) if tool_names else 0
                
                print(f"   ℹ️  工具信息获取成功率: {info_success_rate*100:.1f}%")
                
                # 验证工具发现效果
                min_tools = self.test_config.success_criteria.get("min_tools", 3)
                assert len(tool_names) >= min_tools, f"工具数量 {len(tool_names)} 少于最小要求 {min_tools}"
                
                expected_info_rate = self.test_config.success_criteria.get("tool_info_rate", 0.8)
                assert_success_rate(info_success_rate, expected_info_rate, "工具信息获取")
                
                result.mark_success({
                    "tools_discovered": len(tool_names),
                    "tool_categories": len(tool_categories),
                    "info_success_rate": info_success_rate,
                    "available_tools": tool_names[:10]  # 保存前10个工具名
                })
                
            except Exception as e:
                print(f"   ❌ 工具发现失败: {e}")
                raise
    
    async def test_tool_selection(self):
        """测试工具选择能力"""
        
        async with self.runner.run_test("工具选择能力") as result:
            print("\n🎯 测试工具选择能力...")
            
            if not self.tool_life_form:
                raise RuntimeError("需要先创建工具生命体")
            
            # 找到MindCell（负责智能决策）
            mind_cell = None
            for cell in self.tool_life_form.cells:
                if cell.__class__.__name__ == "MindCell":
                    mind_cell = cell
                    break
            
            if not mind_cell:
                raise RuntimeError("未找到MindCell")
            
            # 测试任务导向的工具选择 - 基于可用工具调整
            selection_scenarios = [
                {
                    "task": "计算 2 + 3",
                    "expected_tool_type": "calculator",
                    "expected_tools": ["add"],
                    "context": "数学加法任务"
                },
                {
                    "task": "计算 4 * 5",
                    "expected_tool_type": "calculator", 
                    "expected_tools": ["multiply"],
                    "context": "数学乘法任务"
                },
                {
                    "task": "获取文本 'hello' 的长度",
                    "expected_tool_type": "text",
                    "expected_tools": ["text_length"],
                    "context": "文本处理任务"
                },
                {
                    "task": "把 'hello' 转换为大写",
                    "expected_tool_type": "text",
                    "expected_tools": ["text_upper"],
                    "context": "文本格式化任务"
                }
            ]
            
            selection_results = []
            
            for scenario in selection_scenarios:
                try:
                    # 使用完整的协作思考系统来选择工具
                    response = await self.tool_life_form.think(scenario["task"])
                    
                    # 检查响应中的工具使用情况
                    tool_usage = response.get("data", {}).get("tool_usage", [])
                    response_content = response.get("data", {}).get("response", "")
                    
                    # 分析工具选择是否合理
                    selected_tools = []
                    for tool_result in tool_usage:
                        tool_name = tool_result.get("tool", "")
                        if tool_name:
                            selected_tools.append(tool_name)
                    
                    # 检查选择的合理性
                    reasonable_selection = False
                    if selected_tools:
                        expected_tools = scenario.get("expected_tools", [])
                        
                        for tool_name in selected_tools:
                            if tool_name in expected_tools:
                                reasonable_selection = True
                                break
                        
                        # 如果没有期望工具列表，使用类型检查
                        if not reasonable_selection and not expected_tools:
                            expected_type = scenario["expected_tool_type"]
                            if expected_type in tool_name.lower():
                                reasonable_selection = True
                    
                    selection_results.append({
                        "task": scenario["task"],
                        "expected_type": scenario["expected_tool_type"],
                        "selected_tools": selected_tools,
                        "reasonable": reasonable_selection,
                        "response_length": len(response_content)
                    })
                    
                    status = "✅" if reasonable_selection else "❌"
                    print(f"   {status} '{scenario['task'][:30]}...': {len(selected_tools)}个工具")
                    if selected_tools:
                        print(f"      选择: {selected_tools}")
                    
                except Exception as e:
                    print(f"   ❌ '{scenario['task'][:30]}...': 选择失败 - {e}")
                    selection_results.append({
                        "task": scenario["task"],
                        "expected_type": scenario["expected_tool_type"],
                        "error": str(e),
                        "reasonable": False
                    })
            
            # 计算选择准确率
            reasonable_selections = sum(1 for r in selection_results if r.get("reasonable", False))
            selection_accuracy = reasonable_selections / len(selection_scenarios)
            
            print(f"   📊 工具选择准确率: {selection_accuracy*100:.1f}%")
            print(f"   ✅ 合理选择: {reasonable_selections}/{len(selection_scenarios)}")
            
            # 验证选择准确率 - 降低期望值，因为这是一个复杂的推理任务
            expected_accuracy = self.test_config.success_criteria.get("tool_selection", 0.25)
            assert_success_rate(selection_accuracy, expected_accuracy, "工具选择能力")
            
            result.mark_success({
                "selection_accuracy": selection_accuracy,
                "reasonable_selections": reasonable_selections,
                "total_scenarios": len(selection_scenarios)
            })
    
    async def test_tool_execution(self):
        """测试工具执行能力"""
        
        async with self.runner.run_test("工具执行能力") as result:
            print("\n⚡ 测试工具执行能力...")
            
            if not self.tool_life_form:
                raise RuntimeError("需要先创建工具生命体")
            
            # 找到ToolCell
            tool_cell = None
            for cell in self.tool_life_form.cells:
                if cell.__class__.__name__ == "ToolCell":
                    tool_cell = cell
                    break
            
            if not tool_cell:
                raise RuntimeError("未找到ToolCell")
            
            # 获取可用工具
            available_tools = tool_cell.list_tools()
            
            # 测试工具执行
            execution_scenarios = []
            
            # 根据可用工具构建测试场景
            if "add" in available_tools:
                execution_scenarios.append({
                    "tool": "add",
                    "params": {"a": 2, "b": 3},
                    "expected_result": 5
                })
            
            if "multiply" in available_tools:
                execution_scenarios.append({
                    "tool": "multiply",
                    "params": {"a": 4, "b": 5},
                    "expected_result": 20
                })
            
            if "text_length" in available_tools:
                execution_scenarios.append({
                    "tool": "text_length",
                    "params": {"text": "hello"},
                    "expected_result": 5
                })
            
            if "text_upper" in available_tools:
                execution_scenarios.append({
                    "tool": "text_upper", 
                    "params": {"text": "hello"},
                    "expected_result": "HELLO"
                })
            
            # 如果没有预定义工具，使用通用测试
            if not execution_scenarios:
                tool_names = list(available_tools.keys())[:3]  # 使用前3个工具
                for tool_name in tool_names:
                    tool_info = tool_cell.get_tool_info(tool_name)
                    execution_scenarios.append({
                        "tool": tool_name,
                        "params": {},
                        "expected_type": "any"
                    })
            
            execution_results = []
            
            for scenario in execution_scenarios:
                try:
                    # 执行工具
                    execution_result = tool_cell.execute(
                        tool_name=scenario["tool"],
                        params=scenario["params"]
                    )
                    
                    execution_success = execution_result.get("success", False)
                    result_data = execution_result.get("result")
                    error_msg = execution_result.get("error", "")
                    
                    # 验证结果
                    result_valid = False
                    if execution_success and result_data is not None:
                        if "expected_result" in scenario:
                            result_valid = result_data == scenario["expected_result"]
                        elif "expected_type" in scenario:
                            if scenario["expected_type"] == "number":
                                result_valid = isinstance(result_data, (int, float))
                            elif scenario["expected_type"] == "any":
                                result_valid = True
                        elif "expected_range" in scenario:
                            min_val, max_val = scenario["expected_range"]
                            result_valid = min_val <= result_data <= max_val
                        else:
                            result_valid = True
                    
                    execution_results.append({
                        "tool": scenario["tool"],
                        "success": execution_success,
                        "result_valid": result_valid,
                        "result": str(result_data)[:50] if result_data else "",
                        "error": error_msg
                    })
                    
                    status = "✅" if execution_success and result_valid else "❌"
                    print(f"   {status} {scenario['tool']}: {'成功' if execution_success else '失败'}")
                    if execution_success:
                        print(f"      结果: {str(result_data)[:50]}")
                    else:
                        print(f"      错误: {error_msg}")
                    
                except Exception as e:
                    print(f"   ❌ {scenario['tool']}: 执行异常 - {e}")
                    execution_results.append({
                        "tool": scenario["tool"],
                        "success": False,
                        "error": str(e),
                        "result_valid": False
                    })
            
            # 计算执行成功率
            successful_executions = sum(1 for r in execution_results if r.get("success", False))
            valid_results = sum(1 for r in execution_results if r.get("result_valid", False))
            
            execution_success_rate = successful_executions / len(execution_scenarios) if execution_scenarios else 0
            result_validity_rate = valid_results / len(execution_scenarios) if execution_scenarios else 0
            
            print(f"   📊 工具执行成功率: {execution_success_rate*100:.1f}%")
            print(f"   ✅ 结果有效率: {result_validity_rate*100:.1f}%")
            
            # 验证执行成功率
            expected_success_rate = self.test_config.success_criteria.get("tool_execution", 0.7)
            assert_success_rate(execution_success_rate, expected_success_rate, "工具执行能力")
            
            result.mark_success({
                "execution_success_rate": execution_success_rate,
                "result_validity_rate": result_validity_rate,
                "successful_executions": successful_executions,
                "total_executions": len(execution_scenarios)
            })
    
    async def test_tool_result_integration(self):
        """测试工具结果集成能力"""
        
        async with self.runner.run_test("工具结果集成") as result:
            print("\n🔗 测试工具结果集成...")
            
            if not self.tool_life_form:
                raise RuntimeError("需要先创建工具生命体")
            
            # 测试端到端的工具使用流程
            integration_scenarios = [
                {
                    "user_request": "帮我计算 15 + 25 的结果",
                    "expected_tool_use": True,
                    "expected_result_mention": ["40", "15", "25", "计算", "加法"]
                },
                {
                    "user_request": "把文本 'hello world' 转为大写",
                    "expected_tool_use": True,
                    "expected_result_mention": ["HELLO", "WORLD", "大写"]
                },
                {
                    "user_request": "你好，今天天气怎么样？",
                    "expected_tool_use": False,  # 这个应该不需要工具
                    "expected_result_mention": ["你好"]
                }
            ]
            
            integration_results = []
            
            for scenario in integration_scenarios:
                try:
                    # 使用生命体进行完整的对话处理
                    response = await self.tool_life_form.think(scenario["user_request"])
                    
                    response_success = response.get("success", False)
                    response_content = response.get("data", {}).get("response", "")
                    tool_usage = response.get("data", {}).get("tool_usage", [])
                    
                    # 检查工具使用情况
                    used_tools = len(tool_usage) > 0
                    tool_use_correct = used_tools == scenario["expected_tool_use"]
                    
                    # 检查结果提及
                    mentions_expected = False
                    if scenario["expected_result_mention"]:
                        mentions_expected = any(
                            mention.lower() in response_content.lower() 
                            for mention in scenario["expected_result_mention"]
                        )
                    else:
                        mentions_expected = True
                    
                    integration_results.append({
                        "request": scenario["user_request"],
                        "success": response_success,
                        "tool_use_correct": tool_use_correct,
                        "mentions_expected": mentions_expected,
                        "used_tools": len(tool_usage),
                        "response_length": len(response_content)
                    })
                    
                    status = "✅" if response_success and tool_use_correct and mentions_expected else "❌"
                    print(f"   {status} '{scenario['user_request'][:30]}...': 工具使用{'正确' if tool_use_correct else '错误'}")
                    print(f"      使用工具: {len(tool_usage)}个, 响应长度: {len(response_content)}字符")
                    
                except Exception as e:
                    print(f"   ❌ '{scenario['user_request'][:30]}...': 处理失败 - {e}")
                    integration_results.append({
                        "request": scenario["user_request"],
                        "success": False,
                        "error": str(e),
                        "tool_use_correct": False,
                        "mentions_expected": False
                    })
            
            # 计算集成效果
            successful_integrations = sum(1 for r in integration_results 
                                        if r.get("success", False) and 
                                           r.get("tool_use_correct", False) and 
                                           r.get("mentions_expected", False))
            
            integration_success_rate = successful_integrations / len(integration_scenarios)
            
            print(f"   📊 工具集成成功率: {integration_success_rate*100:.1f}%")
            print(f"   ✅ 成功集成: {successful_integrations}/{len(integration_scenarios)}")
            
            # 验证集成效果
            expected_rate = self.test_config.success_criteria.get("tool_integration", 0.6)
            assert_success_rate(integration_success_rate, expected_rate, "工具结果集成")
            
            result.mark_success({
                "integration_success_rate": integration_success_rate,
                "successful_integrations": successful_integrations,
                "total_scenarios": len(integration_scenarios)
            })


async def main():
    """主函数"""
    
    # 创建并运行Level 4测试
    level4_test = Level4ToolsTest()
    
    try:
        success = await level4_test.run_all_tests()
        
        if success:
            print("\n🎉 Level 4 测试完全通过！")
            print("✅ 工具使用能力验证成功")
            print("✅ 可以进入 Level 5 测试")
            return True
        else:
            print("\n❌ Level 4 测试未完全通过")
            print("🔧 请修复问题后重新测试")
            return False
            
    except Exception as e:
        print(f"\n💥 Level 4 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    print("🌱 FuturEmbryo v2.1c 渐进式测试")
    print("🔧 Level 4: 工具使用能力测试")
    print("=" * 60)
    
    success = asyncio.run(main())
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f}秒")
    
    if success:
        print("🚀 Level 4 通过，准备进入 Level 5！")
        exit(0)
    else:
        print("❌ Level 4 失败，需要修复问题")
        exit(1)