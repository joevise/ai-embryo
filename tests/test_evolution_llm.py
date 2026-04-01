"""
AI Embryo Engine — LLM Evolution 测试

覆盖: LLM 驱动的进化引擎（使用 Mock LLM）
"""

import os
import sys
import tempfile
import shutil
import asyncio
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_embryo.organism_package import OrganismPackage
from ai_embryo.evolution_llm import MockLLMEvolutionEngine


class TestMockLLMEvolution:
    """测试 Mock LLM 进化引擎"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = MockLLMEvolutionEngine()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_mock_crossover(self):
        """测试 Mock 交叉"""
        parent_a = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "parent_a",
            name="ParentA",
            purpose="父代A",
            persona_config={"type": "analytical"},
        )

        parent_b = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "parent_b",
            name="ParentB",
            purpose="父代B",
            persona_config={"type": "creative"},
        )

        child = asyncio.run(self.engine.crossover(parent_a, parent_b))

        assert child is not None
        assert child.name == "ParentAxParentB"
        assert child.parent_a == "ParentA"
        assert child.parent_b == "ParentB"
        assert child.generation == 2

    def test_mock_mutate(self):
        """测试 Mock 变异"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "to_mutate",
            name="ToMutate",
            purpose="待变异",
            persona_config={"type": "analytical"},
        )

        result = asyncio.run(self.engine.mutate(pkg, feedback="回答太浅了"))

        assert result is not None
        assert "improvements" in result
        assert "soul_change" in result
        assert "mind_change" in result
        assert "values_change" in result

    def test_mock_mutate_with_feedback(self):
        """测试带反馈的变异"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "feedback_mutate",
            name="FeedbackMutate",
            purpose="带反馈变异",
            persona_config={"type": "executive"},
        )

        result = asyncio.run(self.engine.mutate(pkg, feedback="决策太快了，需要更谨慎"))

        assert result is not None
        assert "improvements" in result

    def test_mock_reflect(self):
        """测试 Mock 反思"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "to_reflect",
            name="ToReflect",
            purpose="待反思",
            persona_config={"type": "analytical"},
        )

        conversation = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，有什么可以帮助你的？"},
            {"role": "user", "content": "什么是量子计算？"},
            {
                "role": "assistant",
                "content": "量子计算是一种基于量子力学原理的计算方式...",
            },
        ]

        result = asyncio.run(self.engine.reflect(pkg, conversation))

        assert result is not None
        assert "strengths" in result
        assert "weaknesses" in result
        assert "mind_updates" in result
        assert "memory_update" in result
        assert "fitness_self_score" in result

    def test_mock_reflect_with_feedback(self):
        """测试带反馈的反思"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "feedback_reflect",
            name="FeedbackReflect",
            purpose="带反馈反思",
            persona_config={"type": "creative"},
        )

        conversation = [
            {"role": "user", "content": "给我一个产品创意"},
            {"role": "assistant", "content": "我有一个关于智能家居的创意..."},
        ]

        result = asyncio.run(self.engine.reflect(pkg, conversation, feedback="创意不够新颖"))

        assert result is not None
        assert "strengths" in result
        assert "weaknesses" in result

    def test_mock_reflect_empty_conversation(self):
        """测试空对话的反思"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "empty_reflect",
            name="EmptyReflect",
            purpose="空对话反思",
            persona_config={"type": "analytical"},
        )

        result = asyncio.run(self.engine.reflect(pkg, []))

        assert result is not None
        assert "strengths" in result
        assert "memory_update" in result


class TestCrossoverLineage:
    """测试交叉后的族谱信息"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = MockLLMEvolutionEngine()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_child_has_correct_generation(self):
        """测试子代代数正确"""
        parent_a = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "pa",
            name="ParentA",
            purpose="父代A",
            persona_config={"type": "analytical"},
        )
        parent_a.generation = 3

        parent_b = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "pb",
            name="ParentB",
            purpose="父代B",
            persona_config={"type": "creative"},
        )
        parent_b.generation = 5

        child = asyncio.run(self.engine.crossover(parent_a, parent_b))

        assert child.generation == 6

    def test_child_has_both_parents(self):
        """测试子代有双方父代"""
        parent_a = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "pa2",
            name="Alpha",
            purpose="父代Alpha",
            persona_config={"type": "analytical"},
        )

        parent_b = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "pb2",
            name="Beta",
            purpose="父代Beta",
            persona_config={"type": "creative"},
        )

        child = asyncio.run(self.engine.crossover(parent_a, parent_b))

        assert child.parent_a == "Alpha"
        assert child.parent_b == "Beta"


class TestMutation:
    """测试变异功能"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = MockLLMEvolutionEngine()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_mutate_returns_dict(self):
        """测试变异返回字典"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "mut1",
            name="Mut1",
            purpose="变异测试",
            persona_config={"type": "executive"},
        )

        result = asyncio.run(self.engine.mutate(pkg))

        assert isinstance(result, dict)
        assert "improvements" in result

    def test_mutate_with_empty_feedback(self):
        """测试无反馈变异"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "mut2",
            name="Mut2",
            purpose="无反馈变异",
            persona_config={"type": "analytical"},
        )

        result = asyncio.run(self.engine.mutate(pkg))

        assert isinstance(result, dict)
        assert result["improvements"] is not None


class TestReflection:
    """测试反思功能"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = MockLLMEvolutionEngine()

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_reflect_conversation_format(self):
        """测试对话格式"""
        pkg = OrganismPackage.create(
            base_dir=Path(self.temp_dir) / "ref1",
            name="Ref1",
            purpose="反思测试",
            persona_config={"type": "creative"},
        )

        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "Tell me about AI"},
            {"role": "assistant", "content": "AI is artificial intelligence..."},
        ]

        result = asyncio.run(self.engine.reflect(pkg, conversation))

        assert "strengths" in result
        assert "weaknesses" in result
        assert "memory_update" in result
        assert 0 <= result["fitness_self_score"] <= 1


def run_tests():
    """运行所有测试"""
    import traceback

    test_classes = [
        TestMockLLMEvolution,
        TestCrossoverLineage,
        TestMutation,
        TestReflection,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{'=' * 60}")
        print(f"🧪 {test_class.__name__}")
        print(f"{'=' * 60}")

        instance = test_class()
        setup_method = getattr(instance, "setup_method", None)
        teardown_method = getattr(instance, "teardown_method", None)

        for method_name in dir(instance):
            if not method_name.startswith("test_"):
                continue

            if setup_method:
                try:
                    setup_method()
                except Exception as e:
                    print(f"  ⚠️ Setup failed: {e}")
                    continue

            try:
                getattr(instance, method_name)()
                print(f"  ✅ {method_name}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {method_name}: {e}")
                traceback.print_exc()
                failed += 1
            finally:
                if teardown_method:
                    try:
                        teardown_method()
                    except Exception:
                        pass

    print(f"\n{'=' * 60}")
    print(f"📊 结果: {passed} 通过, {failed} 失败, 共 {passed + failed} 测试")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
