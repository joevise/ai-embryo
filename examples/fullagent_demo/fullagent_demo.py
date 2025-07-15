#!/usr/bin/env python3
"""
FuturEmbryo Full Agent Demo
==========================

完整功能展示：对话记忆 + 知识库查询 + MCP工具调用

功能特性：
- 持久化记忆：记住所有对话历史
- FastGPT知识库：专业知识查询
- MCP工具：Context7技术文档查询
- 配置驱动：通过config.yaml配置所有功能
"""

import sys
import yaml
import asyncio
import json
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from futurembryo.cells.llm_cell import LLMCell
from futurembryo.cells.state_memory_cell import StateMemoryCell
from futurembryo.cells.mind_cell import MindCell
from futurembryo.cells.tool_cell import ToolCell
from futurembryo.core.context_builder import IntelligentContextBuilder
from futurembryo.adapters.fastgpt_adapter import FastGPTAdapter

class FullAgent:
    """FuturEmbryo框架完整功能演示Agent"""
    
    def __init__(self, config_path="config.yaml"):
        """从配置文件初始化Agent"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        print(f"🚀 启动 {self.config['agent']['name']}")
        
        # 0. 初始化logger
        self.logger = logging.getLogger(__name__)
        
        # 1. 初始化对话历史
        self.conversation_history = []
        
        # 2. 初始化知识库
        if self.config['knowledge_base']['enabled']:
            kb_config = self.config['knowledge_base']
            self.knowledge = FastGPTAdapter({
                "dataset_id": kb_config['id'],
                "base_url": kb_config['api_url'],
                "api_key": kb_config['api_key']
            })
            print("📚 FastGPT知识库已连接")
        
        # 3. 先创建ToolCell，包含MCP服务器配置
        tool_cell_config = {
            "auto_load_defaults": self.config['tools']['defaults'],
            "mcp_servers": self.config['tools']['mcp_servers']
        }
        self.tool_cell = ToolCell(config=tool_cell_config)
        
        # 4. 初始化上下文构建器（统一管理所有组件）
        self.context_builder = IntelligentContextBuilder(
            user_id=f"user_{self.config['agent']['name']}",
            enable_memory=self.config['memory']['enabled'],
            memory_collection=self.config['memory']['collection_name'],
            tool_cell=self.tool_cell,  # 传递已配置的ToolCell
            enable_user_profile=False,  # 暂时禁用用户画像功能
            enable_mentions=False       # 暂时禁用@引用功能
        )
        
        # 5. 保存mind_rule用于上下文构建
        self.mind_rule = self.config.get('mind', {}).get('mind_rule', '')
        self.default_thinking_mode = self.config.get('mind', {}).get('thinking_mode', 'reflection')
        
        # 6. 创建独立的LLM Cell
        llm_config = {
            "api_key": self.config['api']['key'],
            "base_url": self.config['api']['base_url'],
            "timeout": self.config['api']['timeout'],
            "temperature": self.config['agent']['temperature'],
            "max_tokens": self.config['agent']['max_tokens'],
            "system_prompt": self.config['agent']['system_prompt']
        }
        
        self.llm = LLMCell(
            model_name=self.config['agent']['model'],
            config=llm_config,
            tool_cell=self.tool_cell
        )
        
        # 7. 注册自定义工具到ToolCell
        if hasattr(self, 'knowledge'):
            self._register_knowledge_tool()
        self._register_memory_tool()
        
        print("✅ Full Agent 初始化完成")
        self._show_capabilities()
    
    def _register_knowledge_tool(self):
        """注册知识库查询工具"""
        def query_knowledge(query: str) -> dict:
            """查询专业知识库"""
            try:
                print(f"🔍 正在查询知识库: {query}")
                result = self.knowledge.query(query)
                print(f"✅ 知识库查询成功: {len(str(result))} 字符")
                return {"success": True, "answer": result}
            except Exception as e:
                print(f"❌ 知识库查询失败: {e}")
                return {"success": False, "error": str(e)}
        
        registry = self.tool_cell.get_tool_registry()
        registry.register_function(
            name="query_knowledge",
            description="查询专业知识库，获取准确的专业信息",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "要查询的问题"}
                },
                "required": ["query"]
            },
            function=query_knowledge
        )
    
    def _register_memory_tool(self):
        """注册记忆查询工具"""
        def query_memory() -> dict:
            """查询对话历史记忆"""
            if not self.conversation_history:
                return {"history": "还没有对话历史", "count": 0}
            
            # 返回最近的对话历史
            recent_history = []
            for item in self.conversation_history[-6:]:  # 最近3轮对话
                role = "您" if item["role"] == "user" else "我"
                recent_history.append(f"{role}: {item['content'][:100]}...")
            
            return {
                "history": "\n".join(recent_history),
                "count": len(self.conversation_history),
                "summary": f"我们总共对话了{len(self.conversation_history)//2}轮"
            }
        
        registry = self.tool_cell.get_tool_registry()
        registry.register_function(
            name="query_memory",
            description="查询我们的对话历史记忆",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            function=query_memory
        )
    
    def _show_capabilities(self):
        """显示Agent能力"""
        print("\n🎯 Agent 能力:")
        print("• 💬 智能对话 - 理解上下文，记忆历史")
        print("• 🧠 记忆系统 - 记住所有对话历史") 
        print("• 📚 知识查询 - FastGPT专业知识库")
        print("• 🔧 工具调用 - Context7技术文档查询")
        print("• ⚙️  配置驱动 - config.yaml完全控制")
        print("• 🧠 智能上下文 - IntelligentContextBuilder统一管理")
        if self.config.get('mind', {}).get('enabled', False):
            character = self.config.get('mind', {}).get('character', '默认')
            print(f"• 🌸 {character}思维 - 诗意细腻的思考方式")
    
    async def chat(self, user_input: str) -> str:
        """智能对话，使用IntelligentContextBuilder统一管理所有功能"""
        # 1. 保存用户输入到记忆
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # 2. 构建上下文（限制历史长度）
        if len(self.conversation_history) > 50:  # 保留最近10轮对话
            self.conversation_history = self.conversation_history[-50:]
        
        # 3. 使用ContextBuilder构建完整上下文
        mind_enabled = self.config.get('mind', {}).get('enabled', False)
        additional_context = {
            "knowledge_base_enabled": self.config['knowledge_base']['enabled'],
            "mind_enabled": mind_enabled
        }
        
        # 只有当mind启用时才传递相关配置
        if mind_enabled:
            additional_context.update({
                "mind_rule": self.mind_rule,
                "thinking_mode": self.default_thinking_mode
            })
        
        full_context = await self.context_builder.build_context(
            user_input=user_input,
            conversation_history=self.conversation_history,
            additional_context=additional_context
        )
        
        # 4. 格式化上下文为LLM可理解的格式
        formatted_context = self.context_builder.format_context_for_llm(full_context)
        
        # 5. 构建系统提示
        system_prompt = self.config['agent']['system_prompt']
        # 只有当mind启用时才添加思考指导
        if mind_enabled and self.mind_rule:
            system_prompt += f"\n\n思考指导：{self.mind_rule}"
        
        # 6. 使用LLM进行对话（使用完整上下文）
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{formatted_context}\n\n用户当前输入：{user_input}"}
        ]
        
        # 7. 使用LLM进行对话处理
        try:
            # 直接使用LLMCell的异步方法，确保整个调用链在同一task中
            response_result = await self.llm._handle_conversation_with_tools(
                messages,
                self.config['agent']['temperature'],
                self.config['agent']['max_tokens']
            )
            
            response = response_result.get("response", "抱歉，我无法生成回复。")
                
        except Exception as e:
            self.llm.logger.error(f"纯异步链处理失败: {e}")
            response = f"抱歉，我遇到了技术问题：{str(e)}"
        
        # 8. 保存交互到上下文构建器的记忆中
        try:
            await self.context_builder.save_interaction(user_input, response)
        except Exception as e:
            self.logger.error(f"保存交互记忆失败: {e}")
        
        # 9. 保存回复到记忆
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def _format_conversation_history(self) -> str:
        """格式化对话历史为字符串"""
        if not self.conversation_history:
            return ""
        
        formatted = []
        for item in self.conversation_history[-4:]:  # 只取最近2轮
            role = "用户" if item["role"] == "user" else "我"
            formatted.append(f"{role}: {item['content']}")
        
        return "\n".join(formatted)
    
    async def run_interactive(self):
        """运行交互式对话"""
        print("\n" + "="*60)
        print("🎤 开始对话！输入 'quit' 退出")
        print("💡 试试问我：'我们之前聊过什么？'、'查询Python最佳实践'")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n👤 您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！感谢使用FuturEmbryo！")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 思考中...")
                response = await self.chat(user_input)
                print(f"🤖 Agent: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

async def main():
    """主函数"""
    print("🌟 FuturEmbryo Full Agent Demo")
    print("=" * 50)
    
    try:
        # 创建Agent
        agent = FullAgent()
        
        # 运行交互式对话
        await agent.run_interactive()
        
    except FileNotFoundError:
        print("❌ 未找到config.yaml配置文件")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())