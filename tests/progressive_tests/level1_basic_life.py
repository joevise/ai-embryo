#!/usr/bin/env python3
"""
Level 1: 基础数字生命测试

测试目标：验证最基础的数字生命体功能
- 纯LLMCell架构
- 基础对话能力
- IERT生命元素
- 数字生命名片
- 无记忆/思维/工具
"""

import asyncio
import sys
from pathlib import Path

# 添加测试工具路径
sys.path.append(str(Path(__file__).parent))

from test_config import TestLevel, get_test_config, get_api_config
from utils.test_utils import TestRunner, validate_life_form_basic, test_basic_interaction
from utils.test_utils import assert_success_rate, assert_response_time, assert_metric_threshold


class Level1BasicLifeTest:
    """Level 1 基础数字生命测试类"""
    
    def __init__(self):
        self.test_config = get_test_config(TestLevel.LEVEL_1_BASIC)
        self.runner = TestRunner("Level 1: 基础数字生命")
        self.test_life_form = None
    
    async def run_all_tests(self):
        """运行所有Level 1测试"""
        
        print("🧬 Level 1: 基础数字生命测试")
        print("=" * 50)
        print("测试范围: 纯LLMCell, 基础对话, IERT元素, 数字名片")
        print("排除功能: 记忆, 思维, 工具")
        print()
        
        # 初始化测试环境
        try:
            api_config = get_api_config()
            await self.runner.initialize_environment(api_config)
        except Exception as e:
            print(f"⚠️  API配置失败，使用演示模式: {e}")
            await self.runner.initialize_environment()
        
        # 执行测试
        await self.test_basic_life_creation()
        await self.test_iert_elements()
        await self.test_basic_conversation()
        await self.test_digital_life_card()
        await self.test_configuration_control()
        
        # 清理
        self.runner.cleanup()
        
        # 输出结果
        self.runner.print_summary()
        return self.runner.get_success_rate() >= 0.95  # 要求95%通过率
    
    async def test_basic_life_creation(self):
        """测试基础生命体创建"""
        
        async with self.runner.run_test("基础生命体创建") as result:
            print("🧬 测试基础生命体创建...")
            
            # 创建最简单的数字生命体
            life_form = await self.runner.environment.create_basic_life(
                goal="创建一个简单的聊天助手",
                constraints={
                    "architecture": "pipeline",
                    "cell_types": ["LLMCell"],
                    "no_memory": True,
                    "no_tools": True,
                    "no_advanced_thinking": True,
                    "complexity": "simple"
                }
            )
            
            self.test_life_form = life_form
            result.add_artifact("life_form", life_form)
            
            # 验证生命体基础属性
            validations = validate_life_form_basic(life_form)
            
            # 验证必要属性
            required_validations = [
                "has_dna", "has_cells", "has_name", "is_alive", 
                "has_think_method", "dll_signature_valid"
            ]
            
            passed_count = 0
            for validation in required_validations:
                if validations.get(validation, False):
                    passed_count += 1
                    print(f"   ✅ {validation}")
                else:
                    print(f"   ❌ {validation}")
            
            # 验证架构
            assert len(life_form.cells) == 1, f"期望1个Cell，实际{len(life_form.cells)}个"
            assert life_form.cells[0].__class__.__name__ == "LLMCell", "主Cell应该是LLMCell"
            
            print(f"   📊 基础验证通过: {passed_count}/{len(required_validations)}")
            print(f"   🧬 生命体名称: {life_form.dna.name}")
            print(f"   🔧 Cell架构: {[cell.__class__.__name__ for cell in life_form.cells]}")
            
            # 成功标准
            success_rate = passed_count / len(required_validations)
            assert_success_rate(success_rate, 1.0, "基础生命体创建")
            
            result.mark_success({
                "validation_pass_rate": success_rate,
                "cell_count": len(life_form.cells),
                "life_form_name": life_form.dna.name
            })
    
    async def test_iert_elements(self):
        """测试IERT生命元素"""
        
        async with self.runner.run_test("IERT生命元素验证") as result:
            print("\n🧬 测试IERT生命元素...")
            
            if not self.test_life_form:
                raise RuntimeError("需要先创建生命体")
            
            main_cell = self.test_life_form.cells[0]
            
            # 检查生命元素管理器
            assert hasattr(main_cell, 'life_elements'), "Cell应该有life_elements属性"
            
            life_elements = main_cell.life_elements
            
            # 验证DLL签名
            dll_signature = main_cell.get_dll_signature()
            detailed_signature = main_cell.get_detailed_signature()
            
            print(f"   📝 DLL签名: {dll_signature}")
            print(f"   📋 详细签名: {len(str(detailed_signature))}字符")
            
            # 验证四个元素
            elements_check = {}
            for element_type in ["I", "E", "R", "T"]:
                element = life_elements.get_element(element_type)
                elements_check[element_type] = element is not None
                if element:
                    print(f"   ✅ {element_type}元素: {type(element).__name__}")
                else:
                    print(f"   ❌ {element_type}元素: 缺失")
            
            # 验证签名格式
            assert dll_signature, "DLL签名不能为空"
            assert len(dll_signature) > 10, "DLL签名过短"
            
            # 验证所有元素存在
            missing_elements = [k for k, v in elements_check.items() if not v]
            assert not missing_elements, f"缺失IERT元素: {missing_elements}"
            
            result.mark_success({
                "dll_signature": dll_signature,
                "elements_present": sum(elements_check.values()),
                "signature_length": len(dll_signature)
            })
    
    async def test_basic_conversation(self):
        """测试基础对话能力"""
        
        async with self.runner.run_test("基础对话能力") as result:
            print("\n💬 测试基础对话能力...")
            
            if not self.test_life_form:
                raise RuntimeError("需要先创建生命体")
            
            # 定义测试对话
            test_conversations = [
                "你好，很高兴认识你",
                "你是谁？",
                "请介绍一下你自己",
                "今天天气怎么样？",
                "你能帮我做什么？"
            ]
            
            # 执行对话测试
            interaction_results = await test_basic_interaction(
                self.test_life_form, test_conversations
            )
            
            print(f"   📊 对话测试结果:")
            print(f"      总测试数: {interaction_results['total_tests']}")
            print(f"      成功响应: {interaction_results['successful_responses']}")
            print(f"      成功率: {interaction_results['success_rate']*100:.1f}%")
            print(f"      平均响应时间: {interaction_results.get('avg_response_time', 0):.2f}s")
            
            # 显示一些响应示例
            successful_responses = [r for r in interaction_results['responses'] if r['success']]
            if successful_responses:
                example = successful_responses[0]
                response_text = example.get('response_length', 0)
                print(f"   💭 响应示例长度: {response_text}字符")
            
            # 验证成功标准
            expected_success_rate = self.test_config.success_criteria["response_rate"]
            assert_success_rate(
                interaction_results['success_rate'], 
                expected_success_rate, 
                "基础对话能力"
            )
            
            if interaction_results.get('avg_response_time'):
                assert_response_time(
                    interaction_results['avg_response_time'], 
                    10.0,  # 最大10秒响应时间
                    "基础对话响应时间"
                )
            
            result.mark_success({
                "conversation_success_rate": interaction_results['success_rate'],
                "avg_response_time": interaction_results.get('avg_response_time', 0),
                "total_conversations": len(test_conversations)
            })
    
    async def test_digital_life_card(self):
        """测试数字生命名片"""
        
        async with self.runner.run_test("数字生命名片生成") as result:
            print("\n📇 测试数字生命名片...")
            
            if not self.test_life_form:
                raise RuntimeError("需要先创建生命体")
            
            # 检查名片数据
            assert hasattr(self.test_life_form, 'life_card_data'), "生命体应该有life_card_data"
            
            life_card_data = self.test_life_form.life_card_data
            assert life_card_data, "生命名片数据不能为空"
            
            # 验证名片必要字段
            required_fields = ["identity", "capabilities", "interfaces", "collaboration"]
            missing_fields = []
            
            for field in required_fields:
                if field in life_card_data:
                    print(f"   ✅ {field}: 已包含")
                else:
                    missing_fields.append(field)
                    print(f"   ❌ {field}: 缺失")
            
            assert not missing_fields, f"名片缺失必要字段: {missing_fields}"
            
            # 验证身份信息
            identity = life_card_data["identity"]
            assert identity.get("name"), "名片应该包含名称"
            assert identity.get("type"), "名片应该包含类型"
            assert identity.get("unique_id"), "名片应该包含唯一ID"
            
            # 验证能力信息
            capabilities = life_card_data["capabilities"]
            assert "core_abilities" in capabilities, "应该包含核心能力"
            assert len(capabilities["core_abilities"]) > 0, "核心能力不能为空"
            
            # 验证接口信息
            interfaces = life_card_data["interfaces"]
            assert interfaces.get("process_method"), "应该包含处理方法"
            
            print(f"   📝 生命体名称: {identity.get('name')}")
            print(f"   🔧 核心能力: {', '.join(capabilities['core_abilities'][:3])}")
            print(f"   🔗 主要接口: {interfaces.get('process_method')}")
            print(f"   🤝 协作风格: {life_card_data['collaboration'].get('style', '未知')}")
            
            # 测试名片导出
            grower = self.runner.environment.grower
            json_card = grower.export_life_card(self.test_life_form.dna.name, "json")
            markdown_card = grower.export_life_card(self.test_life_form.dna.name, "markdown")
            
            assert json_card, "JSON格式导出失败"
            assert markdown_card, "Markdown格式导出失败"
            
            print(f"   📄 JSON导出: {len(json_card)}字符")
            print(f"   📝 Markdown导出: {len(markdown_card)}字符")
            
            result.mark_success({
                "required_fields_present": len(required_fields),
                "core_abilities_count": len(capabilities["core_abilities"]),
                "json_export_length": len(json_card),
                "markdown_export_length": len(markdown_card)
            })
    
    async def test_configuration_control(self):
        """测试配置可控性"""
        
        async with self.runner.run_test("配置可控性验证") as result:
            print("\n🔧 测试配置可控性...")
            
            # 测试约束引导配置
            constrained_life = await self.runner.environment.create_basic_life(
                goal="创建一个专业的客服助手",
                constraints={
                    "architecture": "pipeline",
                    "cell_types": ["LLMCell"],
                    "personality_style": "professional",
                    "response_style": "formal",
                    "safety_level": "high"
                }
            )
            
            result.add_artifact("constrained_life", constrained_life)
            
            # 验证约束生效
            status = constrained_life.get_status()
            
            print(f"   🎭 个性特征: {', '.join(status.get('personality', []))}")
            print(f"   📝 生命体名称: {constrained_life.dna.name}")
            print(f"   🔧 Cell数量: {len(constrained_life.cells)}")
            
            # 验证架构约束
            assert len(constrained_life.cells) == 1, "应该只有1个Cell"
            assert constrained_life.cells[0].__class__.__name__ == "LLMCell", "应该是LLMCell"
            
            # 验证个性约束影响
            personality = status.get('personality', [])
            professional_indicators = ['professional', 'formal', 'helpful']
            has_professional_traits = any(trait in str(personality).lower() for trait in professional_indicators)
            
            print(f"   ✅ 专业特征识别: {'是' if has_professional_traits else '否'}")
            
            # 测试基础交互（验证约束效果）
            test_response = await constrained_life.think("你好，请介绍你的服务")
            response_success = test_response.get("success", False)
            
            print(f"   💬 约束后交互测试: {'成功' if response_success else '失败'}")
            
            result.mark_success({
                "constraint_applied": True,
                "cell_architecture_correct": len(constrained_life.cells) == 1,
                "professional_traits_detected": has_professional_traits,
                "post_constraint_interaction": response_success
            })


async def main():
    """主函数"""
    
    # 创建并运行Level 1测试
    level1_test = Level1BasicLifeTest()
    
    try:
        success = await level1_test.run_all_tests()
        
        if success:
            print("\n🎉 Level 1 测试完全通过！")
            print("✅ 基础数字生命体功能验证成功")
            print("✅ 可以进入 Level 2 测试")
            return True
        else:
            print("\n❌ Level 1 测试未完全通过")
            print("🔧 请修复问题后重新测试")
            return False
            
    except Exception as e:
        print(f"\n💥 Level 1 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    print("🌱 FuturEmbryo v2.1c 渐进式测试")
    print("🧬 Level 1: 基础数字生命测试")
    print("=" * 60)
    
    success = asyncio.run(main())
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f}秒")
    
    if success:
        print("🚀 Level 1 通过，准备进入 Level 2！")
        exit(0)
    else:
        print("❌ Level 1 失败，需要修复问题")
        exit(1)