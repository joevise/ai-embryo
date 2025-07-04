#!/usr/bin/env python3
"""
FuturEmbryo多智能体协作系统 - 快速开始示例

展示最基本的使用方法，用户可以复制此文件开始自己的项目
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from futurembryo import setup_futurx_api
from agents.user_aware_agent_v2 import UserAwareAgent


async def basic_example():
    """基础使用示例"""
    print("🚀 FuturEmbryo多智能体协作 - 基础示例")
    print("=" * 50)
    
    # 1. 设置API
    setup_futurx_api(
        api_key="your-api-key",  # 替换为你的API密钥
        base_url="https://litellm.futurx.cc"
    )
    
    # 2. 创建一个简单的研究员Agent
    researcher_config = {
        "name": "研究员小助手",
        "description": "帮助用户进行信息研究",
        "role": "researcher",
        "capabilities": ["信息检索", "报告撰写"],
        "personality": ["专业", "细致"],
        
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 2000,
            "system_prompt": "你是一个专业的研究员，擅长收集和分析信息。"
        },
        
        "user_memory_config": {
            "auto_learning": True,
            "explicit_memory_keywords": ["记住", "重要"]
        }
    }
    
    # 3. 初始化Agent
    researcher = UserAwareAgent("researcher", researcher_config)
    print("✅ 研究员Agent创建成功")
    
    # 4. 进行对话
    print("\\n💬 开始对话演示...")
    
    # 第一轮：告诉系统用户兴趣
    user_input1 = "我对人工智能技术很感兴趣，特别是多智能体协作，请记住这个"
    print(f"👤 用户: {user_input1}")
    
    result1 = await asyncio.to_thread(
        researcher.process_user_input, 
        user_input1
    )
    
    if result1["success"]:
        print(f"🤖 助手: {result1['data']['response']}")
    
    # 第二轮：基于用户兴趣进行研究
    user_input2 = "帮我研究一下多智能体协作的最新发展趋势"
    print(f"\\n👤 用户: {user_input2}")
    
    result2 = await asyncio.to_thread(
        researcher.process_user_input, 
        user_input2, 
        [
            {"role": "user", "content": user_input1},
            {"role": "assistant", "content": result1['data']['response']}
        ]
    )
    
    if result2["success"]:
        print(f"🤖 助手: {result2['data']['response']}")
        
        # 显示生成的产出物
        deliverables = result2['data'].get('deliverables', [])
        if deliverables:
            print("\\n📊 生成的产出物:")
            for d in deliverables:
                print(f"   • {d['mention']} - {d['name']}")
    
    # 第三轮：使用@引用查看用户画像
    user_input3 = "显示我的@user-profile"
    print(f"\\n👤 用户: {user_input3}")
    
    result3 = await asyncio.to_thread(
        researcher.process_user_input,
        user_input3,
        []
    )
    
    if result3["success"]:
        print(f"🤖 助手: {result3['data']['response']}")
    
    print("\\n✅ 基础示例完成！")


async def multi_agent_example():
    """多智能体协作示例"""
    print("\\n🤖 多智能体协作示例")
    print("=" * 50)
    
    # 设置API
    setup_futurx_api(
        api_key="your-api-key",  # 替换为你的API密钥
        base_url="https://litellm.futurx.cc"
    )
    
    # 创建研究员Agent
    researcher = UserAwareAgent("researcher", {
        "name": "研究员",
        "role": "researcher",
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.3,
            "system_prompt": "你是一个专业研究员，负责信息收集和初步分析。"
        }
    })
    
    # 创建写作者Agent
    writer = UserAwareAgent("writer", {
        "name": "写作者", 
        "role": "writer",
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.6,
            "system_prompt": "你是一个专业写作者，负责整理和编写清晰的报告。"
        }
    })
    
    print("✅ 多个Agent创建成功")
    
    # 协作流程演示
    user_request = "我需要一份关于AI发展趋势的报告"
    print(f"\\n👤 用户需求: {user_request}")
    
    # 1. 研究员收集信息
    print("\\n🔍 研究员收集信息...")
    research_result = await asyncio.to_thread(
        researcher.process_user_input,
        f"@researcher 请研究AI发展趋势，收集相关信息: {user_request}"
    )
    
    if research_result["success"]:
        research_content = research_result["data"]["response"]
        print(f"📊 研究结果: {research_content[:200]}...")
        
        # 2. 写作者整理报告
        print("\\n✍️ 写作者整理报告...")
        write_request = f"@writer 基于以下研究内容写一份AI发展趋势报告:\\n{research_content}"
        
        write_result = await asyncio.to_thread(
            writer.process_user_input,
            write_request
        )
        
        if write_result["success"]:
            final_report = write_result["data"]["response"]
            print(f"📝 最终报告: {final_report[:300]}...")
            
            # 显示产出物
            deliverables = write_result["data"].get("deliverables", [])
            if deliverables:
                print("\\n📊 生成的产出物:")
                for d in deliverables:
                    print(f"   • {d['mention']} - {d['name']}")
    
    print("\\n✅ 多智能体协作示例完成！")


async def mention_system_example():
    """@引用系统示例"""
    print("\\n📝 @引用系统示例")
    print("=" * 50)
    
    # 设置API
    setup_futurx_api(
        api_key="your-api-key",  # 替换为你的API密钥
        base_url="https://litellm.futurx.cc"
    )
    
    # 创建Agent
    agent = UserAwareAgent("assistant", {
        "name": "智能助手",
        "role": "assistant",
        "llm_config": {
            "model": "gpt-4",
            "system_prompt": "你是一个智能助手，能理解@引用并提供个性化服务。"
        }
    })
    
    print("✅ 智能助手创建成功")
    
    # @引用功能演示
    examples = [
        "我喜欢技术和投资，记住这些兴趣",
        "显示我的@user-profile信息", 
        "基于@user-memory为我推荐相关内容",
        "根据@user-preferences调整你的回复风格"
    ]
    
    conversation_history = []
    
    for i, example in enumerate(examples, 1):
        print(f"\\n{i}. 👤 用户: {example}")
        
        result = await asyncio.to_thread(
            agent.process_user_input,
            example,
            conversation_history
        )
        
        if result["success"]:
            response = result["data"]["response"]
            print(f"   🤖 助手: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # 更新对话历史
            conversation_history.extend([
                {"role": "user", "content": example},
                {"role": "assistant", "content": response}
            ])
            
            # 保持历史长度
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
    
    print("\\n✅ @引用系统示例完成！")


async def custom_agent_example():
    """自定义Agent示例"""
    print("\\n🛠️ 自定义Agent示例")
    print("=" * 50)
    
    # 设置API
    setup_futurx_api(
        api_key="your-api-key",  # 替换为你的API密钥
        base_url="https://litellm.futurx.cc"
    )
    
    # 创建自定义的投资顾问Agent
    investment_advisor_config = {
        "name": "投资顾问",
        "description": "专业的投资建议和分析专家",
        "role": "analyst",
        "capabilities": ["投资分析", "风险评估", "市场研究"],
        "personality": ["专业", "谨慎", "客观"],
        
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.2,  # 较低温度，确保专业和准确
            "max_tokens": 3000,
            "system_prompt": \"\"\"你是一个专业的投资顾问，具有以下特质：
            
            专业能力：
            - 投资分析：能够分析投资机会和风险
            - 市场研究：了解市场趋势和经济指标
            - 风险管理：评估投资风险并提供建议
            
            工作原则：
            - 基于数据和分析做出建议
            - 明确风险和不确定性
            - 根据用户风险偏好定制建议
            - 提供教育性的解释
            
            注意：所有建议仅供参考，不构成具体投资建议。\"\"\"
        },
        
        "user_memory_config": {
            "auto_learning": True,
            "explicit_memory_keywords": ["记住", "重要", "风险偏好", "投资目标"]
        }
    }
    
    # 创建Agent
    advisor = UserAwareAgent("investment_advisor", investment_advisor_config)
    print("✅ 投资顾问Agent创建成功")
    
    # 使用示例
    examples = [
        "我是风险厌恶型投资者，偏好稳健投资，请记住这个",
        "分析一下当前AI行业的投资机会",
        "基于我的@user-profile给我一些适合的投资建议"
    ]
    
    conversation_history = []
    
    for i, example in enumerate(examples, 1):
        print(f"\\n{i}. 👤 用户: {example}")
        
        result = await asyncio.to_thread(
            advisor.process_user_input,
            example,
            conversation_history
        )
        
        if result["success"]:
            response = result["data"]["response"]
            print(f"   💼 投资顾问: {response[:300]}{'...' if len(response) > 300 else ''}")
            
            # 更新对话历史
            conversation_history.extend([
                {"role": "user", "content": example},
                {"role": "assistant", "content": response}
            ])
    
    print("\\n✅ 自定义Agent示例完成！")


async def main():
    """主函数 - 运行所有示例"""
    print("🌟 FuturEmbryo多智能体协作系统")
    print("快速开始示例集合")
    print()
    
    try:
        # 运行各种示例
        await basic_example()
        await multi_agent_example() 
        await mention_system_example()
        await custom_agent_example()
        
        print("\\n🎉 所有示例运行完成！")
        print("\\n💡 接下来你可以:")
        print("   • 修改配置文件创建自己的Agent")
        print("   • 运行完整的交互式演示: python multiagent_demo.py")
        print("   • 查看详细文档了解更多功能")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        print("\\n🔧 故障排除:")
        print("   • 检查API密钥是否正确设置")
        print("   • 确保网络连接正常") 
        print("   • 检查依赖是否正确安装")


if __name__ == "__main__":
    # 注意：运行前请设置正确的API密钥
    print("⚠️  注意：请在代码中设置正确的API密钥后运行")
    print("   在 setup_futurx_api() 调用中替换 'your-api-key'")
    print()
    
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())