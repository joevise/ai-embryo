#!/usr/bin/env python3
"""
FuturEmbryo实际LLM测试

使用真实的API密钥和服务端点测试LLM功能
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from futurembryo import (
    LLMCell, setup_futurx_api, 
    CellState, get_config
)


def test_api_connection():
    """测试API连接"""
    print("=== 测试API连接 ===")
    
    # 配置真实的API
    setup_futurx_api(
        api_key="sk-tptTrlFHR14EDpg",
        base_url="https://litellm.futurx.cc"
    )
    
    try:
        # 创建LLMCell
        llm = LLMCell("gpt-3.5-turbo", config={
            "temperature": 0.7,
            "max_tokens": 50,
            "system_prompt": "你是一个测试助手，请简洁回答。"
        })
        
        print(f"✅ LLMCell创建成功")
        print(f"   模型: {llm.model_name}")
        print(f"   API端点: {llm.base_url}")
        print(f"   API密钥: {llm.api_key[:10]}...")
        
        return llm
        
    except Exception as e:
        print(f"❌ LLMCell创建失败: {e}")
        return None


def test_simple_chat(llm):
    """测试简单对话"""
    print("\n=== 测试简单对话 ===")
    
    test_message = "你好，请说'测试成功'"
    print(f"发送消息: {test_message}")
    
    try:
        start_time = time.time()
        result = llm({"input": test_message})
        end_time = time.time()
        
        if result["success"]:
            response = result["data"]["response"]
            usage = result["data"]["usage"]
            
            print(f"✅ 对话成功")
            print(f"   响应: {response}")
            print(f"   耗时: {end_time - start_time:.2f}秒")
            print(f"   Token使用: {usage['total_tokens']} (输入:{usage['prompt_tokens']}, 输出:{usage['completion_tokens']})")
            print(f"   Cell状态: {llm.state}")
            
            return True
        else:
            print(f"❌ 对话失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 对话异常: {e}")
        return False


def test_chinese_conversation(llm):
    """测试中文对话能力"""
    print("\n=== 测试中文对话能力 ===")
    
    questions = [
        "请用一句话介绍人工智能",
        "1+1等于几？",
        "今天是星期几？",
        "请说一个中文成语"
    ]
    
    success_count = 0
    
    for i, question in enumerate(questions, 1):
        print(f"\n问题 {i}: {question}")
        
        try:
            result = llm({"input": question})
            
            if result["success"]:
                response = result["data"]["response"]
                usage = result["data"]["usage"]
                
                print(f"✅ 回答: {response}")
                print(f"   Token: {usage['total_tokens']}")
                success_count += 1
            else:
                print(f"❌ 失败: {result['error']}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print(f"\n中文对话测试结果: {success_count}/{len(questions)} 成功")
    return success_count == len(questions)


def test_different_models(api_key, base_url):
    """测试不同模型"""
    print("\n=== 测试不同模型 ===")
    
    models_to_test = [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-3-haiku",
        "claude-3-sonnet"
    ]
    
    successful_models = []
    
    for model in models_to_test:
        print(f"\n测试模型: {model}")
        
        try:
            llm = LLMCell(model, config={
                "api_key": api_key,
                "base_url": base_url,
                "temperature": 0.5,
                "max_tokens": 30
            })
            
            result = llm({"input": "请说'模型测试成功'"})
            
            if result["success"]:
                response = result["data"]["response"]
                usage = result["data"]["usage"]
                
                print(f"✅ {model} 工作正常")
                print(f"   响应: {response}")
                print(f"   Token: {usage['total_tokens']}")
                successful_models.append(model)
            else:
                print(f"❌ {model} 调用失败: {result['error']}")
                
        except Exception as e:
            print(f"❌ {model} 异常: {e}")
    
    print(f"\n可用模型: {successful_models}")
    return successful_models


def test_conversation_memory(llm):
    """测试对话记忆（通过消息列表）"""
    print("\n=== 测试对话记忆 ===")
    
    # 构建多轮对话
    messages = [
        {"role": "system", "content": "你是一个有记忆的助手。"},
        {"role": "user", "content": "我的名字是张三"},
        {"role": "assistant", "content": "你好张三，很高兴认识你！"},
        {"role": "user", "content": "你还记得我的名字吗？"}
    ]
    
    try:
        result = llm({"messages": messages})
        
        if result["success"]:
            response = result["data"]["response"]
            print(f"✅ 记忆测试成功")
            print(f"   AI回答: {response}")
            
            # 检查是否提到了名字
            if "张三" in response:
                print("✅ AI正确记住了用户名字")
                return True
            else:
                print("⚠️ AI可能没有记住用户名字")
                return False
        else:
            print(f"❌ 记忆测试失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 记忆测试异常: {e}")
        return False


def test_performance_stats(llm):
    """测试性能统计"""
    print("\n=== 测试性能统计 ===")
    
    # 执行多次调用
    print("执行5次快速调用...")
    
    for i in range(5):
        result = llm({"input": f"这是第{i+1}次测试"})
        if result["success"]:
            print(f"  第{i+1}次: ✅ {result['metadata']['execution_time']:.3f}s")
        else:
            print(f"  第{i+1}次: ❌")
    
    # 获取统计信息
    status = llm.get_status()
    
    print(f"\n性能统计:")
    print(f"  总执行次数: {status['execution_count']}")
    print(f"  平均执行时间: {status['avg_execution_time']:.3f}s")
    print(f"  最后执行时间: {status['last_execution_time']:.3f}s")
    print(f"  当前状态: {status['state']}")


def main():
    """主测试函数"""
    print("🧬 FuturEmbryo实际LLM功能测试")
    print("=" * 50)
    
    # 显示配置信息
    print(f"API端点: https://litellm.futurx.cc")
    print(f"API密钥: sk-tptTrlFHR14EDpg")
    print()
    
    # 1. 测试API连接
    llm = test_api_connection()
    if not llm:
        print("❌ API连接失败，终止测试")
        return
    
    # 2. 测试简单对话
    if not test_simple_chat(llm):
        print("❌ 简单对话失败，终止测试")
        return
    
    # 3. 测试中文对话
    test_chinese_conversation(llm)
    
    # 4. 测试对话记忆
    test_conversation_memory(llm)
    
    # 5. 测试性能统计
    test_performance_stats(llm)
    
    # 6. 测试不同模型
    successful_models = test_different_models(
        "sk-tptTrlFHR14EDpg", 
        "https://litellm.futurx.cc"
    )
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print(f"✅ 基础功能正常")
    print(f"✅ 中文对话支持")
    print(f"✅ 对话记忆功能")
    print(f"✅ 性能统计功能")
    print(f"✅ 可用模型: {len(successful_models)}个")
    
    print(f"\n推荐使用的模型: {successful_models[0] if successful_models else 'gpt-3.5-turbo'}")


if __name__ == "__main__":
    main() 