#!/usr/bin/env python3
"""
FuturEmbryo v2.1c 渐进式测试运行器

统一管理和执行所有Level的测试，支持单独运行或批量运行
"""

import asyncio
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from test_config import TestLevel, TestConfigManager, get_test_config


class ProgressiveTestRunner:
    """渐进式测试运行器"""
    
    def __init__(self):
        self.config_manager = TestConfigManager()
        self.results: Dict[TestLevel, Dict[str, Any]] = {}
        self.start_time = time.time()
    
    async def run_single_level(self, level: TestLevel) -> bool:
        """运行单个Level测试"""
        
        if not self.config_manager.is_level_enabled(level):
            print(f"⚠️  {level.value} 已禁用，跳过")
            return True
        
        config = get_test_config(level)
        level_start_time = time.time()
        
        print(f"\n🎯 开始 {level.value.upper()} 测试")
        print("=" * 60)
        print(f"超时时间: {config.timeout}s")
        print(f"成功标准: {len(config.success_criteria)}项指标")
        print(f"测试场景: {len(config.test_scenarios)}个")
        
        try:
            # 动态导入对应的测试模块
            success = await self._execute_level_test(level)
            
            execution_time = time.time() - level_start_time
            
            # 记录结果
            config_dict = asdict(config)
            # 转换枚举为字符串以便JSON序列化
            if "level" in config_dict:
                config_dict["level"] = config_dict["level"].value if hasattr(config_dict["level"], 'value') else str(config_dict["level"])
            
            self.results[level] = {
                "success": success,
                "execution_time": execution_time,
                "config": config_dict,
                "timestamp": time.time()
            }
            
            if success:
                print(f"\n✅ {level.value.upper()} 测试通过！")
                print(f"⏱️  执行时间: {execution_time:.2f}s")
            else:
                print(f"\n❌ {level.value.upper()} 测试失败！")
                print(f"⏱️  执行时间: {execution_time:.2f}s")
            
            return success
            
        except Exception as e:
            execution_time = time.time() - level_start_time
            print(f"\n💥 {level.value.upper()} 测试执行异常: {e}")
            
            self.results[level] = {
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "timestamp": time.time()
            }
            
            return False
    
    async def _execute_level_test(self, level: TestLevel) -> bool:
        """执行具体的Level测试"""
        
        if level == TestLevel.LEVEL_1_BASIC:
            from level1_basic_life import Level1BasicLifeTest
            test_instance = Level1BasicLifeTest()
            return await test_instance.run_all_tests()
            
        elif level == TestLevel.LEVEL_2_THINKING:
            from level2_thinking import Level2ThinkingTest
            test_instance = Level2ThinkingTest()
            return await test_instance.run_all_tests()
            
        elif level == TestLevel.LEVEL_3_MEMORY:
            from level3_memory import Level3MemoryTest
            test_instance = Level3MemoryTest()
            return await test_instance.run_all_tests()
            
        elif level == TestLevel.LEVEL_4_TOOLS:
            from level4_tools import Level4ToolsTest
            test_instance = Level4ToolsTest()
            return await test_instance.run_all_tests()
            
        elif level == TestLevel.LEVEL_5_COLLABORATION:
            from level5_collaboration import Level5CollaborationTest
            test_instance = Level5CollaborationTest()
            return await test_instance.run_all_tests()
            
        elif level == TestLevel.LEVEL_6_LEARNING:
            from level6_learning import Level6LearningTest
            test_instance = Level6LearningTest()
            return await test_instance.run_all_tests()
            
        elif level == TestLevel.LEVEL_7_HYBRID:
            from level7_hybrid import Level7HybridTest
            test_instance = Level7HybridTest()
            return await test_instance.run_all_tests()
            
        else:
            raise ValueError(f"未知的测试Level: {level}")
    
    async def run_progressive_tests(self, start_level: Optional[TestLevel] = None,
                                  stop_on_failure: bool = True) -> bool:
        """运行渐进式测试"""
        
        print("🌱 FuturEmbryo v2.1c 渐进式测试套件")
        print("🧬 AI First 数字生命体协作框架")
        print("=" * 70)
        
        # 确定测试顺序
        all_levels = list(TestLevel)
        
        if start_level:
            start_index = all_levels.index(start_level)
            test_levels = all_levels[start_index:]
            print(f"📍 从 {start_level.value} 开始测试")
        else:
            test_levels = all_levels
            print("📍 执行完整渐进式测试")
        
        print(f"📋 测试Level数量: {len(test_levels)}")
        print()
        
        # 逐级执行测试
        all_passed = True
        
        for i, level in enumerate(test_levels, 1):
            print(f"\n🎯 进度: {i}/{len(test_levels)} - {level.value}")
            
            success = await self.run_single_level(level)
            
            if not success:
                all_passed = False
                if stop_on_failure:
                    print(f"\n🛑 {level.value} 失败，停止后续测试")
                    break
                else:
                    print(f"\n⚠️  {level.value} 失败，继续后续测试")
            else:
                print(f"✅ {level.value} 通过，继续下一Level")
        
        # 输出最终结果
        self._print_final_summary(all_passed)
        return all_passed
    
    async def run_specific_levels(self, levels: List[TestLevel]) -> bool:
        """运行指定的Level测试"""
        
        print("🎯 运行指定Level测试")
        print("=" * 40)
        print(f"测试Level: {[level.value for level in levels]}")
        print()
        
        all_passed = True
        
        for level in levels:
            success = await self.run_single_level(level)
            if not success:
                all_passed = False
        
        self._print_final_summary(all_passed)
        return all_passed
    
    def _print_final_summary(self, all_passed: bool):
        """打印最终测试摘要"""
        
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*70}")
        print("📊 渐进式测试总结")
        print("=" * 70)
        
        # 统计信息
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试Level: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "成功率: 0%")
        print(f"总耗时: {total_time:.2f}s")
        
        # 详细结果
        if self.results:
            print(f"\n📋 详细结果:")
            for level, result in self.results.items():
                status = "✅" if result["success"] else "❌"
                time_str = f"{result['execution_time']:.2f}s"
                print(f"   {status} {level.value}: {time_str}")
                
                if not result["success"] and "error" in result:
                    print(f"      错误: {result['error']}")
        
        # 最终状态
        print(f"\n🎉 测试状态: {'全部通过' if all_passed else '存在失败'}")
        
        if all_passed:
            print("🚀 FuturEmbryo v2.1c 框架验证完成！")
            print("🌟 数字生命体协作能力得到全面验证")
        else:
            print("🔧 请修复失败的测试项目")
            print("💡 建议先解决基础Level的问题")
    
    def save_results(self, filepath: str = "reports/test_results.json"):
        """保存测试结果"""
        
        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # 准备保存数据
        save_data = {
            "test_session": {
                "start_time": self.start_time,
                "total_time": time.time() - self.start_time,
                "framework_version": "FuturEmbryo v2.1c"
            },
            "results": {}
        }
        
        for level, result in self.results.items():
            save_data["results"][level.value] = result
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 测试结果已保存到: {filepath}")
    
    def set_demo_mode(self, enabled: bool = True):
        """设置演示模式"""
        self.config_manager.set_demo_mode(enabled)
        if enabled:
            print("🎭 演示模式已启用（降低成功标准）")
        else:
            print("🎯 标准模式已启用（使用正常标准）")


async def main():
    """主函数"""
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="FuturEmbryo v2.1c 渐进式测试运行器")
    parser.add_argument("--all", action="store_true", help="运行所有Level测试")
    parser.add_argument("--level", type=str, help="运行指定Level (如: 1,3,5)")
    parser.add_argument("--start-level", type=int, help="从指定Level开始 (1-7)")
    parser.add_argument("--continue-on-failure", action="store_true", help="失败后继续测试")
    parser.add_argument("--demo-mode", action="store_true", help="启用演示模式")
    parser.add_argument("--save-results", type=str, default="reports/test_results.json", 
                       help="保存结果文件路径")
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = ProgressiveTestRunner()
    
    # 设置演示模式
    if args.demo_mode:
        runner.set_demo_mode(True)
    
    try:
        success = False
        
        if args.all or (not args.level and not args.start_level):
            # 运行所有测试
            success = await runner.run_progressive_tests(
                stop_on_failure=not args.continue_on_failure
            )
            
        elif args.start_level:
            # 从指定Level开始
            if 1 <= args.start_level <= 7:
                level_map = {
                    1: TestLevel.LEVEL_1_BASIC,
                    2: TestLevel.LEVEL_2_THINKING,
                    3: TestLevel.LEVEL_3_MEMORY,
                    4: TestLevel.LEVEL_4_TOOLS,
                    5: TestLevel.LEVEL_5_COLLABORATION,
                    6: TestLevel.LEVEL_6_LEARNING,
                    7: TestLevel.LEVEL_7_HYBRID
                }
                start_level = level_map[args.start_level]
                success = await runner.run_progressive_tests(
                    start_level=start_level,
                    stop_on_failure=not args.continue_on_failure
                )
            else:
                print("❌ Level必须在1-7之间")
                return False
                
        elif args.level:
            # 运行指定Level
            try:
                level_numbers = [int(x.strip()) for x in args.level.split(",")]
                level_map = {
                    1: TestLevel.LEVEL_1_BASIC,
                    2: TestLevel.LEVEL_2_THINKING,
                    3: TestLevel.LEVEL_3_MEMORY,
                    4: TestLevel.LEVEL_4_TOOLS,
                    5: TestLevel.LEVEL_5_COLLABORATION,
                    6: TestLevel.LEVEL_6_LEARNING,
                    7: TestLevel.LEVEL_7_HYBRID
                }
                levels = [level_map[num] for num in level_numbers if 1 <= num <= 7]
                
                if levels:
                    success = await runner.run_specific_levels(levels)
                else:
                    print("❌ 无有效的Level编号")
                    return False
                    
            except ValueError:
                print("❌ Level格式错误，应为数字，如: 1,3,5")
                return False
        
        # 保存结果
        runner.save_results(args.save_results)
        
        return success
        
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        return False
        
    except Exception as e:
        print(f"\n💥 测试运行器异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    
    # 显示使用说明
    if len(sys.argv) == 1:
        print("🌱 FuturEmbryo v2.1c 渐进式测试运行器")
        print("=" * 50)
        print("使用方法:")
        print("  python test_runner.py --all                    # 运行所有测试")
        print("  python test_runner.py --level 1               # 运行Level 1")
        print("  python test_runner.py --level 1,3,5           # 运行指定Level")
        print("  python test_runner.py --start-level 3         # 从Level 3开始")
        print("  python test_runner.py --demo-mode --all       # 演示模式")
        print("  python test_runner.py --continue-on-failure   # 失败后继续")
        print()
        print("测试Level说明:")
        print("  Level 1: 基础数字生命 (LLMCell)")
        print("  Level 2: 思维思考能力 (+ MindCell)")
        print("  Level 3: 知识记忆能力 (+ StateMemoryCell)")
        print("  Level 4: 工具使用能力 (+ ToolCell)")
        print("  Level 5: 通信协作能力 (多生命体)")
        print("  Level 6: 学习反馈能力 (自我改进)")
        print("  Level 7: 杂交生成能力 (生命体融合)")
        print()
        
        # 默认运行Level 1演示
        print("🎯 默认运行Level 1演示...")
        sys.argv.extend(["--level", "1", "--demo-mode"])
    
    # 运行测试
    success = asyncio.run(main())
    exit(0 if success else 1)