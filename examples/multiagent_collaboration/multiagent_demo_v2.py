#!/usr/bin/env python3
"""
FuturEmbryo多智能体协作系统演示 v2

基于升级后的动态智能体生成架构
展示AI驱动的任务分析、智能体设计和协作执行
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('multiagent_demo_v2.log', encoding='utf-8')
    ]
)

from futurembryo import setup_futurx_api
from agents.coordinator_agent import CoordinatorAgent


class MultiAgentCollaborationSystemV2:
    """多智能体协作系统 v2 - 基于新架构"""
    
    def __init__(self, user_id: str = "demo_user"):
        """
        初始化协作系统
        
        Args:
            user_id: 用户标识
        """
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        self.coordinator = None
        self.conversation_history = []
        
        print("🚀 启动 FuturEmbryo 多智能体协作系统 v2")
        print("=" * 60)
        
        # 设置API
        self._setup_api()
        
        print("✅ 系统初始化完成！")
        self._show_system_capabilities()
    
    def _setup_api(self):
        """设置API配置"""
        print("🔧 配置FuturX API...")
        setup_futurx_api(
            api_key="sk-tptTrlFHR14EDpg",
            base_url="https://litellm.futurx.cc/v1"
        )
        print("🔗 API配置完成")
    
    async def initialize(self):
        """异步初始化系统"""
        try:
            print("🔄 初始化智能协调器...")
            
            # 创建协调器
            self.coordinator = CoordinatorAgent(self.user_id)
            await self.coordinator.initialize()
            
            print("✅ 智能协调器初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 系统初始化失败: {e}")
            raise
    
    def _show_system_capabilities(self):
        """显示系统能力"""
        print("\n🎯 系统核心能力:")
        print("• 🧠 AI驱动任务分析 - 自动理解任务需求和复杂度")
        print("• 🏭 动态智能体生成 - 根据任务需求设计专门的AI智能体")
        print("• 🔧 智能工具配置 - 自动为智能体配置合适的工具和能力")
        print("• 🔄 三阶段工作流 - 分析设计 → 确认 → 执行")
        print("• 📊 结果整合 - 多智能体协作输出完整结果")
        
        print("\n🔄 三阶段工作流程:")
        print("1️⃣ **分析设计阶段** - AI分析任务并设计智能体团队")
        print("2️⃣ **确认阶段** - 用户确认或修改执行计划")  
        print("3️⃣ **执行阶段** - 动态创建智能体并协作完成任务")
        
        print("\n💡 使用方式:")
        print("• 直接描述您需要完成的任务")
        print("• 系统会自动分析并设计专门的智能体团队")
        print("• 确认计划后开始执行")
        
        print("\n🌟 示例任务:")
        print("• '帮我分析人工智能在教育领域的应用现状和发展趋势'")
        print("• '我需要制定一个完整的产品营销策略'")
        print("• '分析这个行业的竞争格局并给出建议'")
        print("• '帮我写一份技术调研报告'")
        
        print("\n📝 特殊命令:")
        print("• 'quit' - 退出系统")
        print("• 'status' - 查看系统状态")
        print("• 'reset' - 重置协调器")
        print("• 'help' - 显示帮助信息")
    
    async def process_user_input(self, user_input: str) -> str:
        """处理用户输入"""
        try:
            self.logger.info(f"📥 Processing user input: {user_input}")
            
            # 通过协调器处理
            response = await self.coordinator.process_message(user_input)
            
            # 更新对话历史
            self.conversation_history.append({
                "role": "user", 
                "content": user_input,
                "timestamp": self._get_timestamp()
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response,
                "timestamp": self._get_timestamp()
            })
            
            return response
            
        except Exception as e:
            error_msg = f"处理请求时出现错误: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return error_msg
    
    async def run_interactive_demo(self):
        """运行交互式演示"""
        print("\n" + "="*70)
        print("🤖 FuturEmbryo 智能体协作系统 v2 - 开始对话")
        print("="*70)
        print("\n🚀 系统已就绪，请开始描述您的任务需求")
        print("💡 系统将自动分析并设计专门的智能体团队来帮您完成任务")
        print("\n" + "-"*70)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n💬 您好！请告诉我您需要完成什么任务: ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() == 'quit':
                    print("\n👋 感谢使用 FuturEmbryo 智能体协作系统 v2！")
                    break
                elif user_input.lower() == 'status':
                    await self._show_status()
                    continue
                elif user_input.lower() == 'reset':
                    await self._reset_system()
                    continue
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                # 处理任务请求
                print(f"\n🔄 智能协调器正在分析任务...")
                response = await self.process_user_input(user_input)
                
                print(f"\n🎯 智能协调器响应:")
                print("-" * 50)
                print(response)
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断，正在退出...")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in interactive demo: {e}")
                print(f"\n❌ 处理过程中出现错误: {e}")
    
    async def _show_status(self):
        """显示系统状态"""
        try:
            status = self.coordinator.get_status()
            print(f"\n📊 系统状态:")
            print(f"  • 当前阶段: {status.get('current_phase', 'unknown')}")
            print(f"  • 等待确认: {'是' if status.get('is_waiting_confirmation') else '否'}")
            print(f"  • 有待执行计划: {'是' if status.get('has_pending_plan') else '否'}")
            print(f"  • 已创建智能体数量: {status.get('created_agents_count', 0)}")
            
            if status.get('created_agents'):
                print(f"  • 已创建智能体: {', '.join(status['created_agents'])}")
            
            print(f"\n💬 对话统计:")
            print(f"  • 历史轮数: {len(self.conversation_history) // 2}")
                
        except Exception as e:
            print(f"❌ 获取状态失败: {e}")
    
    async def _reset_system(self):
        """重置系统"""
        try:
            print("\n🔄 重置智能协调器...")
            await self.coordinator.reset()
            self.conversation_history.clear()
            print("✅ 系统重置完成")
        except Exception as e:
            print(f"❌ 重置失败: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        print(f"\n📖 系统帮助:")
        print(f"\n🎯 工作流程:")
        print(f"  1. 描述任务 → 系统AI分析任务需求")
        print(f"  2. 设计智能体 → 自动设计专门的智能体团队")
        print(f"  3. 确认计划 → 您确认或修改执行计划")
        print(f"  4. 执行任务 → 动态创建智能体并协作完成")
        
        print(f"\n💡 使用技巧:")
        print(f"  • 清晰描述需求: '我需要...'、'帮我...'")
        print(f"  • 确认计划: 输入'确认'、'同意'或'ok'来执行")
        print(f"  • 修改计划: 直接说明您的修改要求")
        print(f"  • 查看状态: 输入'status'查看当前系统状态")
        
        print(f"\n🔧 系统命令:")
        print(f"  • help - 显示此帮助")
        print(f"  • status - 显示系统状态")
        print(f"  • reset - 重置协调器状态")
        print(f"  • quit - 退出系统")
        
        print(f"\n🌟 示例对话:")
        print(f"  用户: '帮我分析区块链技术的发展趋势'")
        print(f"  系统: [分析任务并设计智能体团队] → 等待确认")
        print(f"  用户: '确认'")
        print(f"  系统: [创建智能体] → [执行分析] → [输出完整报告]")
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def run_preset_examples(self):
        """运行预设示例"""
        examples = [
            {
                "title": "AI技术调研",
                "description": "分析人工智能在医疗健康领域的应用现状和发展前景，包括技术案例、市场分析和未来趋势预测。"
            },
            {
                "title": "产品营销策略",
                "description": "为一个新的智能家居产品制定完整的市场营销策略，包括目标客户分析、竞争对手分析、营销渠道规划和预算分配。"
            },
            {
                "title": "行业分析报告",
                "description": "深入分析新能源汽车行业的发展现状、主要玩家、技术趋势、政策影响和投资机会。"
            }
        ]
        
        print("\n📋 预设示例任务:")
        for i, example in enumerate(examples, 1):
            print(f"\n{i}. {example['title']}")
            print(f"   描述: {example['description']}")
        
        while True:
            try:
                choice = input(f"\n请选择示例 (1-{len(examples)}) 或输入 'back' 返回: ").strip()
                
                if choice.lower() == 'back':
                    break
                
                if choice.isdigit() and 1 <= int(choice) <= len(examples):
                    selected = examples[int(choice) - 1]
                    print(f"\n🚀 运行示例: {selected['title']}")
                    print(f"📝 任务描述: {selected['description']}")
                    print("-" * 50)
                    
                    response = await self.process_user_input(selected['description'])
                    print(f"\n🎯 系统响应:")
                    print("-" * 50)
                    print(response)
                    print("-" * 50)
                    
                    input("\n按回车键继续...")
                    break
                else:
                    print("❌ 无效选择，请重试")
                    
            except (ValueError, KeyboardInterrupt):
                break


async def main():
    """主函数"""
    print("🌟 FuturEmbryo 多智能体协作系统 v2")
    print("基于AI驱动的动态智能体生成架构")
    print()
    
    try:
        # 创建系统实例
        system = MultiAgentCollaborationSystemV2()
        await system.initialize()
        
        # 检查命令行参数
        if len(sys.argv) > 1 and sys.argv[1] == "--examples":
            await system.run_preset_examples()
        else:
            # 运行交互式演示
            await system.run_interactive_demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        logging.error(f"Main execution error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 程序结束")


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())