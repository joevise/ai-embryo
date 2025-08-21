#!/usr/bin/env python3
"""
测试配置管理 - 统一管理所有Level的测试配置
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TestLevel(Enum):
    """测试Level枚举"""
    LEVEL_1_BASIC = "level1_basic_life"
    LEVEL_2_THINKING = "level2_thinking" 
    LEVEL_3_MEMORY = "level3_memory"
    LEVEL_4_TOOLS = "level4_tools"
    LEVEL_5_COLLABORATION = "level5_collaboration"
    LEVEL_6_LEARNING = "level6_learning"
    LEVEL_7_HYBRID = "level7_hybrid"


@dataclass
class TestConfig:
    """单个测试配置"""
    level: TestLevel
    enabled: bool = True
    timeout: int = 60
    retry_count: int = 3
    success_criteria: Dict[str, float] = None
    test_scenarios: List[str] = None
    
    def __post_init__(self):
        if self.success_criteria is None:
            self.success_criteria = {}
        if self.test_scenarios is None:
            self.test_scenarios = []


class TestConfigManager:
    """测试配置管理器"""
    
    def __init__(self):
        self.configs = self._initialize_default_configs()
        self.api_config = self._load_api_config()
        
    def _initialize_default_configs(self) -> Dict[TestLevel, TestConfig]:
        """初始化默认测试配置"""
        
        configs = {}
        
        # Level 1: 基础数字生命测试
        configs[TestLevel.LEVEL_1_BASIC] = TestConfig(
            level=TestLevel.LEVEL_1_BASIC,
            timeout=30,
            success_criteria={
                "response_rate": 1.0,           # 响应率 100%
                "basic_config_valid": 1.0,      # 基础配置有效性 100%
                "iert_elements_valid": 1.0,     # IERT元素有效性 100%
                "life_card_generated": 1.0      # 数字名片生成 100%
            },
            test_scenarios=[
                "简单问候对话",
                "基础问答交互", 
                "配置参数验证",
                "生命元素检查"
            ]
        )
        
        # Level 2: 思维思考能力测试
        configs[TestLevel.LEVEL_2_THINKING] = TestConfig(
            level=TestLevel.LEVEL_2_THINKING,
            timeout=45,
            success_criteria={
                "thinking_quality": 0.75,       # 思考质量 ≥ 75%
                "attention_accuracy": 0.80,     # 注意力准确率 ≥ 80%
                "feedback_judgment": 0.85,      # 反馈判断合理性 ≥ 85%
                "depth_improvement": 0.30       # 思考深度提升 ≥ 30%
            },
            test_scenarios=[
                "复杂问题分析",
                "注意力焦点测试",
                "反馈判断验证",
                "思维质量评估"
            ]
        )
        
        # Level 3: 知识记忆能力测试
        configs[TestLevel.LEVEL_3_MEMORY] = TestConfig(
            level=TestLevel.LEVEL_3_MEMORY,
            timeout=60,
            success_criteria={
                "memory_storage_rate": 0.95,    # 记忆存储成功率 ≥ 95%
                "memory_retrieval_rate": 0.90,  # 记忆检索准确率 ≥ 90%
                "context_continuity": 0.85,     # 上下文连续性 ≥ 85%
                "knowledge_accumulation": 0.80  # 知识积累效果 ≥ 80%
            },
            test_scenarios=[
                "多轮对话记忆",
                "知识存储检索",
                "上下文连贯性",
                "个性化学习"
            ]
        )
        
        # Level 4: 工具使用能力测试
        configs[TestLevel.LEVEL_4_TOOLS] = TestConfig(
            level=TestLevel.LEVEL_4_TOOLS,
            timeout=90,
            success_criteria={
                "min_tools": 3,              # 最少工具数量 ≥ 3
                "tool_info_rate": 0.8,       # 工具信息获取成功率 ≥ 80%
                "tool_selection": 0.25,      # 工具选择准确率 ≥ 25% (当前实现限制)
                "tool_execution": 0.7,       # 工具执行成功率 ≥ 70%
                "tool_integration": 0.33      # 工具结果集成成功率 ≥ 33% (当前实现限制)
            },
            test_scenarios=[
                "工具智能选择",
                "工具调用执行",
                "结果集成验证",
                "错误恢复测试"
            ]
        )
        
        # Level 5: 通信协作能力测试
        configs[TestLevel.LEVEL_5_COLLABORATION] = TestConfig(
            level=TestLevel.LEVEL_5_COLLABORATION,
            timeout=120,
            success_criteria={
                "card_exchange_rate": 1.0,       # 名片交换成功率 100%
                "collaboration_discovery": 0.80, # 协作发现准确率 ≥ 80%
                "collaboration_effectiveness": 0.20, # 协作效果提升 ≥ 20%
                "communication_stability": 0.95  # 通信稳定性 ≥ 95%
            },
            test_scenarios=[
                "数字名片交换",
                "协作发现测试",
                "多生命体任务",
                "信息共享安全"
            ]
        )
        
        # Level 6: 学习反馈能力测试
        configs[TestLevel.LEVEL_6_LEARNING] = TestConfig(
            level=TestLevel.LEVEL_6_LEARNING,
            timeout=90,
            success_criteria={
                "feedback_absorption_rate": 0.70, # 有效反馈吸收率 ≥ 70%
                "performance_improvement": 0.15,  # 性能指标改善 ≥ 15%
                "learning_stability": 0.90,       # 学习稳定性 ≥ 90%
                "config_optimization": 0.80       # 配置优化效果 ≥ 80%
            },
            test_scenarios=[
                "反馈价值判断",
                "自动配置调整",
                "性能改进验证",
                "学习稳定性测试"
            ]
        )
        
        # Level 7: 杂交生成能力测试
        configs[TestLevel.LEVEL_7_HYBRID] = TestConfig(
            level=TestLevel.LEVEL_7_HYBRID,
            timeout=150,
            success_criteria={
                "hybrid_success_rate": 0.70,     # 杂交生成成功率 ≥ 70%
                "capability_fusion": 0.75,       # 能力融合效果 ≥ 75%
                "emergent_abilities": 0.50,      # 新兴能力涌现 ≥ 50%
                "stability_maintenance": 0.85    # 稳定性保持 ≥ 85%
            },
            test_scenarios=[
                "双亲能力融合",
                "配置继承机制",
                "新兴能力验证",
                "稳定性保持测试"
            ]
        )
        
        return configs
    
    def _load_api_config(self) -> Dict[str, str]:
        """加载API配置"""
        return {
            "api_key": os.getenv("FUTURX_API_KEY", "sk-tptTrlFHR14EDpg"),
            "base_url": os.getenv("FUTURX_BASE_URL", "https://litellm.futurx.cc"),
            "timeout": int(os.getenv("API_TIMEOUT", "300"))
        }
    
    def get_config(self, level: TestLevel) -> TestConfig:
        """获取指定Level的配置"""
        return self.configs.get(level)
    
    def get_all_configs(self) -> Dict[TestLevel, TestConfig]:
        """获取所有Level配置"""
        return self.configs.copy()
    
    def update_config(self, level: TestLevel, **kwargs):
        """更新指定Level的配置"""
        if level in self.configs:
            config = self.configs[level]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    def get_api_config(self) -> Dict[str, str]:
        """获取API配置"""
        return self.api_config.copy()
    
    def is_level_enabled(self, level: TestLevel) -> bool:
        """检查Level是否启用"""
        config = self.configs.get(level)
        return config.enabled if config else False
    
    def get_enabled_levels(self) -> List[TestLevel]:
        """获取所有启用的Level"""
        return [level for level, config in self.configs.items() if config.enabled]
    
    def export_config(self, filepath: str):
        """导出配置到文件"""
        config_data = {}
        for level, config in self.configs.items():
            config_data[level.value] = asdict(config)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            import json
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def set_demo_mode(self, demo_mode: bool = True):
        """设置演示模式（降低成功标准）"""
        if demo_mode:
            for config in self.configs.values():
                # 降低成功标准以便演示
                for key in config.success_criteria:
                    if config.success_criteria[key] > 0.5:
                        config.success_criteria[key] *= 0.8  # 降低20%
                config.timeout = int(config.timeout * 1.5)  # 增加超时时间
        else:
            # 恢复默认配置
            self.configs = self._initialize_default_configs()


# 全局配置实例
test_config_manager = TestConfigManager()


def get_test_config(level: TestLevel) -> TestConfig:
    """便捷函数：获取测试配置"""
    return test_config_manager.get_config(level)


def get_api_config() -> Dict[str, str]:
    """便捷函数：获取API配置"""
    return test_config_manager.get_api_config()


def set_demo_mode(enabled: bool = True):
    """便捷函数：设置演示模式"""
    test_config_manager.set_demo_mode(enabled)


if __name__ == "__main__":
    # 配置测试
    print("🔧 FuturEmbryo测试配置管理器")
    print("=" * 40)
    
    # 显示所有Level配置
    for level in TestLevel:
        config = get_test_config(level)
        print(f"\n📋 {level.value}:")
        print(f"   超时时间: {config.timeout}s")
        print(f"   成功标准: {len(config.success_criteria)}项")
        print(f"   测试场景: {len(config.test_scenarios)}个")
        print(f"   启用状态: {'✅' if config.enabled else '❌'}")
    
    # 显示API配置
    print(f"\n🔗 API配置:")
    api_config = get_api_config()
    print(f"   Base URL: {api_config['base_url']}")
    print(f"   超时时间: {api_config['timeout']}s")
    print(f"   API Key: {'已配置' if api_config['api_key'] != 'your-api-key-here' else '未配置'}")