#!/usr/bin/env python3
"""
FuturEmbryo Full Agent - 简洁版
==============================

展示FuturEmbryo框架的优雅组装理念
最少代码构建最强AI Agent
"""

import sys, yaml, asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from futurembryo.cells.llm_cell import LLMCell
from futurembryo.core.context_builder import IntelligentContextBuilder
from futurembryo.adapters.fastgpt_adapter import FastGPTAdapter

class Agent:
    """简洁优雅的FuturEmbryo Agent"""
    
    def __init__(self, config_path="config.yaml"):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        print(f"🌟 {self.config['agent']['name']}")
        print("=" * 50)
        
        # 组装核心组件
        self._setup_components()
        self._show_capabilities()
        
        # 对话历史
        self.conversation_history = []
        
        print("✅ Agent 初始化完成\n")
    
    def _setup_components(self):
        """组装Agent核心组件"""
        
        # 📖 知识库
        if self.config['knowledge_base']['enabled']:
            kb = self.config['knowledge_base']
            self.knowledge = FastGPTAdapter({
                "dataset_id": kb['id'],
                "base_url": kb['api_url'], 
                "api_key": kb['api_key']
            })
            print("📖 知识库已连接")
        
        # 🎯 智能上下文构建器
        self.context_builder = IntelligentContextBuilder(
            max_tokens=self.config['agent']['max_tokens'] * 0.7,
            conversation_history_limit=self.config.get('context', {}).get('history_limit', 15)
        )
        
        # 初始化组件配置
        context_config = {
            "mind_cell": {
                "model_name": self.config.get('mind', {}).get('model_name', 'gpt-4'),
                "api_key": self.config['api']['key'],
                "base_url": self.config['api']['base_url']
            } if self.config.get('mind', {}).get('enabled', False) else {},
            
            "memory_cell": {
                "embedding_model": self.config['memory']['embedding_model'],
                "collection_name": self.config['memory']['collection_name']
            } if self.config['memory']['enabled'] else {},
            
            "tool_cell": {
                "auto_load_defaults": self.config['tools']['defaults'],
                "mcp_servers": self.config['tools']['mcp_servers']
            }
        }
        
        self.context_builder.initialize_components(context_config)
        print("🎯 智能上下文已就绪")
        
        # 🧠 核心LLM
        self.llm = LLMCell(
            model_name=self.config['agent']['model'],
            config={
                "api_key": self.config['api']['key'],
                "base_url": self.config['api']['base_url'],
                "timeout": self.config['api']['timeout'],
                "temperature": self.config['agent']['temperature'],
                "max_tokens": self.config['agent']['max_tokens'],
                "system_prompt": self.config['agent']['system_prompt']
            },
            tool_cell=self.context_builder.tool_cell
        )
        print("🧠 LLM核心已激活")
        
        # 注册自定义工具
        if hasattr(self, 'knowledge'):
            self._register_knowledge_tool()
        self._register_memory_tool()
    
    def _register_knowledge_tool(self):
        """注册知识库查询工具"""
        def query_knowledge(query: str) -> dict:
            try:
                result = self.knowledge.query(query)
                return {"success": True, "answer": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        registry = self.context_builder.tool_cell.get_tool_registry()
        registry.register_function(
            name="query_knowledge",
            description="查询专业知识库，获取准确的专业信息",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "要查询的问题"}},
                "required": ["query"]
            },
            function=query_knowledge
        )
    
    def _register_memory_tool(self):
        """注册记忆查询工具"""
        def query_memory() -> dict:
            if not self.conversation_history:
                return {"history": "还没有对话历史", "count": 0}
            
            recent_history = []
            for item in self.conversation_history[-6:]:
                role = "您" if item["role"] == "user" else "我"
                recent_history.append(f"{role}: {item['content'][:100]}...")
            
            return {
                "history": "\n".join(recent_history),
                "count": len(self.conversation_history),
                "summary": f"我们总共对话了{len(self.conversation_history)//2}轮"
            }
        
        registry = self.context_builder.tool_cell.get_tool_registry()
        registry.register_function(
            name="query_memory",
            description="查询我们的对话历史记忆",
            parameters={"type": "object", "properties": {}, "required": []},
            function=query_memory
        )
    
    def _show_capabilities(self):
        """展示Agent能力"""
        capabilities = [
            "💬 智能对话 - 理解上下文，记忆历史",
            "🧠 记忆系统 - 记住所有对话历史",
            "📚 知识查询 - FastGPT专业知识库", 
            "🔧 工具调用 - MCP协议支持",
            "⚙️ 配置驱动 - config.yaml完全控制"
        ]
        
        print("\n🎯 Agent 能力:")
        for cap in capabilities:
            print(f"• {cap}")
    
    async def chat(self, user_input: str) -> str:
        """核心对话处理"""
        # 保存用户输入
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # 限制历史长度
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        # 构建智能上下文
        full_context = await self.context_builder.build_full_context(
            user_input=user_input,
            conversation_history=self.conversation_history,
            enable_thinking=self.config.get('mind', {}).get('enabled', False),
            enable_memory=self.config['memory']['enabled'],
            enable_tools=True,
            thinking_mode=self.config.get('mind', {}).get('thinking_mode', 'reflection'),
            mind_rule=self.config.get('mind', {}).get('mind_rule', ''),
            additional_context={
                "knowledge_base_enabled": self.config['knowledge_base']['enabled']
            }
        )
        
        # 构建增强系统提示
        thinking_guidance = self.context_builder.extract_thinking_guidance(full_context)
        enhanced_prompt = self.context_builder.build_enhanced_system_prompt(
            original_system_prompt=self.config['agent']['system_prompt'],
            thinking_guidance=thinking_guidance,
            mind_rule=self.config.get('mind', {}).get('mind_rule', '')
        )
        
        # 格式化上下文
        formatted_context = self.context_builder._format_context_for_llm(full_context)
        
        # LLM对话
        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": f"{formatted_context}\n\n用户当前输入：{user_input}"}
        ]
        
        try:
            response_result = await self.llm._handle_conversation_with_tools(
                messages,
                self.config['agent']['temperature'],
                self.config['agent']['max_tokens']
            )
            response = response_result.get("response", "抱歉，我无法生成回复。")
        except Exception as e:
            response = f"抱歉，我遇到了技术问题：{str(e)}"
        
        # 保存回复
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    async def run_interactive(self):
        """交互式运行"""
        print("🎤 开始对话！输入 'quit' 退出")
        print("💡 试试问我：'我们之前聊过什么？'、'告诉我最新的新闻'")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n👤 您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！")
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
    """主函数 - 展示框架的简洁性"""
    agent = Agent()
    await agent.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())