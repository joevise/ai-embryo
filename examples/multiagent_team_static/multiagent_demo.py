#!/usr/bin/env python3
"""
FuturEmbryo多智能体协作系统演示

基于FuturEmbryo核心框架的用户中心@机制驱动多智能体协作演示
展示用户记忆学习、@引用处理、个性化响应等核心功能
"""

import sys
import yaml
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入FuturEmbryo核心组件
from futurembryo import setup_futurx_api

# 导入我们的扩展组件
sys.path.insert(0, str(Path(__file__).parent))
from agents.user_aware_agent import UserAwareAgent
from agents.coordinator_agent import CoordinatorAgent
from cells.user_memory_cell import UserMemoryCell
from cells.mention_processor_cell import MentionProcessorCell


class MultiAgentCollaborationDemo:
    """多智能体协作系统演示"""
    
    def __init__(self, config_path="configs/demo_config.yaml"):
        """初始化演示系统"""
        print("🚀 启动FuturEmbryo多智能体协作系统")
        print("=" * 60)
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 设置API
        self._setup_api()
        
        # 初始化核心组件
        self._init_core_components()
        
        # 创建专业Agent实例
        self._create_agents()
        
        # 创建智能协调员
        self._create_coordinator()
        
        # 系统状态
        self.conversation_history = []
        self.session_deliverables = []
        
        print("✅ 系统初始化完成！")
        self._show_system_capabilities()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"📋 配置加载成功: {config_path}")
            return config
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            raise
    
    def _setup_api(self):
        """设置API配置"""
        api_config = self.config.get("api", {})
        setup_futurx_api(
            api_key=api_config.get("key"),
            base_url=api_config.get("base_url")
        )
        print("🔗 API配置完成")
    
    def _init_core_components(self):
        """初始化核心组件"""
        # 1. 用户记忆系统
        user_memory_config = self.config.get("user_memory", {})
        self.user_memory = UserMemoryCell(user_memory_config)
        print("🧠 用户记忆系统已启动")
        
        # 2. @引用处理系统
        mention_config = self.config.get("mention_system", {})
        self.mention_processor = MentionProcessorCell(mention_config)
        print("📝 @引用处理系统已启动")
        
        # 3. 加载Agent模板
        self.agent_templates = self._load_agent_templates()
        print(f"📚 Agent模板加载完成: {len(self.agent_templates)} 个模板")
    
    def _load_agent_templates(self) -> dict:
        """加载Agent模板"""
        try:
            with open("templates/agent_templates.yaml", 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Agent模板加载失败，使用默认配置: {e}")
            return {}
    
    def _create_agents(self):
        """创建Agent实例"""
        self.agents = {}
        agents_config = self.config.get("agents", {})
        
        for agent_id, agent_config in agents_config.items():
            try:
                # 获取模板配置
                template_name = agent_config.get("template")
                template_config = self.agent_templates.get(template_name, {})
                
                # 合并配置（自定义配置覆盖模板配置）
                final_config = {**template_config, **agent_config.get("customizations", {})}
                
                # 添加共享组件
                final_config["user_memory_config"] = self.config.get("user_memory", {})
                final_config["mention_processor_config"] = self.config.get("mention_system", {})
                
                # 创建Agent
                agent = UserAwareAgent(agent_id, final_config)
                self.agents[agent_id] = agent
                
                print(f"🤖 Agent '{agent_id}' 创建成功")
                
            except Exception as e:
                print(f"❌ Agent '{agent_id}' 创建失败: {e}")
        
        print(f"🎯 共创建 {len(self.agents)} 个专业智能体")
    
    def _create_coordinator(self):
        """创建智能协调员"""
        try:
            coordinator_config = {
                "user_memory": self.config.get("user_memory", {}),
                "mention_system": self.config.get("mention_system", {})
            }
            
            self.coordinator = CoordinatorAgent(
                available_agents=self.agents,
                config=coordinator_config
            )
            
            print("🧠 智能协调员创建成功")
            
        except Exception as e:
            print(f"❌ 智能协调员创建失败: {e}")
            self.coordinator = None
    
    def _show_system_capabilities(self):
        """显示系统能力"""
        print("\\n🎯 系统核心能力:")
        print("• 🧠 智能协调员 - 自动分析任务并分配给合适的专业Agent")
        print("• 📋 任务分解 - 将复杂任务智能拆分成可执行的子任务")
        print("• 🎯 智能路由 - 根据任务类型自动选择最适合的专业Agent")
        print("• 🔄 流程协调 - 管理多Agent协作的执行顺序和依赖关系")
        print("• 📊 结果整合 - 汇总各专业Agent的输出形成完整答案")
        print("• 🧠 用户记忆学习 - 自动学习用户偏好和兴趣")
        print("• 📝 @引用机制 - 统一的对象引用系统")
        
        print("\\n🤖 智能协调员管理的专业智能体:")
        for agent_id, agent in self.agents.items():
            info = agent.get_agent_info()
            print(f"• @{agent_id} - {info['name']}: {info['description']}")
        
        print("\\n💡 使用方式:")
        print("• 直接告诉我你需要什么，智能协调员会自动分析并安排合适的专业Agent")
        print("• 例如：'帮我研究AI发展趋势并写一份报告'")
        print("• 例如：'我需要制定一个学习计划'") 
        print("• 例如：'分析这个数据并给出建议'")
        print("• 系统会自动判断是需要单个Agent还是多Agent协作")
        
        print("\\n📝 可用@引用:")
        print("• @user-profile - 用户画像信息")
        print("• @user-memory - 用户记忆内容")
        print("• @user-preferences - 用户偏好设置")
        print("• @[deliverable-id] - 引用产出物")
    
    async def process_user_input(self, user_input: str) -> dict:
        """处理用户输入 - 通过智能协调员"""
        print(f"\\n🔄 处理用户输入: {user_input}")
        
        # 检查智能协调员是否可用
        if not self.coordinator:
            print("❌ 智能协调员不可用，回退到直接处理")
            return await self._fallback_direct_processing(user_input)
        
        try:
            # 使用智能协调员处理用户输入
            result = await self.coordinator.process_user_input(
                user_input, 
                self.conversation_history[-10:]  # 传递最近对话历史
            )
            
            if result["success"]:
                # 更新对话历史
                self.conversation_history.append({"role": "user", "content": user_input})
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": result["data"]["response"]
                })
                
                return result
            else:
                print(f"❌ 智能协调员处理失败: {result.get('error')}")
                return result
                
        except Exception as e:
            print(f"❌ 智能协调员异常: {e}")
            return {
                "success": False,
                "error": f"智能协调员处理异常: {str(e)}"
            }
    
    async def execute_confirmed_plan(self, execution_plan: Dict[str, Any], user_input: str, 
                                    conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行已确认的计划"""
        print(f"\\n🚀 开始执行确认的计划...")
        
        try:
            # 使用智能协调员执行计划
            result = await self.coordinator.execute_confirmed_plan(
                execution_plan, 
                user_input, 
                conversation_history
            )
            
            if result["success"]:
                # 更新对话历史
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": result["data"]["response"]
                })
                
                return result
            else:
                print(f"❌ 计划执行失败: {result.get('error')}")
                return result
                
        except Exception as e:
            print(f"❌ 计划执行异常: {e}")
            return {
                "success": False,
                "error": f"计划执行异常: {str(e)}"
            }
    
    async def handle_plan_modification(self, original_plan: Dict[str, Any], user_input: str, 
                                      modification_request: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理用户的计划修改意见"""
        print(f"\\n🔄 处理修改意见: {modification_request}")
        
        # 检查智能协调员是否可用
        if not self.coordinator:
            return {
                "success": False,
                "error": "智能协调员不可用，无法处理修改"
            }
        
        try:
            # 使用智能协调员处理修改意见
            result = await self.coordinator.modify_execution_plan(
                original_plan,
                user_input,
                modification_request,
                conversation_history
            )
            
            if result["success"]:
                # 构建修改后的显示内容
                data = result["data"]
                execution_plan = data["plan"]
                
                # 格式化修改后的分析结果
                analysis_display = self.coordinator._format_analysis_for_display(
                    data["analysis"],
                    execution_plan
                )
                
                return {
                    "success": True,
                    "data": {
                        "response": analysis_display,
                        "agent_name": "AI智能协调员",
                        "agent_id": "coordinator",
                        "requires_confirmation": True,
                        "execution_plan": execution_plan,
                        "user_input": user_input,
                        "conversation_history": conversation_history,
                        "is_modified": True
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"修改处理失败: {result.get('error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"修改处理异常: {str(e)}"
            }
    
    async def _fallback_direct_processing(self, user_input: str) -> dict:
        """回退到直接处理模式"""
        # 简单的回退处理：使用第一个可用Agent
        if self.agents:
            first_agent = list(self.agents.values())[0]
            try:
                result = await asyncio.to_thread(
                    first_agent.process_user_input,
                    user_input,
                    self.conversation_history[-10:]
                )
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": f"回退处理失败: {str(e)}"
                }
        else:
            return {
                "success": False,
                "error": "没有可用的智能体"
            }
    
    
    async def run_interactive_demo(self):
        """运行交互式演示"""
        print("\\n" + "=" * 60)
        print("🎤 开始与智能协调员对话！")
        print("💡 智能协调员会帮你:")
        print("   📋 分析你的需求")
        print("   🎯 选择合适的专业Agent")
        print("   🔄 协调多Agent协作")
        print("   📊 整合所有结果")
        print("")
        print("🌟 尝试以下对话:")
        print("   • '我对AI投资很感兴趣，帮我研究一下当前的投资机会'")
        print("   • '帮我制定一个学习Python的计划'")
        print("   • '分析一下当前电商行业的发展趋势'")
        print("   • '我要写一份关于区块链的技术报告'")
        print("   • 输入 'quit' 退出，'help' 查看帮助")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\\n👤 您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 感谢使用FuturEmbryo多智能体协作系统！")
                    break
                
                if user_input.lower() in ['help', '帮助']:
                    self._show_help()
                    continue
                
                if user_input.lower() in ['status', '状态']:
                    self._show_status()
                    continue
                
                if not user_input:
                    continue
                
                print("🤖 处理中...")
                
                # 处理用户输入
                result = await self.process_user_input(user_input)
                
                if result["success"]:
                    data = result["data"]
                    response = data["response"]
                    agent_name = data.get("agent_name", "系统")
                    
                    print(f"🤖 {agent_name}: {response}")
                    
                    # 检查是否需要用户确认
                    if data.get("requires_confirmation"):
                        while True:  # 循环处理确认/修改
                            print("\\n" + "="*50)
                            user_response = input("👤 您的选择: ").strip()
                            
                            # 处理用户响应
                            if user_response.lower() in ['y', 'yes', '是', '确认', '好的']:
                                print("\\n✅ 用户确认执行，开始执行计划...")
                                
                                # 执行确认的计划
                                execution_result = await self.execute_confirmed_plan(
                                    data["execution_plan"],
                                    data["user_input"],
                                    data["conversation_history"]
                                )
                                
                                if execution_result["success"]:
                                    exec_data = execution_result["data"]
                                    exec_response = exec_data["response"]
                                    exec_agent_name = exec_data.get("agent_name", "系统")
                                    
                                    print(f"🎯 最终结果 - {exec_agent_name}: {exec_response}")
                                    
                                    # 显示产出物信息
                                    deliverables = exec_data.get("deliverables", [])
                                    if deliverables:
                                        print("\\n📊 生成的产出物:")
                                        for deliverable in deliverables:
                                            print(f"   • {deliverable['mention']} - {deliverable['name']}")
                                        print("   💡 您可以使用@引用来使用这些产出物")
                                    
                                    # 显示学习信息
                                    user_learning = exec_data.get("user_learning", {})
                                    if user_learning.get("profile_updated") or user_learning.get("preferences_learned"):
                                        print("🧠 系统学习更新:")
                                        if user_learning.get("profile_updated"):
                                            print("   • 用户画像已更新")
                                        if user_learning.get("preferences_learned"):
                                            print("   • 用户偏好已学习")
                                else:
                                    print(f"❌ 执行失败: {execution_result.get('error', '未知错误')}")
                                
                                break  # 执行完成，退出循环
                            
                            elif user_response.lower() in ['cancel', '取消', 'n', 'no']:
                                print("❌ 用户取消执行")
                                break  # 取消，退出循环
                            
                            else:
                                # 用户提出了修改意见
                                print(f"\\n🔄 AI正在根据您的修改意见重新规划...")
                                
                                # 处理修改意见
                                modification_result = await self.handle_plan_modification(
                                    data["execution_plan"],
                                    data["user_input"],
                                    user_response,
                                    data["conversation_history"]
                                )
                                
                                if modification_result["success"]:
                                    mod_data = modification_result["data"]
                                    mod_response = mod_data["response"]
                                    mod_agent_name = mod_data.get("agent_name", "系统")
                                    
                                    print(f"🧠 {mod_agent_name}: {mod_response}")
                                    
                                    # 更新数据为修改后的计划，继续循环确认
                                    data = mod_data
                                    print("\\n📝 请对修改后的计划进行确认...")
                                else:
                                    print(f"❌ 修改失败: {modification_result.get('error', '未知错误')}")
                                    break  # 修改失败，退出循环
                    else:
                        # 无需确认，直接显示结果
                        # 显示产出物信息
                        deliverables = data.get("deliverables", [])
                        if deliverables:
                            print("\\n📊 生成的产出物:")
                            for deliverable in deliverables:
                                print(f"   • {deliverable['mention']} - {deliverable['name']}")
                            print("   💡 您可以使用@引用来使用这些产出物")
                        
                        # 显示学习信息
                        user_learning = data.get("user_learning", {})
                        if user_learning.get("profile_updated") or user_learning.get("preferences_learned"):
                            print("🧠 系统学习更新:")
                            if user_learning.get("profile_updated"):
                                print("   • 用户画像已更新")
                            if user_learning.get("preferences_learned"):
                                print("   • 用户偏好已学习")
                
                else:
                    print(f"❌ 处理失败: {result.get('error', '未知错误')}")
                
            except KeyboardInterrupt:
                print("\\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 系统错误: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        print("\\n📖 使用帮助:")
        print("\\n🤖 智能体使用:")
        print("   @researcher - 研究和信息收集")
        print("   @analyst - 数据分析和洞察")
        print("   @writer - 内容写作和整理")
        print("   @creative - 创意和方案设计")
        print("   @planner - 项目规划和任务分解")
        
        print("\\n📝 用户信息引用:")
        print("   @user-profile - 查看用户画像")
        print("   @user-memory - 查看用户记忆")
        print("   @user-preferences - 查看用户偏好")
        
        print("\\n💡 使用技巧:")
        print("   • 明确表达需求: '我需要研究...'")
        print("   • 指定智能体: '@researcher 帮我研究...'")
        print("   • 要求记录信息: '记住我对...感兴趣'")
        print("   • 引用产出物: '基于@report-123 写总结'")
        
        print("\\n🎯 系统命令:")
        print("   help - 显示此帮助")
        print("   status - 显示系统状态")
        print("   quit - 退出系统")
    
    def _show_status(self):
        """显示系统状态"""
        print("\\n📊 系统状态:")
        
        # 用户记忆状态
        user_context = self.user_memory.get_user_context_for_agents()
        profile = user_context.get("user_profile", {})
        
        print("\\n🧠 用户信息:")
        interests = profile.get("interests", [])
        if interests:
            print(f"   兴趣: {', '.join(interests)}")
        
        comm_style = profile.get("communication_style", "未设置")
        print(f"   沟通风格: {comm_style}")
        
        recent_memories = user_context.get("recent_memories", [])
        print(f"   记忆条目: {len(recent_memories)} 个")
        
        # 对话统计
        print(f"\\n💬 对话统计:")
        print(f"   历史轮数: {len(self.conversation_history) // 2}")
        
        # 产出物统计
        print(f"\\n📊 产出物:")
        print(f"   本次会话: {len(self.session_deliverables)} 个")
        
        if self.session_deliverables:
            print("   最近产出:")
            for deliverable in self.session_deliverables[-3:]:
                print(f"   • {deliverable['mention']} - {deliverable['name']}")
        
        # Agent状态
        print(f"\\n🤖 智能体状态:")
        for agent_id, agent in self.agents.items():
            print(f"   • {agent_id}: 活跃")
    
    async def run_preset_scenario(self, scenario_name: str):
        """运行预设场景"""
        scenarios = self.config.get("demo", {}).get("scenarios", [])
        scenario = next((s for s in scenarios if s["name"] == scenario_name), None)
        
        if not scenario:
            print(f"❌ 未找到场景: {scenario_name}")
            return
        
        print(f"\\n🎬 运行场景: {scenario['description']}")
        print(f"📝 初始提示: {scenario['initial_prompt']}")
        print("-" * 40)
        
        # 执行场景
        result = await self.process_user_input(scenario["initial_prompt"])
        
        if result["success"]:
            print(f"🤖 {result['data']['agent_name']}: {result['data']['response']}")
        else:
            print(f"❌ 场景执行失败: {result.get('error')}")


async def main():
    """主函数"""
    print("🌟 FuturEmbryo多智能体协作系统演示")
    print("基于FuturEmbryo核心框架的用户中心@机制驱动")
    print()
    
    try:
        # 创建演示系统
        demo = MultiAgentCollaborationDemo()
        
        # 检查命令行参数
        if len(sys.argv) > 1:
            scenario = sys.argv[1]
            if scenario in ["personal_assistant", "business_analysis", "creative_project"]:
                await demo.run_preset_scenario(scenario)
                return
        
        # 运行交互式演示
        await demo.run_interactive_demo()
        
    except FileNotFoundError as e:
        print(f"❌ 配置文件未找到: {e}")
        print("请确保在正确目录运行，且配置文件存在")
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())