#!/usr/bin/env python3
"""
Level 2: 思维思考能力测试

测试目标：验证数字生命体的深度思考能力
- LLMCell + MindCell架构
- 思考过程质量
- 注意力指导能力
- 反馈判断机制
"""

import asyncio
import sys
from pathlib import Path

# 添加测试工具路径
sys.path.append(str(Path(__file__).parent))

from test_config import TestLevel, get_test_config, get_api_config
from utils.test_utils import TestRunner, validate_life_form_basic, test_basic_interaction
from utils.test_utils import assert_success_rate, assert_response_time, assert_metric_threshold


class Level2ThinkingTest:
    """Level 2 思维思考能力测试类"""
    
    def __init__(self):
        self.test_config = get_test_config(TestLevel.LEVEL_2_THINKING)
        self.runner = TestRunner("Level 2: 思维思考能力")
        self.thinking_life_form = None
    
    async def run_all_tests(self):
        """运行所有Level 2测试"""
        
        print("🧠 Level 2: 思维思考能力测试")
        print("=" * 50)
        print("测试范围: LLMCell + MindCell, 深度思考, 注意力控制, 反馈判断")
        print("新增功能: 思维推理, 注意力指导, 反馈过滤")
        print()
        
        # 初始化测试环境
        try:
            api_config = get_api_config()
            await self.runner.initialize_environment(api_config)
        except Exception as e:
            print(f"⚠️  API配置失败，使用演示模式: {e}")
            await self.runner.initialize_environment()
        
        # 执行测试
        await self.test_thinking_life_creation()
        await self.test_thinking_process_quality()
        await self.test_attention_control()
        await self.test_feedback_judgment()
        
        # 清理
        self.runner.cleanup()
        
        # 输出结果
        self.runner.print_summary()
        return self.runner.get_success_rate() >= 0.80  # 要求80%通过率
    
    async def test_thinking_life_creation(self):
        """测试具备思维能力的生命体创建"""
        
        async with self.runner.run_test("思维生命体创建") as result:
            print("🧠 测试思维生命体创建...")
            
            # 创建具备思考能力的数字生命体
            thinking_life = await self.runner.environment.create_basic_life(
                goal="创建一个会深度思考的分析助手",
                constraints={
                    "cell_types": ["LLMCell", "MindCell"],
                    "thinking_enabled": True,
                    "attention_control": True,
                    "architecture": "pipeline"
                }
            )
            
            self.thinking_life_form = thinking_life
            result.add_artifact("thinking_life", thinking_life)
            
            # 验证架构
            print(f"   🏗️  Cell架构: {[cell.__class__.__name__ for cell in thinking_life.cells]}")
            
            # 检查是否包含MindCell
            has_mind_cell = any(cell.__class__.__name__ == "MindCell" for cell in thinking_life.cells)
            has_llm_cell = any(cell.__class__.__name__ == "LLMCell" for cell in thinking_life.cells)
            
            assert has_llm_cell, "应该包含LLMCell"
            assert has_mind_cell, "应该包含MindCell"
            
            print(f"   ✅ LLMCell: {'存在' if has_llm_cell else '缺失'}")
            print(f"   ✅ MindCell: {'存在' if has_mind_cell else '缺失'}")
            
            # 找到MindCell并验证其能力
            mind_cell = None
            for cell in thinking_life.cells:
                if cell.__class__.__name__ == "MindCell":
                    mind_cell = cell
                    break
            
            if mind_cell:
                # 验证MindCell的思维功能
                has_direct_attention = hasattr(mind_cell, 'direct_attention')
                has_judge_feedback = hasattr(mind_cell, 'judge_feedback')
                has_feedback_filter = hasattr(mind_cell, 'feedback_filter')
                
                print(f"   🎯 注意力指导: {'✅' if has_direct_attention else '❌'}")
                print(f"   🧠 反馈判断: {'✅' if has_judge_feedback else '❌'}")
                print(f"   🔍 反馈过滤器: {'✅' if has_feedback_filter else '❌'}")
                
                result.mark_success({
                    "has_mind_cell": True,
                    "attention_control": has_direct_attention,
                    "feedback_judgment": has_judge_feedback,
                    "cell_count": len(thinking_life.cells)
                })
            else:
                raise AssertionError("未找到MindCell")
    
    async def test_thinking_process_quality(self):
        """测试思考过程质量"""
        
        async with self.runner.run_test("思考过程质量") as result:
            print("\n🤔 测试思考过程质量...")
            
            if not self.thinking_life_form:
                raise RuntimeError("需要先创建思维生命体")
            
            # 找到MindCell
            mind_cell = None
            for cell in self.thinking_life_form.cells:
                if cell.__class__.__name__ == "MindCell":
                    mind_cell = cell
                    break
            
            if not mind_cell:
                raise RuntimeError("未找到MindCell")
            
            # 测试不同思维模式
            thinking_scenarios = [
                {
                    "input": "分析当前AI技术发展趋势",
                    "mode": "analysis",
                    "expected_depth": "高"
                },
                {
                    "input": "制定学习Python的计划",
                    "mode": "planning", 
                    "expected_depth": "中"
                },
                {
                    "input": "评估远程工作的利弊",
                    "mode": "reflection",
                    "expected_depth": "高"
                }
            ]
            
            thinking_results = []
            
            for scenario in thinking_scenarios:
                try:
                    # 使用MindCell进行思考
                    thinking_context = {
                        "user_input": scenario["input"],
                        "thinking_mode": scenario["mode"]
                    }
                    
                    thinking_result = mind_cell.process(thinking_context)
                    
                    if thinking_result.get("thinking_process"):
                        thinking_content = thinking_result["thinking_process"]
                        thinking_length = len(thinking_content)
                        
                        # 简单的质量评估
                        quality_indicators = {
                            "length_adequate": thinking_length > 100,
                            "has_structure": any(indicator in thinking_content for indicator in ["1.", "首先", "其次", "因此"]),
                            "has_reasoning": any(word in thinking_content for word in ["因为", "所以", "分析", "考虑"]),
                            "mode_applied": thinking_result.get("thinking_mode") == scenario["mode"]
                        }
                        
                        quality_score = sum(quality_indicators.values()) / len(quality_indicators)
                        
                        thinking_results.append({
                            "scenario": scenario["input"][:30] + "...",
                            "mode": scenario["mode"],
                            "length": thinking_length,
                            "quality_score": quality_score,
                            "confidence": thinking_result.get("confidence", 0.0)
                        })
                        
                        print(f"   💭 {scenario['mode']}: 长度{thinking_length}, 质量{quality_score:.2f}")
                        
                    else:
                        print(f"   ❌ {scenario['mode']}: 思考失败")
                        thinking_results.append({
                            "scenario": scenario["input"][:30] + "...",
                            "mode": scenario["mode"],
                            "length": 0,
                            "quality_score": 0.0,
                            "error": thinking_result.get("error", "未知错误")
                        })
                        
                except Exception as e:
                    print(f"   ❌ {scenario['mode']}: 异常 - {e}")
                    thinking_results.append({
                        "scenario": scenario["input"][:30] + "...",
                        "mode": scenario["mode"],
                        "length": 0,
                        "quality_score": 0.0,
                        "error": str(e)
                    })
            
            # 计算整体思考质量
            valid_results = [r for r in thinking_results if "error" not in r]
            if valid_results:
                avg_quality = sum(r["quality_score"] for r in valid_results) / len(valid_results)
                avg_length = sum(r["length"] for r in valid_results) / len(valid_results)
                
                print(f"   📊 平均质量分数: {avg_quality:.2f}")
                print(f"   📏 平均思考长度: {avg_length:.0f}字符")
                
                # 验证质量标准
                expected_quality = self.test_config.success_criteria["thinking_quality"]
                assert_metric_threshold(
                    {"thinking_quality": avg_quality},
                    {"thinking_quality": expected_quality},
                    "思考过程质量"
                )
                
                result.mark_success({
                    "avg_thinking_quality": avg_quality,
                    "avg_thinking_length": avg_length,
                    "successful_scenarios": len(valid_results),
                    "total_scenarios": len(thinking_scenarios)
                })
            else:
                raise AssertionError("所有思考场景都失败了")
    
    async def test_attention_control(self):
        """测试注意力控制能力"""
        
        async with self.runner.run_test("注意力控制") as result:
            print("\n🎯 测试注意力控制...")
            
            if not self.thinking_life_form:
                raise RuntimeError("需要先创建思维生命体")
            
            # 找到MindCell
            mind_cell = None
            for cell in self.thinking_life_form.cells:
                if cell.__class__.__name__ == "MindCell":
                    mind_cell = cell
                    break
            
            if not mind_cell or not hasattr(mind_cell, 'direct_attention'):
                raise RuntimeError("MindCell缺少注意力控制功能")
            
            # 测试注意力指导
            attention_scenarios = [
                {
                    "context": {"user_input": "分析市场数据"},
                    "expected_focus": ["analysis", "reasoning"]
                },
                {
                    "context": {"user_input": "制定学习计划"},
                    "expected_focus": ["planning", "strategy"]
                },
                {
                    "context": {"user_input": "解决技术问题"},
                    "expected_focus": ["problem_solving", "solutions"]
                }
            ]
            
            attention_results = []
            
            for scenario in attention_scenarios:
                try:
                    focus_areas = mind_cell.direct_attention(scenario["context"])
                    
                    # 检查焦点准确性
                    expected_focus = scenario["expected_focus"]
                    actual_focus = focus_areas if isinstance(focus_areas, list) else []
                    
                    # 计算焦点匹配度
                    matches = sum(1 for expected in expected_focus if any(expected in actual for actual in actual_focus))
                    accuracy = matches / len(expected_focus) if expected_focus else 0
                    
                    attention_results.append({
                        "input": scenario["context"]["user_input"],
                        "expected": expected_focus,
                        "actual": actual_focus,
                        "accuracy": accuracy
                    })
                    
                    print(f"   🎯 '{scenario['context']['user_input'][:20]}...': 准确率{accuracy*100:.1f}%")
                    print(f"      期望: {expected_focus}")
                    print(f"      实际: {actual_focus}")
                    
                except Exception as e:
                    print(f"   ❌ 注意力测试失败: {e}")
                    attention_results.append({
                        "input": scenario["context"]["user_input"],
                        "error": str(e),
                        "accuracy": 0.0
                    })
            
            # 计算整体准确率
            valid_results = [r for r in attention_results if "error" not in r]
            if valid_results:
                avg_accuracy = sum(r["accuracy"] for r in valid_results) / len(valid_results)
                
                print(f"   📊 注意力指导平均准确率: {avg_accuracy*100:.1f}%")
                
                # 验证准确率标准
                expected_accuracy = self.test_config.success_criteria["attention_accuracy"]
                assert_metric_threshold(
                    {"attention_accuracy": avg_accuracy},
                    {"attention_accuracy": expected_accuracy},
                    "注意力控制准确率"
                )
                
                result.mark_success({
                    "attention_accuracy": avg_accuracy,
                    "successful_tests": len(valid_results),
                    "total_tests": len(attention_scenarios)
                })
            else:
                raise AssertionError("所有注意力控制测试都失败了")
    
    async def test_feedback_judgment(self):
        """测试反馈判断能力"""
        
        async with self.runner.run_test("反馈判断能力") as result:
            print("\n🧠 测试反馈判断能力...")
            
            if not self.thinking_life_form:
                raise RuntimeError("需要先创建思维生命体")
            
            # 找到MindCell
            mind_cell = None
            for cell in self.thinking_life_form.cells:
                if cell.__class__.__name__ == "MindCell":
                    mind_cell = cell
                    break
            
            if not mind_cell or not hasattr(mind_cell, 'judge_feedback'):
                raise RuntimeError("MindCell缺少反馈判断功能")
            
            # 测试反馈判断
            feedback_scenarios = [
                {
                    "feedback": "你的分析很专业，逻辑清晰",
                    "expected": "absorb",
                    "type": "positive_professional"
                },
                {
                    "feedback": "请提供更准确的信息",
                    "expected": "absorb", 
                    "type": "constructive"
                },
                {
                    "feedback": "今天天气不错",
                    "expected": "ignore",
                    "type": "irrelevant"
                },
                {
                    "feedback": "请不要提供医疗建议",
                    "expected": "absorb",
                    "type": "safety_constraint"
                },
                {
                    "feedback": "你太笨了，什么都不会",
                    "expected": "ignore",
                    "type": "negative_unhelpful"
                }
            ]
            
            judgment_results = []
            
            for scenario in feedback_scenarios:
                try:
                    judgment = mind_cell.judge_feedback(scenario["feedback"])
                    
                    # 检查判断准确性
                    is_correct = judgment == scenario["expected"]
                    
                    judgment_results.append({
                        "feedback": scenario["feedback"][:40] + "...",
                        "type": scenario["type"],
                        "expected": scenario["expected"],
                        "actual": judgment,
                        "correct": is_correct
                    })
                    
                    status = "✅" if is_correct else "❌"
                    print(f"   {status} {scenario['type']}: 期望{scenario['expected']}, 实际{judgment}")
                    
                except Exception as e:
                    print(f"   ❌ 反馈判断失败: {e}")
                    judgment_results.append({
                        "feedback": scenario["feedback"][:40] + "...",
                        "type": scenario["type"],
                        "error": str(e),
                        "correct": False
                    })
            
            # 计算判断准确率
            correct_judgments = sum(1 for r in judgment_results if r.get("correct", False))
            accuracy = correct_judgments / len(judgment_results)
            
            print(f"   📊 反馈判断准确率: {accuracy*100:.1f}%")
            print(f"   ✅ 正确判断: {correct_judgments}/{len(judgment_results)}")
            
            # 验证判断准确率
            expected_accuracy = self.test_config.success_criteria["feedback_judgment"]
            assert_metric_threshold(
                {"feedback_judgment": accuracy},
                {"feedback_judgment": expected_accuracy},
                "反馈判断准确率"
            )
            
            result.mark_success({
                "judgment_accuracy": accuracy,
                "correct_judgments": correct_judgments,
                "total_judgments": len(judgment_results)
            })


async def main():
    """主函数"""
    
    # 创建并运行Level 2测试
    level2_test = Level2ThinkingTest()
    
    try:
        success = await level2_test.run_all_tests()
        
        if success:
            print("\n🎉 Level 2 测试完全通过！")
            print("✅ 思维思考能力验证成功")
            print("✅ 可以进入 Level 3 测试")
            return True
        else:
            print("\n❌ Level 2 测试未完全通过")
            print("🔧 请修复问题后重新测试")
            return False
            
    except Exception as e:
        print(f"\n💥 Level 2 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    print("🌱 FuturEmbryo v2.1c 渐进式测试")
    print("🧠 Level 2: 思维思考能力测试")
    print("=" * 60)
    
    success = asyncio.run(main())
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f}秒")
    
    if success:
        print("🚀 Level 2 通过，准备进入 Level 3！")
        exit(0)
    else:
        print("❌ Level 2 失败，需要修复问题")
        exit(1)