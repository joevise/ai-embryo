#!/usr/bin/env python3
"""
Level 5: 通信协作能力测试

测试目标：验证多个数字生命体之间的协作通信能力
- 多生命体架构
- 数字生命通信协议
- 协作任务执行
- 生命体间知识共享
"""

import asyncio
import sys
from pathlib import Path

# 添加测试工具路径
sys.path.append(str(Path(__file__).parent))

from test_config import TestLevel, get_test_config, get_api_config
from utils.test_utils import TestRunner, validate_life_form_basic, test_basic_interaction
from utils.test_utils import assert_success_rate, assert_response_time, assert_metric_threshold


class Level5CollaborationTest:
    """Level 5 通信协作能力测试类"""
    
    def __init__(self):
        self.test_config = get_test_config(TestLevel.LEVEL_5_COLLABORATION)
        self.runner = TestRunner("Level 5: 通信协作能力")
        self.life_forms = {}  # 存储多个生命体
    
    async def run_all_tests(self):
        """运行所有Level 5测试"""
        
        print("🤝 Level 5: 通信协作能力测试")
        print("=" * 50)
        print("测试范围: 多生命体架构, 通信协议, 协作任务, 知识共享")
        print("新增功能: 生命体通信, 协作决策, 任务分工")
        print()
        
        # 初始化测试环境
        try:
            api_config = get_api_config()
            await self.runner.initialize_environment(api_config)
        except Exception as e:
            print(f"⚠️  API配置失败，使用演示模式: {e}")
            await self.runner.initialize_environment()
        
        # 执行测试
        await self.test_multi_life_creation()
        await self.test_communication_protocol()
        await self.test_collaborative_task()
        await self.test_knowledge_sharing()
        await self.test_coordination_mechanism()
        
        # 清理
        self.runner.cleanup()
        
        # 输出结果
        self.runner.print_summary()
        return self.runner.get_success_rate() >= 0.65  # 要求65%通过率
    
    async def test_multi_life_creation(self):
        """测试多生命体创建"""
        
        async with self.runner.run_test("多生命体创建") as result:
            print("🤝 测试多生命体创建...")
            
            # 创建不同专业的生命体
            life_specs = [
                {
                    "name": "researcher",
                    "goal": "创建一个专业的研究助手",
                    "constraints": {
                        "cell_types": ["LLMCell", "MindCell", "StateMemoryCell"],
                        "specialization": "research",
                        "collaboration_enabled": True
                    }
                },
                {
                    "name": "analyzer",
                    "goal": "创建一个数据分析师",
                    "constraints": {
                        "cell_types": ["LLMCell", "MindCell", "StateMemoryCell", "ToolCell"],
                        "specialization": "analysis",
                        "collaboration_enabled": True
                    }
                },
                {
                    "name": "coordinator",
                    "goal": "创建一个项目协调者",
                    "constraints": {
                        "cell_types": ["LLMCell", "MindCell"],
                        "specialization": "coordination",
                        "collaboration_enabled": True
                    }
                }
            ]
            
            creation_results = []
            
            for spec in life_specs:
                try:
                    life_form = await self.runner.environment.create_basic_life(
                        goal=spec["goal"],
                        constraints=spec["constraints"]
                    )
                    
                    self.life_forms[spec["name"]] = life_form
                    
                    # 验证生命体基本功能
                    validations = validate_life_form_basic(life_form)
                    has_collaboration = hasattr(life_form, 'collaborate') or hasattr(life_form, 'communicate')
                    
                    creation_results.append({
                        "name": spec["name"],
                        "created": True,
                        "basic_validations": sum(validations.values()),
                        "has_collaboration": has_collaboration,
                        "cell_count": len(life_form.cells)
                    })
                    
                    print(f"   ✅ {spec['name']}: 创建成功, {len(life_form.cells)}个Cell")
                    print(f"      协作能力: {'✅' if has_collaboration else '❌'}")
                    
                    result.add_artifact(f"life_{spec['name']}", life_form)
                    
                except Exception as e:
                    print(f"   ❌ {spec['name']}: 创建失败 - {e}")
                    creation_results.append({
                        "name": spec["name"],
                        "created": False,
                        "error": str(e)
                    })
            
            # 验证创建成功率
            successful_creations = sum(1 for r in creation_results if r.get("created", False))
            creation_success_rate = successful_creations / len(life_specs)
            
            print(f"   📊 生命体创建成功率: {creation_success_rate*100:.1f}%")
            print(f"   🧬 成功创建: {successful_creations}/{len(life_specs)}个生命体")
            
            # 验证成功标准
            expected_rate = self.test_config.success_criteria.get("creation_rate", 0.8)
            assert_success_rate(creation_success_rate, expected_rate, "多生命体创建")
            
            result.mark_success({
                "creation_success_rate": creation_success_rate,
                "successful_creations": successful_creations,
                "total_life_forms": len(life_specs),
                "created_life_forms": list(self.life_forms.keys())
            })
    
    async def test_communication_protocol(self):
        """测试生命体间通信协议"""
        
        async with self.runner.run_test("通信协议验证") as result:
            print("\n📡 测试通信协议...")
            
            if len(self.life_forms) < 2:
                raise RuntimeError("需要至少2个生命体进行通信测试")
            
            # 获取两个生命体进行通信测试
            life_names = list(self.life_forms.keys())
            sender = self.life_forms[life_names[0]]
            receiver = self.life_forms[life_names[1]]
            
            print(f"   📤 发送方: {life_names[0]}")
            print(f"   📥 接收方: {life_names[1]}")
            
            # 测试通信场景
            communication_scenarios = [
                {
                    "message": "你好，我是研究助手，可以协作吗？",
                    "type": "greeting",
                    "expected_response": True
                },
                {
                    "message": "请帮我分析这个数据集的特征",
                    "type": "task_request",
                    "expected_response": True
                },
                {
                    "message": "我们来讨论一下项目计划",
                    "type": "discussion",
                    "expected_response": True
                }
            ]
            
            communication_results = []
            
            for scenario in communication_scenarios:
                try:
                    # 模拟生命体间通信
                    # 这里可能需要实现特定的通信接口
                    
                    # 发送方准备消息
                    send_context = {
                        "message": scenario["message"],
                        "target": life_names[1],
                        "type": scenario["type"]
                    }
                    
                    # 如果生命体有特定的通信方法
                    if hasattr(sender, 'send_message'):
                        send_result = await sender.send_message(send_context)
                    else:
                        # 使用通用think方法模拟
                        send_result = await sender.think(f"向{life_names[1]}发送消息: {scenario['message']}")
                    
                    # 接收方处理消息
                    receive_context = {
                        "message": scenario["message"],
                        "sender": life_names[0],
                        "type": scenario["type"]
                    }
                    
                    if hasattr(receiver, 'receive_message'):
                        receive_result = await receiver.receive_message(receive_context)
                    else:
                        # 使用通用think方法模拟
                        receive_result = await receiver.think(f"收到来自{life_names[0]}的消息: {scenario['message']}")
                    
                    # 评估通信效果
                    send_success = send_result.get("success", False)
                    receive_success = receive_result.get("success", False)
                    
                    communication_success = send_success and receive_success
                    
                    communication_results.append({
                        "scenario": scenario["type"],
                        "message": scenario["message"][:30] + "...",
                        "send_success": send_success,
                        "receive_success": receive_success,
                        "communication_success": communication_success
                    })
                    
                    status = "✅" if communication_success else "❌"
                    print(f"   {status} {scenario['type']}: {'成功' if communication_success else '失败'}")
                    
                except Exception as e:
                    print(f"   ❌ {scenario['type']}: 通信异常 - {e}")
                    communication_results.append({
                        "scenario": scenario["type"],
                        "error": str(e),
                        "communication_success": False
                    })
            
            # 计算通信成功率
            successful_communications = sum(1 for r in communication_results if r.get("communication_success", False))
            communication_success_rate = successful_communications / len(communication_scenarios)
            
            print(f"   📊 通信成功率: {communication_success_rate*100:.1f}%")
            print(f"   📡 成功通信: {successful_communications}/{len(communication_scenarios)}")
            
            # 验证通信效果
            expected_rate = self.test_config.success_criteria.get("communication", 0.7)
            assert_success_rate(communication_success_rate, expected_rate, "通信协议")
            
            result.mark_success({
                "communication_success_rate": communication_success_rate,
                "successful_communications": successful_communications,
                "total_scenarios": len(communication_scenarios)
            })
    
    async def test_collaborative_task(self):
        """测试协作任务执行"""
        
        async with self.runner.run_test("协作任务执行") as result:
            print("\n🎯 测试协作任务执行...")
            
            if len(self.life_forms) < 2:
                raise RuntimeError("需要至少2个生命体进行协作测试")
            
            # 定义协作任务
            collaborative_task = {
                "description": "制定一个AI项目的完整计划",
                "subtasks": [
                    "需求分析和目标定义",
                    "技术方案设计",
                    "资源评估和时间规划",
                    "风险评估和应对策略"
                ],
                "roles": {
                    "researcher": "负责需求分析和技术调研",
                    "analyzer": "负责数据分析和风险评估",
                    "coordinator": "负责整体协调和计划制定"
                }
            }
            
            print(f"   🎯 协作任务: {collaborative_task['description']}")
            print(f"   📋 子任务数量: {len(collaborative_task['subtasks'])}")
            
            # 执行协作任务
            collaboration_results = []
            task_assignments = {}
            
            # 为每个生命体分配任务
            available_life_forms = list(self.life_forms.keys())
            for i, subtask in enumerate(collaborative_task["subtasks"]):
                assigned_life = available_life_forms[i % len(available_life_forms)]
                task_assignments[subtask] = assigned_life
                
                try:
                    # 生命体执行分配的子任务
                    life_form = self.life_forms[assigned_life]
                    
                    task_context = {
                        "main_task": collaborative_task["description"],
                        "assigned_subtask": subtask,
                        "role": collaborative_task["roles"].get(assigned_life, "participant"),
                        "collaboration_mode": True
                    }
                    
                    task_result = await life_form.think(
                        f"在协作项目中执行任务: {subtask}",
                        context=task_context
                    )
                    
                    task_success = task_result.get("success", False)
                    task_output = task_result.get("data", {}).get("response", "")
                    
                    collaboration_results.append({
                        "subtask": subtask,
                        "assigned_to": assigned_life,
                        "success": task_success,
                        "output_length": len(task_output),
                        "quality_score": self._assess_task_quality(task_output, subtask)
                    })
                    
                    status = "✅" if task_success else "❌"
                    print(f"   {status} {subtask[:40]}... -> {assigned_life}")
                    print(f"      输出长度: {len(task_output)}字符")
                    
                except Exception as e:
                    print(f"   ❌ {subtask[:40]}... -> {assigned_life}: 执行失败 - {e}")
                    collaboration_results.append({
                        "subtask": subtask,
                        "assigned_to": assigned_life,
                        "success": False,
                        "error": str(e)
                    })
            
            # 测试结果整合
            try:
                # 选择一个生命体作为协调者整合结果
                coordinator_name = "coordinator" if "coordinator" in self.life_forms else available_life_forms[0]
                coordinator = self.life_forms[coordinator_name]
                
                integration_context = {
                    "task_results": [r for r in collaboration_results if r.get("success", False)],
                    "main_task": collaborative_task["description"],
                    "role": "integration_coordinator"
                }
                
                integration_result = await coordinator.think(
                    "整合所有子任务结果，形成完整的项目计划",
                    context=integration_context
                )
                
                integration_success = integration_result.get("success", False)
                final_plan = integration_result.get("data", {}).get("response", "")
                
                print(f"   🔗 结果整合: {'成功' if integration_success else '失败'}")
                print(f"   📄 最终计划长度: {len(final_plan)}字符")
                
            except Exception as e:
                print(f"   ❌ 结果整合失败: {e}")
                integration_success = False
            
            # 计算协作效果
            successful_subtasks = sum(1 for r in collaboration_results if r.get("success", False))
            collaboration_success_rate = successful_subtasks / len(collaborative_task["subtasks"])
            
            avg_quality = sum(r.get("quality_score", 0) for r in collaboration_results if "quality_score" in r)
            avg_quality = avg_quality / len(collaboration_results) if collaboration_results else 0
            
            print(f"   📊 协作成功率: {collaboration_success_rate*100:.1f}%")
            print(f"   ⭐ 平均质量分数: {avg_quality:.2f}")
            print(f"   ✅ 成功子任务: {successful_subtasks}/{len(collaborative_task['subtasks'])}")
            
            # 验证协作效果
            expected_rate = self.test_config.success_criteria.get("collaboration", 0.6)
            assert_success_rate(collaboration_success_rate, expected_rate, "协作任务执行")
            
            result.mark_success({
                "collaboration_success_rate": collaboration_success_rate,
                "integration_success": integration_success,
                "avg_quality_score": avg_quality,
                "successful_subtasks": successful_subtasks,
                "total_subtasks": len(collaborative_task["subtasks"])
            })
    
    def _assess_task_quality(self, output: str, subtask: str) -> float:
        """评估任务输出质量"""
        if not output:
            return 0.0
        
        # 简单的质量评估
        quality_indicators = {
            "length_adequate": len(output) > 100,  # 足够长度
            "has_structure": any(indicator in output for indicator in ["1.", "首先", "其次", "最后"]),  # 有结构
            "task_relevant": any(keyword in output.lower() for keyword in subtask.lower().split()),  # 相关性
            "has_details": len(output.split()) > 50  # 有详细内容
        }
        
        return sum(quality_indicators.values()) / len(quality_indicators)
    
    async def test_knowledge_sharing(self):
        """测试生命体间知识共享"""
        
        async with self.runner.run_test("知识共享机制") as result:
            print("\n📚 测试知识共享...")
            
            if len(self.life_forms) < 2:
                raise RuntimeError("需要至少2个生命体进行知识共享测试")
            
            # 选择两个生命体进行知识共享测试
            life_names = list(self.life_forms.keys())
            teacher = self.life_forms[life_names[0]]
            learner = self.life_forms[life_names[1]]
            
            print(f"   🧑‍🏫 知识提供者: {life_names[0]}")
            print(f"   🧑‍🎓 知识学习者: {life_names[1]}")
            
            # 准备共享知识
            knowledge_items = [
                {
                    "topic": "Python编程最佳实践",
                    "content": "使用虚拟环境管理依赖，遵循PEP8编码规范，编写单元测试"
                },
                {
                    "topic": "机器学习模型评估",
                    "content": "使用交叉验证，关注准确率、召回率和F1分数，避免过拟合"
                },
                {
                    "topic": "项目管理经验",
                    "content": "制定明确的里程碑，定期团队沟通，使用敏捷开发方法"
                }
            ]
            
            sharing_results = []
            
            for knowledge in knowledge_items:
                try:
                    # 教师分享知识
                    sharing_context = {
                        "knowledge_topic": knowledge["topic"],
                        "knowledge_content": knowledge["content"],
                        "sharing_mode": True,
                        "target_learner": life_names[1]
                    }
                    
                    # 如果有特定的知识分享方法
                    if hasattr(teacher, 'share_knowledge'):
                        share_result = await teacher.share_knowledge(sharing_context)
                    else:
                        share_result = await teacher.think(
                            f"向{life_names[1]}分享关于{knowledge['topic']}的知识: {knowledge['content']}"
                        )
                    
                    # 学习者接收和处理知识
                    learning_context = {
                        "received_knowledge": knowledge["content"],
                        "knowledge_topic": knowledge["topic"],
                        "learning_mode": True,
                        "knowledge_source": life_names[0]
                    }
                    
                    if hasattr(learner, 'absorb_knowledge'):
                        learn_result = await learner.absorb_knowledge(learning_context)
                    else:
                        learn_result = await learner.think(
                            f"学习来自{life_names[0]}的知识: {knowledge['topic']} - {knowledge['content']}"
                        )
                    
                    # 验证知识吸收
                    verification_result = await learner.think(
                        f"请总结你学到的关于{knowledge['topic']}的知识"
                    )
                    
                    share_success = share_result.get("success", False)
                    learn_success = learn_result.get("success", False)
                    verify_success = verification_result.get("success", False)
                    
                    verification_content = verification_result.get("data", {}).get("response", "")
                    knowledge_retained = knowledge["topic"].lower() in verification_content.lower()
                    
                    sharing_results.append({
                        "topic": knowledge["topic"],
                        "share_success": share_success,
                        "learn_success": learn_success,
                        "verify_success": verify_success,
                        "knowledge_retained": knowledge_retained,
                        "verification_length": len(verification_content)
                    })
                    
                    status = "✅" if share_success and learn_success and knowledge_retained else "❌"
                    print(f"   {status} {knowledge['topic']}: 分享{'✅' if share_success else '❌'} 学习{'✅' if learn_success else '❌'} 保持{'✅' if knowledge_retained else '❌'}")
                    
                except Exception as e:
                    print(f"   ❌ {knowledge['topic']}: 共享失败 - {e}")
                    sharing_results.append({
                        "topic": knowledge["topic"],
                        "error": str(e),
                        "share_success": False,
                        "learn_success": False,
                        "knowledge_retained": False
                    })
            
            # 计算知识共享效果
            successful_shares = sum(1 for r in sharing_results if r.get("share_success", False) and r.get("learn_success", False))
            knowledge_retention = sum(1 for r in sharing_results if r.get("knowledge_retained", False))
            
            sharing_success_rate = successful_shares / len(knowledge_items)
            retention_rate = knowledge_retention / len(knowledge_items)
            
            print(f"   📊 知识共享成功率: {sharing_success_rate*100:.1f}%")
            print(f"   🧠 知识保持率: {retention_rate*100:.1f}%")
            print(f"   ✅ 成功共享: {successful_shares}/{len(knowledge_items)}")
            
            # 验证知识共享效果
            expected_rate = self.test_config.success_criteria.get("knowledge_sharing", 0.6)
            assert_success_rate(sharing_success_rate, expected_rate, "知识共享机制")
            
            result.mark_success({
                "sharing_success_rate": sharing_success_rate,
                "knowledge_retention_rate": retention_rate,
                "successful_shares": successful_shares,
                "total_knowledge_items": len(knowledge_items)
            })
    
    async def test_coordination_mechanism(self):
        """测试协调机制"""
        
        async with self.runner.run_test("协调机制验证") as result:
            print("\n🎼 测试协调机制...")
            
            if len(self.life_forms) < 3:
                print("   ⚠️  生命体数量不足3个，使用简化协调测试")
            
            # 模拟需要协调的复杂场景
            coordination_scenario = {
                "situation": "多个专家需要协调解决一个复杂的技术问题",
                "problem": "设计一个高并发的微服务架构",
                "constraints": [
                    "性能要求：支持10万QPS",
                    "可用性要求：99.9%",
                    "成本约束：有限预算",
                    "时间约束：3个月内上线"
                ]
            }
            
            print(f"   🎯 协调场景: {coordination_scenario['situation']}")
            print(f"   🔧 具体问题: {coordination_scenario['problem']}")
            
            # 选择协调者
            coordinator_name = "coordinator" if "coordinator" in self.life_forms else list(self.life_forms.keys())[0]
            coordinator = self.life_forms[coordinator_name]
            
            participants = [name for name in self.life_forms.keys() if name != coordinator_name]
            
            print(f"   🎼 协调者: {coordinator_name}")
            print(f"   👥 参与者: {participants}")
            
            coordination_results = []
            
            try:
                # 第一步：协调者分析问题并制定协调计划
                coordination_context = {
                    "scenario": coordination_scenario,
                    "participants": participants,
                    "role": "coordination_leader"
                }
                
                coordination_plan = await coordinator.think(
                    f"制定协调计划解决问题: {coordination_scenario['problem']}",
                    context=coordination_context
                )
                
                plan_success = coordination_plan.get("success", False)
                plan_content = coordination_plan.get("data", {}).get("response", "")
                
                print(f"   📋 协调计划制定: {'成功' if plan_success else '失败'}")
                
                # 第二步：协调各参与者的意见和建议
                participant_inputs = []
                for participant_name in participants:
                    participant = self.life_forms[participant_name]
                    
                    input_context = {
                        "scenario": coordination_scenario,
                        "coordination_plan": plan_content,
                        "role": f"expert_{participant_name}"
                    }
                    
                    participant_input = await participant.think(
                        f"作为{participant_name}专家，对{coordination_scenario['problem']}提出专业建议",
                        context=input_context
                    )
                    
                    if participant_input.get("success", False):
                        participant_inputs.append({
                            "expert": participant_name,
                            "input": participant_input.get("data", {}).get("response", ""),
                            "success": True
                        })
                    else:
                        participant_inputs.append({
                            "expert": participant_name,
                            "error": participant_input.get("error", ""),
                            "success": False
                        })
                
                successful_inputs = sum(1 for inp in participant_inputs if inp["success"])
                input_success_rate = successful_inputs / len(participants) if participants else 1
                
                print(f"   💬 专家意见收集: {successful_inputs}/{len(participants)} 成功")
                
                # 第三步：协调者整合所有意见并制定最终方案
                final_context = {
                    "scenario": coordination_scenario,
                    "participant_inputs": participant_inputs,
                    "role": "final_coordinator"
                }
                
                final_solution = await coordinator.think(
                    "整合所有专家意见，制定最终的技术方案",
                    context=final_context
                )
                
                final_success = final_solution.get("success", False)
                final_content = final_solution.get("data", {}).get("response", "")
                
                print(f"   🎯 最终方案制定: {'成功' if final_success else '失败'}")
                print(f"   📄 方案长度: {len(final_content)}字符")
                
                # 评估协调效果
                coordination_quality = self._assess_coordination_quality(
                    plan_content, participant_inputs, final_content
                )
                
                coordination_results.append({
                    "plan_success": plan_success,
                    "input_success_rate": input_success_rate,
                    "final_success": final_success,
                    "coordination_quality": coordination_quality,
                    "participant_count": len(participants)
                })
                
            except Exception as e:
                print(f"   ❌ 协调过程异常: {e}")
                coordination_results.append({
                    "error": str(e),
                    "plan_success": False,
                    "final_success": False
                })
            
            # 计算协调效果
            if coordination_results and coordination_results[0].get("plan_success", False):
                coordination_success = (
                    coordination_results[0].get("plan_success", False) and
                    coordination_results[0].get("final_success", False) and
                    coordination_results[0].get("input_success_rate", 0) > 0.5
                )
                
                overall_quality = coordination_results[0].get("coordination_quality", 0)
                
                print(f"   📊 协调成功: {'是' if coordination_success else '否'}")
                print(f"   ⭐ 协调质量: {overall_quality:.2f}")
                
                # 验证协调效果
                if coordination_success:
                    expected_quality = self.test_config.success_criteria.get("coordination_quality", 0.6)
                    assert overall_quality >= expected_quality, f"协调质量 {overall_quality:.2f} 低于期望 {expected_quality}"
                
                result.mark_success({
                    "coordination_success": coordination_success,
                    "coordination_quality": overall_quality,
                    "participant_engagement": coordination_results[0].get("input_success_rate", 0)
                })
            else:
                raise AssertionError("协调机制测试失败")
    
    def _assess_coordination_quality(self, plan: str, inputs: list, final_solution: str) -> float:
        """评估协调质量"""
        quality_score = 0.0
        
        # 检查计划质量
        if plan and len(plan) > 100:
            quality_score += 0.3
        
        # 检查参与度
        successful_inputs = sum(1 for inp in inputs if inp.get("success", False))
        if successful_inputs > 0:
            quality_score += 0.3 * (successful_inputs / len(inputs))
        
        # 检查最终方案质量
        if final_solution and len(final_solution) > 200:
            quality_score += 0.2
            
            # 检查是否体现了协调整合
            integration_indicators = ["综合", "整合", "考虑", "结合", "平衡"]
            if any(indicator in final_solution for indicator in integration_indicators):
                quality_score += 0.2
        
        return min(quality_score, 1.0)


async def main():
    """主函数"""
    
    # 创建并运行Level 5测试
    level5_test = Level5CollaborationTest()
    
    try:
        success = await level5_test.run_all_tests()
        
        if success:
            print("\n🎉 Level 5 测试完全通过！")
            print("✅ 通信协作能力验证成功")
            print("✅ 可以进入 Level 6 测试")
            return True
        else:
            print("\n❌ Level 5 测试未完全通过")
            print("🔧 请修复问题后重新测试")
            return False
            
    except Exception as e:
        print(f"\n💥 Level 5 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    print("🌱 FuturEmbryo v2.1c 渐进式测试")
    print("🤝 Level 5: 通信协作能力测试")
    print("=" * 60)
    
    success = asyncio.run(main())
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f}秒")
    
    if success:
        print("🚀 Level 5 通过，准备进入 Level 6！")
        exit(0)
    else:
        print("❌ Level 5 失败，需要修复问题")
        exit(1)