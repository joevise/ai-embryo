#!/usr/bin/env python3
"""
FuturEmbryo Full Agent - 简洁版
================================

展示FuturEmbryo框架的"简单组装"设计理念
用最少的代码构建最强大的AI Agent
"""

import sys
import yaml
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from futurembryo.cells.llm_cell import LLMCell
from futurembryo.cells.state_memory_cell import StateMemoryCell
from futurembryo.cells.mind_cell import MindCell
from futurembryo.cells.tool_cell import ToolCell
from futurembryo.core.context_builder import IntelligentContextBuilder
from futurembryo.adapters.fastgpt_adapter import FastGPTAdapter

class SimpleAgent:
    """简洁版FuturEmbryo Agent - 体现框架的简单组装理念"""
    
    def __init__(self, config_path="config.yaml"):
        """一键从配置文件构建完整Agent"""
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"🌟 {config['agent']['name']}")
        print("=" * 50)
        
        # 组装核心组件 - 体现生物启发的模块化设计
        self._assemble_components(config)
        
        print("✅ Agent 组装完成")
        self._show_capabilities()
    
    def _assemble_components(self, config):
        """组装Agent核心组件 - 像细胞组装成生物体"""
        
        # 🧠 思维细胞 (可选)
        self.mind = None
        if config['mind']['enabled']:
            self.mind = MindCell(
                model_name=config['mind']['model_name'],
                thinking_mode=config['mind']['thinking_mode'],
                character=config['mind']['character'],
                max_thinking_tokens=config['mind']['max_thinking_tokens'],
                mind_rule=config['mind']['mind_rule']
            )
            print("🧠 思维细胞已激活")
        
        # 📚 记忆细胞
        self.memory = StateMemoryCell(config={
            'collection_name': config['memory']['collection_name'],
            'embedding_model': config['memory']['embedding_model']
        })
        print("📚 记忆细胞已激活")
        
        # 🔧 工具细胞
        self.tools = ToolCell()
        print("🔧 工具细胞已激活")
        
        # 📖 知识库适配器
        if config['knowledge_base']['enabled']:
            kb_config = config['knowledge_base']
            self.knowledge = FastGPTAdapter({
                "dataset_id": kb_config['id'],
                "base_url": kb_config['api_url'],
                "api_key": kb_config['api_key']
            })
            print("📖 知识库已连接")
        
        # 🧠 核心对话细胞
        self.llm = LLMCell(
            model_name=config['agent']['model'],
            config={
                'temperature': config['agent']['temperature'],
                'max_tokens': config['agent']['max_tokens'],
                'system_prompt': config['agent']['system_prompt'],
                'api_key': config['api']['key'],
                'base_url': config['api']['base_url'],
                'timeout': config['api']['timeout']
            },
            tool_cell=self.tools
        )
        print("🧠 对话细胞已激活")
        
        # 🎯 上下文构建器
        self.context_builder = IntelligentContextBuilder(
            memory_cell=self.memory,
            knowledge_adapter=self.knowledge if config['knowledge_base']['enabled'] else None,
            tool_cell=self.tools,
            context_config=config['context']
        )
        print("🎯 上下文构建器已就绪")
    
    def _show_capabilities(self):
        """展示Agent能力"""
        print(f"\n🎯 Agent 能力:")
        capabilities = [
            "💬 智能对话 - 理解上下文，记忆历史",
            "🧠 记忆系统 - 记住所有对话历史", 
            "📚 知识查询 - FastGPT专业知识库",
            "🔧 工具调用 - Context7技术文档查询",
            "⚙️  配置驱动 - config.yaml完全控制",
        ]
        
        if self.mind:
            capabilities.append("🧠 智能上下文 - IntelligentContextBuilder统一管理")
        
        for cap in capabilities:
            print(f"• {cap}")
    
    async def chat(self, message: str) -> str:
        """对话处理 - 展示框架的优雅组合"""
        
        # 1. 思维阶段 (可选)
        if self.mind:
            print("🤖 思考中...")
            await self.mind.think(message)
        
        # 2. 构建智能上下文
        context = await self.context_builder.build_full_context(
            current_message=message,
            conversation_history=await self._get_recent_history()
        )
        
        # 3. LLM处理 + 自动工具调用
        response = await self.llm.process_with_context(message, context)
        
        # 4. 保存记忆
        await self.memory.save_memory("user", message)
        await self.memory.save_memory("assistant", response)
        
        return response
    
    async def _get_recent_history(self):
        """获取最近对话历史"""
        try:
            memories = await self.memory.retrieve_memories("conversation", limit=10)
            return [{"role": mem.get("role", "user"), "content": mem.get("content", "")} for mem in memories]
        except:
            return []
    
    async def run_interactive(self):
        """交互式运行"""
        print(f"\n{'='*60}")
        print("🎤 开始对话！输入 'quit' 退出")
        print("💡 试试问我：'我们之前聊过什么？'、'查询Python最佳实践'")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n👤 您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！")
                    break
                
                if not user_input:
                    continue
                
                response = await self.chat(user_input)
                print(f"🤖 {self.llm.model.split('/')[-1]}: {response}")
                
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")

async def main():
    """主函数 - 展示框架的简洁性"""
    agent = SimpleAgent()
    await agent.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())