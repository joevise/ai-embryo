#!/usr/bin/env python3
"""
测试工具模块 - 提供通用的测试辅助函数
"""

import sys
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from contextlib import asynccontextmanager
import traceback

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from futurembryo import setup_futurx_api
    from futurembryo.dna.life_grower import LifeGrower, AILifeForm
    from futurembryo.core.autonomous_growth import AutonomousGrowthEngine
except ImportError as e:
    print(f"⚠️  导入FuturEmbryo模块失败: {e}")
    print("请确保已安装框架: pip install -e .")


class TestResult:
    """测试结果封装"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.error_message = ""
        self.execution_time = 0.0
        self.metrics = {}
        self.artifacts = {}  # 测试产生的对象
        self.start_time = time.time()
    
    def mark_success(self, metrics: Dict[str, Any] = None):
        """标记测试成功"""
        self.success = True
        self.execution_time = time.time() - self.start_time
        if metrics:
            self.metrics.update(metrics)
    
    def mark_failure(self, error: str):
        """标记测试失败"""
        self.success = False
        self.error_message = error
        self.execution_time = time.time() - self.start_time
    
    def add_artifact(self, name: str, obj: Any):
        """添加测试产生的对象"""
        self.artifacts[name] = obj
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_name": self.test_name,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "metrics": self.metrics,
            "artifacts_count": len(self.artifacts)
        }


class TestEnvironment:
    """测试环境管理"""
    
    def __init__(self):
        self.grower: Optional[LifeGrower] = None
        self.life_forms: Dict[str, AILifeForm] = {}
        self.logger = self._setup_logger()
        self.api_configured = False
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(f"FuturEmbryoTest")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def initialize(self, api_config: Dict[str, str] = None):
        """初始化测试环境"""
        try:
            # 配置API
            if api_config:
                setup_futurx_api(
                    api_key=api_config.get("api_key", "demo-key"),
                    base_url=api_config.get("base_url", "https://litellm.futurx.cc")
                )
                self.api_configured = True
                self.logger.info("✅ API配置完成")
            else:
                self.logger.warning("⚠️  未提供API配置，使用演示模式")
            
            # 创建生命成长器
            self.grower = LifeGrower()
            
            # 检查自主生长引擎
            if self.grower.autonomous_engine:
                self.logger.info("🧪 自主生长引擎已启用")
            else:
                self.logger.warning("❌ 自主生长引擎未启用")
            
            self.logger.info("🌱 测试环境初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 测试环境初始化失败: {e}")
            raise
    
    async def create_basic_life(self, goal: str, constraints: Dict[str, Any] = None) -> AILifeForm:
        """创建基础生命体"""
        if not self.grower:
            raise RuntimeError("测试环境未初始化")
        
        try:
            result = await self.grower.grow_from_natural_language(
                goal_description=goal,
                constraints=constraints or {},
                auto_instantiate=True
            )
            
            if result["success"] and "life_form" in result:
                life_form = result["life_form"]
                self.life_forms[life_form.dna.name] = life_form
                return life_form
            else:
                raise RuntimeError(f"生命体创建失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            self.logger.error(f"创建生命体失败: {e}")
            raise
    
    def get_life_form(self, name: str) -> Optional[AILifeForm]:
        """获取已创建的生命体"""
        return self.life_forms.get(name)
    
    def cleanup(self):
        """清理测试环境"""
        self.life_forms.clear()
        self.logger.info("🧹 测试环境已清理")


class TestRunner:
    """测试运行器"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.environment = TestEnvironment()
        self.results: List[TestResult] = []
    
    @asynccontextmanager
    async def run_test(self, test_func_name: str):
        """运行单个测试的上下文管理器"""
        result = TestResult(test_func_name)
        
        try:
            yield result
            if not result.success and not result.error_message:
                result.mark_success()
        except Exception as e:
            result.mark_failure(f"{str(e)}\n{traceback.format_exc()}")
            self.environment.logger.error(f"测试失败 {test_func_name}: {e}")
        finally:
            self.results.append(result)
    
    async def initialize_environment(self, api_config: Dict[str, str] = None):
        """初始化测试环境"""
        await self.environment.initialize(api_config)
    
    def get_success_rate(self) -> float:
        """获取测试成功率"""
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.success) / len(self.results)
    
    def get_total_time(self) -> float:
        """获取总执行时间"""
        return sum(r.execution_time for r in self.results)
    
    def print_summary(self):
        """打印测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        print(f"\n📊 {self.test_name} 测试摘要")
        print("=" * 50)
        print(f"总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"成功率: {self.get_success_rate()*100:.1f}%")
        print(f"总耗时: {self.get_total_time():.2f}s")
        
        if failed > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.results:
                if not result.success:
                    print(f"   • {result.test_name}: {result.error_message}")
    
    def cleanup(self):
        """清理测试环境"""
        self.environment.cleanup()


def validate_life_form_basic(life_form: AILifeForm) -> Dict[str, bool]:
    """验证生命体基础功能"""
    validations = {}
    
    try:
        # 检查基础属性
        validations["has_dna"] = hasattr(life_form, 'dna') and life_form.dna is not None
        validations["has_cells"] = hasattr(life_form, 'cells') and len(life_form.cells) > 0
        validations["has_name"] = hasattr(life_form.dna, 'name') and bool(life_form.dna.name)
        
        # 检查生命体状态
        validations["is_alive"] = getattr(life_form, 'is_alive', False)
        
        # 检查基础方法
        validations["has_think_method"] = hasattr(life_form, 'think')
        validations["has_status_method"] = hasattr(life_form, 'get_status')
        
        # 检查生命元素
        if life_form.cells:
            main_cell = life_form.cells[0]
            validations["has_life_elements"] = hasattr(main_cell, 'life_elements')
            
            if hasattr(main_cell, 'life_elements'):
                validations["dll_signature_valid"] = bool(main_cell.get_dll_signature())
        
        # 检查数字名片
        validations["has_life_card"] = hasattr(life_form, 'life_card_data')
        
    except Exception as e:
        logging.getLogger("TestUtils").error(f"生命体验证失败: {e}")
        validations["validation_error"] = False
    
    return validations


async def test_basic_interaction(life_form: AILifeForm, test_inputs: List[str]) -> Dict[str, Any]:
    """测试基础交互能力"""
    results = {
        "total_tests": len(test_inputs),
        "successful_responses": 0,
        "response_times": [],
        "responses": []
    }
    
    for test_input in test_inputs:
        try:
            start_time = time.time()
            response = await life_form.think(test_input)
            response_time = time.time() - start_time
            
            results["response_times"].append(response_time)
            
            if response.get("success", False):
                results["successful_responses"] += 1
                results["responses"].append({
                    "input": test_input,
                    "success": True,
                    "response_time": response_time,
                    "response_length": len(str(response.get("data", {}).get("response", "")))
                })
            else:
                results["responses"].append({
                    "input": test_input,
                    "success": False,
                    "error": response.get("error", "未知错误"),
                    "response_time": response_time
                })
                
        except Exception as e:
            results["responses"].append({
                "input": test_input,
                "success": False,
                "error": str(e),
                "response_time": 0
            })
    
    # 计算统计信息
    if results["response_times"]:
        results["avg_response_time"] = sum(results["response_times"]) / len(results["response_times"])
        results["max_response_time"] = max(results["response_times"])
        results["min_response_time"] = min(results["response_times"])
    
    results["success_rate"] = results["successful_responses"] / results["total_tests"]
    
    return results


def assert_success_rate(actual_rate: float, expected_rate: float, test_name: str):
    """断言成功率"""
    if actual_rate < expected_rate:
        raise AssertionError(
            f"{test_name}: 成功率 {actual_rate*100:.1f}% 低于期望 {expected_rate*100:.1f}%"
        )


def assert_response_time(actual_time: float, max_time: float, test_name: str):
    """断言响应时间"""
    if actual_time > max_time:
        raise AssertionError(
            f"{test_name}: 响应时间 {actual_time:.2f}s 超过最大允许时间 {max_time:.2f}s"
        )


def assert_metric_threshold(metrics: Dict[str, float], thresholds: Dict[str, float], test_name: str):
    """断言指标阈值"""
    for metric, threshold in thresholds.items():
        if metric not in metrics:
            raise AssertionError(f"{test_name}: 缺少指标 {metric}")
        
        actual = metrics[metric]
        if actual < threshold:
            raise AssertionError(
                f"{test_name}: 指标 {metric} 值 {actual:.3f} 低于阈值 {threshold:.3f}"
            )


if __name__ == "__main__":
    # 测试工具自检
    print("🔧 FuturEmbryo测试工具自检")
    print("=" * 40)
    
    async def self_test():
        # 创建测试环境
        env = TestEnvironment()
        
        try:
            await env.initialize()
            print("✅ 测试环境初始化成功")
            
            # 创建简单生命体
            life = await env.create_basic_life(
                "创建一个简单的测试助手",
                {"architecture": "single", "cell_types": ["LLMCell"]}
            )
            print(f"✅ 生命体创建成功: {life.dna.name}")
            
            # 验证基础功能
            validations = validate_life_form_basic(life)
            passed_validations = sum(1 for v in validations.values() if v)
            print(f"✅ 基础验证通过: {passed_validations}/{len(validations)}")
            
            # 测试交互
            test_results = await test_basic_interaction(life, ["你好", "测试"])
            print(f"✅ 交互测试成功率: {test_results['success_rate']*100:.1f}%")
            
        except Exception as e:
            print(f"❌ 自检失败: {e}")
        finally:
            env.cleanup()
    
    asyncio.run(self_test())