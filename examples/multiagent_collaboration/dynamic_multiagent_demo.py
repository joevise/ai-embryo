"""
FuturEmbryo 智能体协作系统

AI驱动的通用智能助手，支持动态智能体生成和协作
自动分析任务并创建专门的智能体团队来完成复杂工作
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径  
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dynamic_multiagent.log', encoding='utf-8')
    ]
)

from futurembryo import setup_futurx_api
from agents.coordinator_agent import CoordinatorAgent


class DynamicMultiAgentSystem:
    """智能体协作系统"""
    
    def __init__(self, user_id: str = "user"):
        """
        初始化智能体协作系统
        
        Args:
            user_id: 用户标识
        """
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        self.coordinator = None
        
    async def initialize(self):
        """初始化智能体协作系统"""
        try:
            self.logger.info("🚀 Initializing FuturEmbryo Agent Collaboration System...")
            
            # 创建协调器
            self.coordinator = CoordinatorAgent(self.user_id)
            await self.coordinator.initialize()
            
            self.logger.info("✅ Agent collaboration system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize system: {e}")
            raise
    
    async def run_interactive_session(self):
        """运行交互式对话会话"""
        print("\n" + "="*70)
        print("🤖 FuturEmbryo 智能体协作系统 - 开始对话")
        print("="*70)
        print("\n🎯 系统能力:")
        print("  • 智能任务分析和分解")
        print("  • 动态创建专业智能体团队") 
        print("  • 自动配置工具和协作流程")
        print("  • 多智能体协同完成复杂任务")
        print("\n📋 可用命令:")
        print("  • 'quit' - 退出系统")
        print("  • 'status' - 查看系统状态")
        print("  • 'reset' - 重置协调器")
        print("  • 'help' - 显示帮助信息")
        print("\n" + "-"*70)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n💬 您好！请告诉我您需要完成什么任务: ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() == 'quit':
                    print("\n👋 感谢使用 FuturEmbryo 智能体协作系统！")
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
                print(f"\n🔄 协调器正在分析任务...")
                response = await self.coordinator.process_message(user_input)
                
                print(f"\n🎯 协调器响应:")
                print("-" * 40)
                print(response)
                print("-" * 40)
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被用户中断，正在退出...")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in interactive session: {e}")
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
                
        except Exception as e:
            print(f"❌ 获取状态失败: {e}")
    
    async def _reset_system(self):
        """重置系统"""
        try:
            print("\n🔄 重置协调器...")
            await self.coordinator.reset()
            print("✅ 系统重置完成")
        except Exception as e:
            print(f"❌ 重置失败: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        print(f"\n📖 系统帮助:")
        print(f"  • 描述任务: 直接输入您需要完成的任务描述")
        print(f"  • 确认计划: 当协调器提出计划时，输入'确认'、'同意'或'ok'来执行")
        print(f"  • 修改计划: 如果需要修改，直接说明您的修改要求")
        print(f"  • 查看状态: 输入'status'查看当前系统状态")
        print(f"  • 重置系统: 输入'reset'重置协调器状态")
        print(f"  • 退出系统: 输入'quit'退出程序")
        print(f"\n💡 工作流程:")
        print(f"  1. 输入任务 → 2. 协调器分析并设计智能体 → 3. 确认计划 → 4. 执行任务")


async def main():
    """主函数"""
    try:
        # 设置API配置（使用fullagent的配置）
        print("🔧 配置FuturX API...")
        setup_futurx_api(
            api_key="sk-tptTrlFHR14EDpg",
            base_url="https://litellm.futurx.cc/v1"
        )
        
        # 创建系统实例
        system = DynamicMultiAgentSystem()
        await system.initialize()
        
        # 显示启动信息
        print("\n🎉 FuturEmbryo 智能体协作系统已启动！")
        print("\n这是一个AI驱动的通用智能助手系统，能够:")
        print("  • 自动分析任务复杂度和需求")
        print("  • 动态设计和创建专门的AI智能体")
        print("  • 智能配置工具和协作方式") 
        print("  • 实现多智能体协同完成复杂任务")
        
        # 直接启动交互模式
        await system.run_interactive_session()
            
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        logging.error(f"Main execution error: {e}")
    finally:
        print("\n🔚 程序结束")


if __name__ == "__main__":
    asyncio.run(main())