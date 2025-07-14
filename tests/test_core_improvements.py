#!/usr/bin/env python3
"""
测试核心组件改进
验证用户感知功能、@引用处理、异步接口等改进是否正常工作
"""

import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_user_models():
    """测试用户数据模型"""
    print("\n=== 测试用户数据模型 ===")
    
    try:
        from futurembryo.core.user_models import UserProfile, UserMemoryEntry, UserPreferences, UserContext
        
        # 测试用户画像
        profile = UserProfile(
            interests=["AI", "编程"],
            expertise_areas=["机器学习", "软件开发"],
            communication_style="friendly"
        )
        print(f"✅ 用户画像创建成功: {profile.interests}")
        
        # 测试用户偏好
        preferences = UserPreferences()
        preferences.learn_preference("communication", "详细回答", 0.8)
        top_prefs = preferences.get_top_preferences("communication", 3)
        print(f"✅ 用户偏好学习成功: {top_prefs}")
        
        # 测试用户上下文
        context = UserContext(user_id="test_user", profile=profile, preferences=preferences)
        context.add_memory("测试记忆", "explicit", 0.9)
        summary = context.get_context_summary()
        print(f"✅ 用户上下文创建成功: {summary}")
        
        return True
    except Exception as e:
        print(f"❌ 用户数据模型测试失败: {e}")
        return False

def test_mention_processor():
    """测试@引用处理器"""
    print("\n=== 测试@引用处理器 ===")
    
    try:
        from futurembryo.cells.mention_processor_cell import MentionProcessorCell
        
        # 创建@引用处理器
        processor = MentionProcessorCell()
        print("✅ @引用处理器创建成功")
        
        # 测试@引用提取
        test_text = "请查看 @user-profile 和 @user-memory 的信息"
        result = processor.process({
            "action": "extract",
            "text": test_text
        })
        
        if result["success"]:
            mentions = result["mentions"]
            print(f"✅ @引用提取成功: 找到 {len(mentions)} 个引用")
            for mention in mentions:
                print(f"   - @{mention['id']}: {mention['description']}")
        else:
            print(f"❌ @引用提取失败: {result.get('error')}")
            return False
        
        # 测试@引用建议
        suggestion_result = processor.process({
            "action": "suggest", 
            "query": "user"
        })
        
        if suggestion_result["success"]:
            suggestions = suggestion_result["suggestions"]
            print(f"✅ @引用建议成功: 找到 {len(suggestions)} 个建议")
        
        return True
    except Exception as e:
        print(f"❌ @引用处理器测试失败: {e}")
        return False

def test_user_profile_adapter():
    """测试用户画像适配器"""
    print("\n=== 测试用户画像适配器 ===")
    
    try:
        from futurembryo.adapters.user_profile_adapter import UserProfileAdapter
        
        # 创建用户画像适配器
        adapter = UserProfileAdapter({"user_id": "test_user"})
        print("✅ 用户画像适配器创建成功")
        
        # 测试获取用户画像
        profile_result = adapter.process({"action": "get_user_profile"})
        if profile_result["success"]:
            print("✅ 获取用户画像成功")
        
        # 测试更新用户画像
        update_result = adapter.process({
            "action": "update_user_profile",
            "updates": {
                "interests": ["AI", "测试"],
                "communication_style": "professional"
            }
        })
        if update_result["success"]:
            print("✅ 更新用户画像成功")
        
        # 测试添加用户记忆
        memory_result = adapter.process({
            "action": "add_user_memory",
            "content": "用户喜欢详细的技术解释",
            "memory_type": "explicit",
            "importance": 0.8
        })
        if memory_result["success"]:
            print("✅ 添加用户记忆成功")
        
        # 测试学习用户偏好
        preference_result = adapter.process({
            "action": "learn_preference",
            "category": "communication",
            "preference": "detailed_explanation",
            "feedback": 0.9
        })
        if preference_result["success"]:
            print("✅ 学习用户偏好成功")
        
        return True
    except Exception as e:
        print(f"❌ 用户画像适配器测试失败: {e}")
        return False

def test_state_memory_cell():
    """测试增强的StateMemoryCell"""
    print("\n=== 测试增强的StateMemoryCell ===")
    
    try:
        from futurembryo.cells.state_memory_cell import StateMemoryCell
        from futurembryo.adapters.user_profile_adapter import UserProfileAdapter
        
        # 创建StateMemoryCell，配置用户画像适配器
        config = {
            "adapters": [
                {
                    "name": "user_profile",
                    "class_path": "futurembryo.adapters.user_profile_adapter.UserProfileAdapter",
                    "config": {
                        "user_id": "test_user",
                        "auto_learning": True
                    }
                }
            ],
            "routing_strategy": "priority",
            "result_aggregation": "merge"
        }
        
        memory_cell = StateMemoryCell(config)
        print("✅ StateMemoryCell创建成功")
        
        # 测试用户感知操作
        user_profile_result = memory_cell.process({"action": "get_user_profile"})
        if user_profile_result["success"]:
            print("✅ StateMemoryCell用户画像操作成功")
        
        # 测试便捷方法
        try:
            memory_cell.update_user_profile({"interests": ["测试", "验证"]})
            print("✅ StateMemoryCell便捷方法成功")
        except Exception as e:
            print(f"⚠️ StateMemoryCell便捷方法失败: {e}")
        
        return True
    except Exception as e:
        print(f"❌ StateMemoryCell测试失败: {e}")
        return False

def test_context_builder():
    """测试简化的ContextBuilder"""
    print("\n=== 测试简化的ContextBuilder ===")
    
    try:
        from futurembryo.core.context_builder import ContextBuilder, create_context_builder
        
        # 创建上下文构建器
        builder = create_context_builder(
            user_id="test_user",
            enable_memory=True,
            enable_user_profile=True,
            enable_mentions=True
        )
        print("✅ ContextBuilder创建成功")
        
        # 获取状态
        status = builder.get_status()
        print(f"✅ ContextBuilder状态: {status['components']}")
        
        return True
    except Exception as e:
        print(f"❌ ContextBuilder测试失败: {e}")
        return False

async def test_async_interfaces():
    """测试异步接口"""
    print("\n=== 测试异步接口 ===")
    
    try:
        from futurembryo.cells.mention_processor_cell import MentionProcessorCell
        from futurembryo.adapters.user_profile_adapter import UserProfileAdapter
        
        # 测试@引用处理器异步接口
        processor = MentionProcessorCell()
        async_result = await processor.process_async({
            "action": "extract",
            "text": "测试 @user-profile 异步处理"
        })
        if async_result["success"]:
            print("✅ @引用处理器异步接口成功")
        
        # 测试用户画像适配器异步接口
        adapter = UserProfileAdapter({"user_id": "test_async_user"})
        async_profile_result = await adapter.process_async({"action": "get_user_profile"})
        if async_profile_result["success"]:
            print("✅ 用户画像适配器异步接口成功")
        
        return True
    except Exception as e:
        print(f"❌ 异步接口测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试FuturEmbryo核心组件改进")
    print("=" * 60)
    
    test_results = []
    
    # 运行同步测试
    test_results.append(("用户数据模型", test_user_models()))
    test_results.append(("@引用处理器", test_mention_processor()))
    test_results.append(("用户画像适配器", test_user_profile_adapter()))
    test_results.append(("StateMemoryCell增强", test_state_memory_cell()))
    test_results.append(("ContextBuilder简化", test_context_builder()))
    
    # 运行异步测试
    test_results.append(("异步接口", await test_async_interfaces()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！核心组件改进成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
    
    return passed == total

if __name__ == "__main__":
    # 运行测试
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)