#!/usr/bin/env python3
"""
FuturEmbryo第二阶段功能测试

测试StateMemoryCell、Pipeline和ToolCell的功能
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from futurembryo import (
    StateMemoryCell, MemoryEntry, ToolCell, Tool,
    Pipeline, PipelineStep, PipelineBuilder,
    LLMCell, setup_futurx_api, Cell
)


def test_state_memory_cell():
    """测试StateMemoryCell功能"""
    print("=== 测试StateMemoryCell ===")
    
    # 创建StateMemoryCell
    memory = StateMemoryCell({
        "max_short_term": 5,
        "max_working": 3,
        "max_long_term": 10
    })
    
    print(f"✅ StateMemoryCell创建成功")
    
    # 测试存储记忆
    memory_id1 = memory.store("这是第一条记忆", "working", 0.8, ["测试", "重要"])
    memory_id2 = memory.store("这是第二条记忆", "short_term", 0.5, ["测试"])
    memory_id3 = memory.store("这是长期记忆", "long_term", 0.9, ["知识", "重要"])
    
    print(f"✅ 存储了3条记忆: {memory_id1[:8]}..., {memory_id2[:8]}..., {memory_id3[:8]}...")
    
    # 测试检索记忆
    memories = memory.retrieve("记忆", limit=5)
    print(f"✅ 检索到{len(memories)}条记忆")
    
    # 测试会话状态
    memory.set_state("user_name", "张三")
    memory.set_state("conversation_count", 1)
    
    user_name = memory.get_state_value("user_name")
    print(f"✅ 会话状态测试成功，用户名: {user_name}")
    
    # 测试状态获取
    state = memory({"action": "get_state", "include_memories": True})
    print(f"✅ 状态获取成功，记忆统计: {state['data']['memory_counts']}")
    
    return memory


def test_tool_cell():
    """测试ToolCell功能"""
    print("\n=== 测试ToolCell ===")
    
    # 创建ToolCell
    tool_cell = ToolCell({
        "allow_http": True,
        "allow_shell": False,  # 安全起见，不允许shell
        "timeout": 10
    })
    
    print(f"✅ ToolCell创建成功，内置工具数量: {len(tool_cell.tools)}")
    
    # 测试内置工具
    result1 = tool_cell.call_tool("string_length", text="Hello World")
    print(f"✅ 字符串长度工具测试: 'Hello World' 长度为 {result1}")
    
    result2 = tool_cell.call_tool("math_add", a=10, b=20)
    print(f"✅ 数学加法工具测试: 10 + 20 = {result2}")
    
    result3 = tool_cell.call_tool("json_stringify", data={"name": "测试", "value": 123})
    print(f"✅ JSON序列化工具测试成功")
    
    # 注册自定义工具
    def custom_greeting(name, language="zh"):
        greetings = {
            "zh": f"你好，{name}！",
            "en": f"Hello, {name}!",
            "ja": f"こんにちは、{name}さん！"
        }
        return greetings.get(language, f"Hi, {name}!")
    
    tool_cell.register_tool(
        "greeting",
        custom_greeting,
        "多语言问候工具",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "language": {"type": "string", "enum": ["zh", "en", "ja"]}
            }
        }
    )
    
    result4 = tool_cell.call_tool("greeting", name="小明", language="zh")
    print(f"✅ 自定义工具测试: {result4}")
    
    # 列出所有工具
    tools = tool_cell.list_tools()
    print(f"✅ 工具列表获取成功，总计{len(tools)}个工具")
    
    return tool_cell


def test_pipeline():
    """测试Pipeline功能"""
    print("\n=== 测试Pipeline ===")
    
    # 创建简单的测试Cell
    class NumberCell(Cell):
        def __init__(self, operation, value):
            super().__init__()
            self.operation = operation
            self.value = value
        
        def process(self, context):
            input_value = context.get("number", 0)
            if self.operation == "add":
                result = input_value + self.value
            elif self.operation == "multiply":
                result = input_value * self.value
            else:
                result = input_value
            
            return {"number": result, "operation": f"{self.operation} {self.value}"}
    
    # 创建Pipeline - 顺序执行
    pipeline = Pipeline([
        NumberCell("add", 10),
        NumberCell("multiply", 2),
        NumberCell("add", 5)
    ], {"execution_mode": "sequential"})
    
    print(f"✅ 顺序Pipeline创建成功，包含{len(pipeline.steps)}个步骤")
    
    # 执行Pipeline
    result = pipeline({"number": 5})
    print(f"✅ 顺序执行结果: 5 -> {result['data']['final_context']['number']}")
    print(f"   执行了{result['data']['steps_executed']}个步骤")
    
    # 测试并行Pipeline
    parallel_pipeline = Pipeline([
        NumberCell("add", 1),
        NumberCell("add", 2), 
        NumberCell("add", 3)
    ], {"execution_mode": "parallel", "max_workers": 2})
    
    result2 = parallel_pipeline({"number": 10})
    print(f"✅ 并行执行成功，执行了{result2['data']['steps_executed']}个步骤")
    
    # 测试条件Pipeline
    def condition_func(context):
        return context.get("number", 0) > 0
    
    conditional_pipeline = Pipeline(config={"execution_mode": "conditional"})
    conditional_pipeline.add_step(NumberCell("add", 5), condition=condition_func)
    conditional_pipeline.add_step(NumberCell("multiply", 2), condition=lambda ctx: ctx.get("number", 0) < 20)
    
    result3 = conditional_pipeline({"number": 3})
    print(f"✅ 条件执行成功，最终结果: {result3['data']['final_context']['number']}")
    
    return pipeline


def test_pipeline_builder():
    """测试PipelineBuilder"""
    print("\n=== 测试PipelineBuilder ===")
    
    # 使用Builder模式创建Pipeline
    class TextCell(Cell):
        def __init__(self, operation):
            super().__init__()
            self.operation = operation
        
        def process(self, context):
            text = context.get("text", "")
            if self.operation == "upper":
                result = text.upper()
            elif self.operation == "reverse":
                result = text[::-1]
            elif self.operation == "length":
                result = f"{text} (长度: {len(text)})"
            else:
                result = text
            
            return {"text": result}
    
    # 使用Builder创建Pipeline
    pipeline = (PipelineBuilder()
                .add(TextCell("upper"), "转大写")
                .add(TextCell("reverse"), "反转")
                .add(TextCell("length"), "计算长度")
                .sequential()
                .build())
    
    result = pipeline({"text": "hello"})
    final_text = result["data"]["final_context"]["text"]
    print(f"✅ Builder模式Pipeline执行成功: 'hello' -> '{final_text}'")
    
    return pipeline


def test_integration():
    """测试组件集成"""
    print("\n=== 测试组件集成 ===")
    
    # 配置API
    setup_futurx_api(
        api_key="sk-tptTrlFHR14EDpg",
        base_url="https://litellm.futurx.cc"
    )
    
    # 创建组件
    memory = StateMemoryCell()
    tool_cell = ToolCell()
    llm = LLMCell("gpt-3.5-turbo", {
        "temperature": 0.7,
        "max_tokens": 100,
        "system_prompt": "你是一个智能助手，可以使用记忆和工具。"
    })
    
    # 创建集成Pipeline
    class MemoryLLMCell(Cell):
        def __init__(self, llm_cell, memory_cell):
            super().__init__()
            self.llm = llm_cell
            self.memory = memory_cell
        
        def process(self, context):
            user_input = context.get("input", "")
            
            # 检索相关记忆
            memories = self.memory.retrieve(user_input, limit=3)
            memory_context = "\n".join([m["content"] for m in memories])
            
            # 构建LLM输入
            llm_input = f"用户输入: {user_input}\n相关记忆: {memory_context}"
            
            # 调用LLM
            llm_result = self.llm({"input": llm_input})
            
            if llm_result["success"]:
                response = llm_result["data"]["response"]
                
                # 存储新记忆
                self.memory.store(f"用户: {user_input}", "short_term", 0.6)
                self.memory.store(f"助手: {response}", "short_term", 0.6)
                
                return {"response": response, "memories_used": len(memories)}
            else:
                return {"response": "抱歉，我无法处理您的请求。", "memories_used": 0}
    
    # 创建集成Cell
    integrated_cell = MemoryLLMCell(llm, memory)
    
    # 测试对话
    result1 = integrated_cell({"input": "我叫张三，今年25岁"})
    print(f"✅ 第一轮对话: {result1['data']['response'][:50]}...")
    
    result2 = integrated_cell({"input": "我叫什么名字？"})
    print(f"✅ 第二轮对话: {result2['data']['response'][:50]}...")
    print(f"   使用了{result2['data']['memories_used']}条记忆")
    
    return integrated_cell


def main():
    """主测试函数"""
    print("🧪 FuturEmbryo第二阶段功能测试开始\n")
    
    try:
        # 测试各个组件
        memory = test_state_memory_cell()
        tool_cell = test_tool_cell()
        pipeline = test_pipeline()
        builder_pipeline = test_pipeline_builder()
        integrated = test_integration()
        
        print("\n🎉 所有测试通过！")
        print("\n📊 测试总结:")
        print("✅ StateMemoryCell - 记忆管理功能正常")
        print("✅ ToolCell - 工具调用功能正常")
        print("✅ Pipeline - 流水线组合功能正常")
        print("✅ PipelineBuilder - 构建器模式正常")
        print("✅ 组件集成 - 多组件协作正常")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 