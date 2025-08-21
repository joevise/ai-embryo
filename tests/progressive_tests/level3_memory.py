#!/usr/bin/env python3
"""
Level 3: 知识记忆能力测试

测试目标：验证数字生命体的记忆和知识管理能力
- LLMCell + MindCell + StateMemoryCell架构
- 记忆存储和检索
- 上下文记忆管理
- 知识库构建能力
"""

import asyncio
import sys
from pathlib import Path

# 添加测试工具路径
sys.path.append(str(Path(__file__).parent))

from test_config import TestLevel, get_test_config, get_api_config
from utils.test_utils import TestRunner, validate_life_form_basic, test_basic_interaction
from utils.test_utils import assert_success_rate, assert_response_time, assert_metric_threshold


class Level3MemoryTest:
    """Level 3 知识记忆能力测试类"""
    
    def __init__(self):
        self.test_config = get_test_config(TestLevel.LEVEL_3_MEMORY)
        self.runner = TestRunner("Level 3: 知识记忆能力")
        self.memory_life_form = None
    
    async def run_all_tests(self):
        """运行所有Level 3测试"""
        
        print("🧠 Level 3: 知识记忆能力测试")
        print("=" * 50)
        print("测试范围: LLMCell + MindCell + StateMemoryCell, 记忆管理, 知识检索")
        print("新增功能: 记忆存储, 上下文记忆, 知识库构建")
        print()
        
        # 初始化测试环境
        try:
            api_config = get_api_config()
            await self.runner.initialize_environment(api_config)
        except Exception as e:
            print(f"⚠️  API配置失败，使用演示模式: {e}")
            await self.runner.initialize_environment()
        
        # 执行测试
        await self.test_memory_life_creation()
        await self.test_memory_storage()
        await self.test_memory_retrieval()
        await self.test_context_memory()
        await self.test_knowledge_base_building()
        
        # 清理
        self.runner.cleanup()
        
        # 输出结果
        self.runner.print_summary()
        return self.runner.get_success_rate() >= 0.75  # 要求75%通过率
    
    async def test_memory_life_creation(self):
        """测试具备记忆能力的生命体创建"""
        
        async with self.runner.run_test("记忆生命体创建") as result:
            print("🧠 测试记忆生命体创建...")
            
            # 创建具备记忆能力的数字生命体
            memory_life = await self.runner.environment.create_basic_life(
                goal="创建一个有记忆能力的知识助手",
                constraints={
                    "cell_types": ["LLMCell", "MindCell", "StateMemoryCell"],
                    "memory_enabled": True,
                    "knowledge_base": True,
                    "architecture": "pipeline"
                }
            )
            
            self.memory_life_form = memory_life
            result.add_artifact("memory_life", memory_life)
            
            # 验证架构
            print(f"   🏗️  Cell架构: {[cell.__class__.__name__ for cell in memory_life.cells]}")
            
            # 检查是否包含StateMemoryCell
            has_memory_cell = any(cell.__class__.__name__ == "StateMemoryCell" for cell in memory_life.cells)
            has_mind_cell = any(cell.__class__.__name__ == "MindCell" for cell in memory_life.cells)
            has_llm_cell = any(cell.__class__.__name__ == "LLMCell" for cell in memory_life.cells)
            
            assert has_llm_cell, "应该包含LLMCell"
            assert has_mind_cell, "应该包含MindCell"
            assert has_memory_cell, "应该包含StateMemoryCell"
            
            print(f"   ✅ LLMCell: {'存在' if has_llm_cell else '缺失'}")
            print(f"   ✅ MindCell: {'存在' if has_mind_cell else '缺失'}")
            print(f"   ✅ StateMemoryCell: {'存在' if has_memory_cell else '缺失'}")
            
            # 找到StateMemoryCell并验证其能力
            memory_cell = None
            for cell in memory_life.cells:
                if cell.__class__.__name__ == "StateMemoryCell":
                    memory_cell = cell
                    break
            
            if memory_cell:
                # 验证StateMemoryCell的记忆功能
                has_store_method = hasattr(memory_cell, 'store')
                has_search_method = hasattr(memory_cell, 'search')
                has_retrieve_method = hasattr(memory_cell, 'retrieve')
                has_update_method = hasattr(memory_cell, 'update')
                
                print(f"   💾 存储功能: {'✅' if has_store_method else '❌'}")
                print(f"   🔍 搜索功能: {'✅' if has_search_method else '❌'}")
                print(f"   📥 检索功能: {'✅' if has_retrieve_method else '❌'}")
                print(f"   🔄 更新功能: {'✅' if has_update_method else '❌'}")
                
                result.mark_success({
                    "has_memory_cell": True,
                    "store_method": has_store_method,
                    "search_method": has_search_method,
                    "retrieve_method": has_retrieve_method,
                    "cell_count": len(memory_life.cells)
                })
            else:
                raise AssertionError("未找到StateMemoryCell")
    
    async def test_memory_storage(self):
        """测试记忆存储能力"""
        
        async with self.runner.run_test("记忆存储能力") as result:
            print("\n💾 测试记忆存储能力...")
            
            if not self.memory_life_form:
                raise RuntimeError("需要先创建记忆生命体")
            
            # 找到StateMemoryCell
            memory_cell = None
            for cell in self.memory_life_form.cells:
                if cell.__class__.__name__ == "StateMemoryCell":
                    memory_cell = cell
                    break
            
            if not memory_cell:
                raise RuntimeError("未找到StateMemoryCell")
            
            # 测试存储不同类型的记忆
            storage_scenarios = [
                {
                    "content": "Python是一种高级编程语言",
                    "metadata": {"type": "knowledge", "category": "programming"},
                    "context": "编程知识"
                },
                {
                    "content": "用户喜欢简洁的代码风格",
                    "metadata": {"type": "preference", "category": "user"},
                    "context": "用户偏好"
                },
                {
                    "content": "昨天讨论了AI技术发展趋势",
                    "metadata": {"type": "conversation", "category": "history"},
                    "context": "对话历史"
                }
            ]
            
            storage_results = []
            
            for scenario in storage_scenarios:
                try:
                    # 存储记忆
                    storage_result = memory_cell.store(
                        content=scenario["content"],
                        metadata=scenario["metadata"],
                        context=scenario["context"]
                    )
                    
                    storage_success = storage_result.get("success", False)
                    memory_id = storage_result.get("memory_id", "")
                    
                    storage_results.append({
                        "content": scenario["content"][:30] + "...",
                        "type": scenario["metadata"]["type"],
                        "success": storage_success,
                        "memory_id": memory_id
                    })
                    
                    status = "✅" if storage_success else "❌"
                    print(f"   {status} {scenario['metadata']['type']}: {'成功' if storage_success else '失败'}")
                    
                except Exception as e:
                    print(f"   ❌ {scenario['metadata']['type']}: 异常 - {e}")
                    storage_results.append({
                        "content": scenario["content"][:30] + "...",
                        "type": scenario["metadata"]["type"],
                        "success": False,
                        "error": str(e)
                    })
            
            # 计算存储成功率
            successful_stores = sum(1 for r in storage_results if r.get("success", False))
            storage_success_rate = successful_stores / len(storage_scenarios)
            
            print(f"   📊 存储成功率: {storage_success_rate*100:.1f}%")
            print(f"   ✅ 成功存储: {successful_stores}/{len(storage_scenarios)}")
            
            # 验证存储成功率
            expected_rate = self.test_config.success_criteria["memory_storage_rate"]
            assert_success_rate(storage_success_rate, expected_rate, "记忆存储能力")
            
            result.mark_success({
                "storage_success_rate": storage_success_rate,
                "successful_stores": successful_stores,
                "total_storage_attempts": len(storage_scenarios)
            })
    
    async def test_memory_retrieval(self):
        """测试记忆检索能力"""
        
        async with self.runner.run_test("记忆检索能力") as result:
            print("\n🔍 测试记忆检索能力...")
            
            if not self.memory_life_form:
                raise RuntimeError("需要先创建记忆生命体")
            
            # 找到StateMemoryCell
            memory_cell = None
            for cell in self.memory_life_form.cells:
                if cell.__class__.__name__ == "StateMemoryCell":
                    memory_cell = cell
                    break
            
            if not memory_cell:
                raise RuntimeError("未找到StateMemoryCell")
            
            # 测试检索查询
            retrieval_scenarios = [
                {
                    "query": "Python编程语言",
                    "expected_type": "knowledge",
                    "context": "寻找编程相关知识"
                },
                {
                    "query": "用户偏好",
                    "expected_type": "preference",
                    "context": "了解用户喜好"
                },
                {
                    "query": "AI技术讨论",
                    "expected_type": "conversation",
                    "context": "回顾对话历史"
                }
            ]
            
            retrieval_results = []
            
            for scenario in retrieval_scenarios:
                try:
                    # 执行检索
                    search_result = memory_cell.search_memories(
                        query=scenario["query"],
                        context=scenario["context"],
                        limit=5
                    )
                    
                    retrieval_success = search_result.get("success", False)
                    memories = search_result.get("memories", [])
                    relevance_scores = search_result.get("scores", [])
                    
                    # 计算检索质量
                    has_results = len(memories) > 0
                    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
                    
                    retrieval_results.append({
                        "query": scenario["query"],
                        "expected_type": scenario["expected_type"],
                        "success": retrieval_success and has_results,
                        "result_count": len(memories),
                        "avg_relevance": avg_relevance
                    })
                    
                    status = "✅" if retrieval_success and has_results else "❌"
                    print(f"   {status} '{scenario['query']}': {len(memories)}条结果, 相关度{avg_relevance:.2f}")
                    
                except Exception as e:
                    print(f"   ❌ '{scenario['query']}': 异常 - {e}")
                    retrieval_results.append({
                        "query": scenario["query"],
                        "expected_type": scenario["expected_type"],
                        "success": False,
                        "error": str(e)
                    })
            
            # 计算检索成功率
            successful_retrievals = sum(1 for r in retrieval_results if r.get("success", False))
            retrieval_success_rate = successful_retrievals / len(retrieval_scenarios)
            
            # 计算平均相关度
            valid_results = [r for r in retrieval_results if "avg_relevance" in r]
            avg_relevance = sum(r["avg_relevance"] for r in valid_results) / len(valid_results) if valid_results else 0
            
            print(f"   📊 检索成功率: {retrieval_success_rate*100:.1f}%")
            print(f"   🎯 平均相关度: {avg_relevance:.2f}")
            
            # 验证检索成功率
            expected_rate = self.test_config.success_criteria["memory_retrieval_rate"]
            assert_success_rate(retrieval_success_rate, expected_rate, "记忆检索能力")
            
            result.mark_success({
                "retrieval_success_rate": retrieval_success_rate,
                "avg_relevance_score": avg_relevance,
                "successful_retrievals": successful_retrievals,
                "total_retrieval_attempts": len(retrieval_scenarios)
            })
    
    async def test_context_memory(self):
        """测试上下文记忆管理"""
        
        async with self.runner.run_test("上下文记忆管理") as result:
            print("\n🔄 测试上下文记忆管理...")
            
            if not self.memory_life_form:
                raise RuntimeError("需要先创建记忆生命体")
            
            # 模拟多轮对话，测试上下文记忆
            conversation_flow = [
                "我想学习Python编程",
                "请推荐一些学习资源",
                "我比较喜欢实际项目练习",
                "你刚才提到的学习方式是什么？",
                "之前讨论的编程语言是哪种？"
            ]
            
            context_results = []
            conversation_context = {}
            
            for i, user_input in enumerate(conversation_flow):
                try:
                    # 执行对话，期望生命体能利用之前的上下文
                    response = await self.memory_life_form.think(
                        user_input,
                        context=conversation_context
                    )
                    
                    response_success = response.get("success", False)
                    response_content = response.get("data", {}).get("response", "")
                    
                    # 检查是否体现了上下文记忆
                    context_awareness = False
                    if i >= 3:  # 从第4轮开始检查上下文引用
                        context_indicators = ["之前", "刚才", "前面", "Python", "学习"]
                        context_awareness = any(indicator in response_content for indicator in context_indicators)
                    
                    context_results.append({
                        "turn": i + 1,
                        "input": user_input,
                        "success": response_success,
                        "context_aware": context_awareness,
                        "response_length": len(response_content)
                    })
                    
                    # 更新对话上下文
                    conversation_context[f"turn_{i+1}"] = {
                        "user": user_input,
                        "assistant": response_content[:100]  # 保留前100字符
                    }
                    
                    status = "✅" if response_success else "❌"
                    context_status = "🔗" if context_awareness else "🔸"
                    print(f"   {status} 第{i+1}轮: {'成功' if response_success else '失败'} {context_status}")
                    
                except Exception as e:
                    print(f"   ❌ 第{i+1}轮: 异常 - {e}")
                    context_results.append({
                        "turn": i + 1,
                        "input": user_input,
                        "success": False,
                        "error": str(e)
                    })
            
            # 计算上下文记忆效果
            successful_turns = sum(1 for r in context_results if r.get("success", False))
            context_aware_turns = sum(1 for r in context_results if r.get("context_aware", False))
            
            conversation_success_rate = successful_turns / len(conversation_flow)
            context_awareness_rate = context_aware_turns / max(1, len(conversation_flow) - 3)  # 只考虑后3轮
            
            print(f"   📊 对话成功率: {conversation_success_rate*100:.1f}%")
            print(f"   🔗 上下文感知率: {context_awareness_rate*100:.1f}%")
            
            # 验证上下文记忆效果
            expected_rate = self.test_config.success_criteria["context_continuity"]
            assert_success_rate(context_awareness_rate, expected_rate, "上下文记忆管理")
            
            result.mark_success({
                "conversation_success_rate": conversation_success_rate,
                "context_awareness_rate": context_awareness_rate,
                "successful_turns": successful_turns,
                "total_turns": len(conversation_flow)
            })
    
    async def test_knowledge_base_building(self):
        """测试知识库构建能力"""
        
        async with self.runner.run_test("知识库构建能力") as result:
            print("\n📚 测试知识库构建能力...")
            
            if not self.memory_life_form:
                raise RuntimeError("需要先创建记忆生命体")
            
            # 找到StateMemoryCell
            memory_cell = None
            for cell in self.memory_life_form.cells:
                if cell.__class__.__name__ == "StateMemoryCell":
                    memory_cell = cell
                    break
            
            if not memory_cell:
                raise RuntimeError("未找到StateMemoryCell")
            
            # 测试构建主题知识库
            knowledge_topics = [
                {
                    "topic": "机器学习",
                    "facts": [
                        "机器学习是人工智能的一个分支",
                        "监督学习需要标注数据",
                        "深度学习使用多层神经网络"
                    ]
                },
                {
                    "topic": "Python编程",
                    "facts": [
                        "Python是一种解释型语言",
                        "Python支持面向对象编程",
                        "Python有丰富的第三方库"
                    ]
                }
            ]
            
            kb_building_results = []
            
            for topic_data in knowledge_topics:
                topic = topic_data["topic"]
                facts = topic_data["facts"]
                
                try:
                    # 批量存储知识点
                    stored_count = 0
                    for fact in facts:
                        store_result = memory_cell.store(
                            content=fact,
                            metadata={"type": "knowledge", "topic": topic},
                            context=f"{topic}知识库"
                        )
                        if store_result.get("success", False):
                            stored_count += 1
                    
                    # 测试知识库查询
                    query_result = memory_cell.search_memories(
                        query=f"{topic}相关知识",
                        context=f"查询{topic}知识库",
                        limit=10
                    )
                    
                    retrieved_count = len(query_result.get("memories", []))
                    
                    kb_building_results.append({
                        "topic": topic,
                        "facts_stored": stored_count,
                        "total_facts": len(facts),
                        "retrieved_count": retrieved_count,
                        "storage_rate": stored_count / len(facts)
                    })
                    
                    print(f"   📚 {topic}: 存储{stored_count}/{len(facts)}, 检索到{retrieved_count}条")
                    
                except Exception as e:
                    print(f"   ❌ {topic}: 知识库构建失败 - {e}")
                    kb_building_results.append({
                        "topic": topic,
                        "error": str(e),
                        "storage_rate": 0.0
                    })
            
            # 计算知识库构建效果
            valid_results = [r for r in kb_building_results if "error" not in r]
            if valid_results:
                avg_storage_rate = sum(r["storage_rate"] for r in valid_results) / len(valid_results)
                total_stored = sum(r["facts_stored"] for r in valid_results)
                total_facts = sum(r["total_facts"] for r in valid_results)
                
                print(f"   📊 平均存储率: {avg_storage_rate*100:.1f}%")
                print(f"   📝 总计存储: {total_stored}/{total_facts}条知识")
                
                # 验证知识库构建效果
                expected_rate = self.test_config.success_criteria["knowledge_accumulation"]
                assert_success_rate(avg_storage_rate, expected_rate, "知识库构建能力")
                
                result.mark_success({
                    "avg_storage_rate": avg_storage_rate,
                    "total_facts_stored": total_stored,
                    "total_facts": total_facts,
                    "topics_processed": len(valid_results)
                })
            else:
                raise AssertionError("所有知识库构建都失败了")


async def main():
    """主函数"""
    
    # 创建并运行Level 3测试
    level3_test = Level3MemoryTest()
    
    try:
        success = await level3_test.run_all_tests()
        
        if success:
            print("\n🎉 Level 3 测试完全通过！")
            print("✅ 知识记忆能力验证成功")
            print("✅ 可以进入 Level 4 测试")
            return True
        else:
            print("\n❌ Level 3 测试未完全通过")
            print("🔧 请修复问题后重新测试")
            return False
            
    except Exception as e:
        print(f"\n💥 Level 3 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    print("🌱 FuturEmbryo v2.1c 渐进式测试")
    print("🧠 Level 3: 知识记忆能力测试")
    print("=" * 60)
    
    success = asyncio.run(main())
    
    end_time = time.time()
    print(f"\n⏱️  总耗时: {end_time - start_time:.2f}秒")
    
    if success:
        print("🚀 Level 3 通过，准备进入 Level 4！")
        exit(0)
    else:
        print("❌ Level 3 失败，需要修复问题")
        exit(1)