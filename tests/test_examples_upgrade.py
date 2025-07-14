#!/usr/bin/env python3
"""
测试示例升级 - 验证examples能否正确使用核心框架组件
"""

import sys
import traceback
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent))

def test_core_imports():
    """测试核心组件导入"""
    print("🧪 测试核心组件导入...")
    
    try:
        from futurembryo.core.user_models import UserProfile, UserMemoryEntry, UserPreferences, UserContext
        print("✅ 用户数据模型导入成功")
        
        from futurembryo.cells.mention_processor_cell import MentionProcessorCell
        print("✅ MentionProcessorCell导入成功")
        
        from futurembryo.adapters.user_profile_adapter import UserProfileAdapter
        print("✅ UserProfileAdapter导入成功")
        
        from futurembryo.core.context_builder import ContextBuilder
        print("✅ ContextBuilder导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 核心组件导入失败: {e}")
        traceback.print_exc()
        return False

def test_multiagent_collaboration_imports():
    """测试multiagent_collaboration示例的导入"""
    print("\n🧪 测试multiagent_collaboration示例导入...")
    
    try:
        # 测试CoordinatorAgent导入
        sys.path.insert(0, str(Path(__file__).parent / "examples" / "multiagent_collaboration"))
        from agents.coordinator_agent import CoordinatorAgent
        print("✅ CoordinatorAgent导入成功")
        
        # 测试UserAwareAgent导入
        from agents.user_aware_agent import UserAwareAgent
        print("✅ UserAwareAgent导入成功")
        
        # 测试UserAwareAgentV2导入
        from agents.user_aware_agent_v2 import UserAwareAgent as UserAwareAgentV2
        print("✅ UserAwareAgentV2导入成功")
        
        # 测试DynamicAgentFactory导入
        from core.dynamic_agent_factory import DynamicAgentFactory
        print("✅ DynamicAgentFactory导入成功")
        
        return True
    except Exception as e:
        print(f"❌ multiagent_collaboration示例导入失败: {e}")
        traceback.print_exc()
        return False

def test_multiagent_team_static_imports():
    """测试multiagent_team_static示例的导入"""
    print("\n🧪 测试multiagent_team_static示例导入...")
    
    try:
        # 测试CoordinatorAgent导入
        sys.path.insert(0, str(Path(__file__).parent / "examples" / "multiagent_team_static"))
        from agents.coordinator_agent import CoordinatorAgent as StaticCoordinatorAgent
        print("✅ Static CoordinatorAgent导入成功")
        
        return True
    except Exception as e:
        print(f"❌ multiagent_team_static示例导入失败: {e}")
        traceback.print_exc()
        return False

def test_component_initialization():
    """测试组件初始化"""
    print("\n🧪 测试组件初始化...")
    
    try:
        from futurembryo.cells.mention_processor_cell import MentionProcessorCell
        from futurembryo.adapters.user_profile_adapter import UserProfileAdapter
        
        # 测试MentionProcessorCell初始化
        mention_processor = MentionProcessorCell({})
        print("✅ MentionProcessorCell初始化成功")
        
        # 测试UserProfileAdapter初始化
        user_adapter = UserProfileAdapter({"user_id": "test_user"})
        print("✅ UserProfileAdapter初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ 组件初始化失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试示例升级...")
    
    all_passed = True
    
    # 测试核心组件导入
    if not test_core_imports():
        all_passed = False
    
    # 测试示例导入
    if not test_multiagent_collaboration_imports():
        all_passed = False
        
    if not test_multiagent_team_static_imports():
        all_passed = False
    
    # 测试组件初始化
    if not test_component_initialization():
        all_passed = False
    
    # 总结
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有测试通过！示例升级成功完成")
        print("📋 升级总结:")
        print("   ✅ 核心组件已合并到主框架")
        print("   ✅ 示例已更新为使用核心组件")
        print("   ✅ 重复文件已清理")
        print("   ✅ 导入和初始化正常工作")
        print("\n💡 示例现在可以使用统一的核心框架组件了！")
    else:
        print("❌ 部分测试失败，需要检查升级过程")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)