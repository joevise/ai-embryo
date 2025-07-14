#!/usr/bin/env python3
"""
测试异步修复 - 验证UserProfileAdapter的异步调用是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent))

from futurembryo.core.context_builder import ContextBuilder
from futurembryo.adapters.user_profile_adapter import UserProfileAdapter

async def test_async_adapter():
    """测试异步适配器调用"""
    print("🧪 测试异步适配器调用...")
    
    # 创建用户画像适配器
    adapter = UserProfileAdapter({"user_id": "test_user"})
    
    # 测试process_async方法
    try:
        result = await adapter.process_async({
            "action": "get_user_profile"
        })
        print("✅ process_async调用成功")
        print(f"   结果: {result['success']}")
    except Exception as e:
        print(f"❌ process_async调用失败: {e}")
        return False
    
    return True

async def test_context_builder():
    """测试上下文构建器的异步调用"""
    print("\n🧪 测试上下文构建器...")
    
    # 创建上下文构建器
    builder = ContextBuilder(user_id="test_user", enable_memory=True)
    
    try:
        # 构建上下文
        context = await builder.build_context(
            user_input="测试输入",
            conversation_history=[]
        )
        print("✅ 上下文构建成功")
        print(f"   用户ID: {context.get('user_id')}")
        print(f"   时间戳: {context.get('timestamp')}")
    except Exception as e:
        print(f"❌ 上下文构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """主测试函数"""
    print("🚀 开始测试异步修复...")
    
    # 测试1：直接测试适配器
    test1_passed = await test_async_adapter()
    
    # 测试2：测试上下文构建器
    test2_passed = await test_context_builder()
    
    # 总结
    print("\n" + "="*50)
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！异步问题已修复")
        print("✅ UserProfileAdapter 正确支持异步调用")
        print("✅ ContextBuilder 正确使用异步接口")
    else:
        print("❌ 部分测试失败，请检查错误信息")
    
    return test1_passed and test2_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)