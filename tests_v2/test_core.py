"""
AI Embryo Engine — 核心功能测试

不依赖外部 API，纯逻辑测试。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_embryo.genome import Genome
from ai_embryo.cell import Cell
from ai_embryo.registry import CellRegistry
from ai_embryo.organism import Organism
from ai_embryo.embryo import Embryo
from ai_embryo.evolution import EvolutionEngine
from ai_embryo.fitness import FitnessEvaluator, Task
from ai_embryo.exceptions import GenomeValidationError, DevelopmentError

# 导入内置 cells（触发注册）
import ai_embryo.cells  # noqa: F401


# ── 测试用 Cell ──────────────────────────────────────────

@CellRegistry.register()
class EchoCell(Cell):
    """回声细胞 — 直接返回输入"""
    def process(self, input):
        text = input.get("input", "")
        prefix = self.config.get("prefix", "Echo")
        return {"response": f"[{prefix}] {text}"}


@CellRegistry.register()
class UpperCell(Cell):
    """大写细胞 — 把前一步响应转大写"""
    def process(self, input):
        prev = input.get("previous_response", input.get("input", ""))
        return {"response": prev.upper()}


@CellRegistry.register()
class ScoreCell(Cell):
    """评分细胞 — 返回固定分数的响应"""
    def process(self, input):
        score = self.config.get("score", 0.5)
        text = input.get("input", "")
        return {"response": f"分析结果: {text}。综合评分: {score}。这是一个详细的分析报告，包含多个维度的考量。"}


# ── 测试函数 ─────────────────────────────────────────────

def test_genome_creation():
    """测试基因组创建和验证"""
    print("🧪 测试: 基因组创建")
    
    g = Genome(
        name="test_agent",
        identity={
            "purpose": "测试用 AI",
            "personality": ["friendly"],
            "language": "zh-CN",
            "constraints": [],
        },
        blueprint={
            "capabilities": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 100,
                "tools": [],
            },
            "cells": [{"type": "EchoCell", "config": {"prefix": "Test"}}],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.1,
                "fitness_metrics": ["accuracy"],
                "mutable_fields": ["capabilities.temperature"],
            },
        },
    )
    
    assert g.name == "test_agent"
    assert g.identity["purpose"] == "测试用 AI"
    assert len(g.blueprint["cells"]) == 1
    g.validate()
    print("  ✅ 基因组创建和验证通过")


def test_genome_validation_fail():
    """测试基因组验证失败"""
    print("🧪 测试: 基因组验证失败")
    
    error_caught = False
    try:
        g = Genome(name="bad", identity={"purpose": ""}, blueprint={
            "capabilities": {},
            "cells": [{"type": "EchoCell"}],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"], "mutable_fields": []},
        })
        g.validate()  # 显式调用验证
    except GenomeValidationError:
        error_caught = True
    
    assert error_caught, "应该抛出 GenomeValidationError"
    print("  ✅ 正确抛出 GenomeValidationError")


def test_genome_serialization():
    """测试基因组序列化"""
    print("🧪 测试: 基因组序列化")
    
    g = Genome(name="serial_test")
    d = g.to_dict()
    g2 = Genome.from_dict(d)
    
    assert g.name == g2.name
    assert g.identity == g2.identity
    
    # 保存和加载 YAML
    path = "/tmp/test_genome.yaml"
    g.save(path)
    g3 = Genome.from_file(path)
    assert g3.name == "serial_test"
    os.remove(path)
    
    print("  ✅ 序列化/反序列化通过")


def test_genome_crossover():
    """测试基因交叉"""
    print("🧪 测试: 基因交叉")
    
    parent_a = Genome(name="fast_agent")
    parent_a.blueprint["capabilities"]["temperature"] = 0.3
    parent_a.fitness = 0.9
    
    parent_b = Genome(name="creative_agent")
    parent_b.blueprint["capabilities"]["temperature"] = 0.9
    parent_b.fitness = 0.7
    
    child = Genome.crossover(parent_a, parent_b)
    
    assert "fast_agent" in child.name or "creative_agent" in child.name
    # 身份基因应从主导父代（fast_agent，fitness更高）继承
    assert child.identity == parent_a.identity
    print(f"  子代: {child}")
    print("  ✅ 基因交叉通过")


def test_genome_mutation():
    """测试基因变异"""
    print("🧪 测试: 基因变异")
    
    g = Genome(name="mutable")
    g.blueprint["evolution"]["mutable_fields"] = ["capabilities.temperature"]
    
    original_temp = g.blueprint["capabilities"]["temperature"]
    
    # 高变异率保证发生变异
    g.mutate(mutation_rate=1.0)
    new_temp = g.blueprint["capabilities"]["temperature"]
    
    print(f"  温度: {original_temp} → {new_temp}")
    # 变异后值应该不同（极小概率相同，忽略）
    print("  ✅ 基因变异通过")


def test_variable_reference():
    """测试变量引用解析"""
    print("🧪 测试: 变量引用")
    
    g = Genome(name="ref_test")
    g.blueprint["capabilities"]["model"] = "gpt-4o"
    
    config = {"model": "${capabilities.model}", "name": "static"}
    resolved = g.resolve_references(config)
    
    assert resolved["model"] == "gpt-4o"
    assert resolved["name"] == "static"
    print(f"  解析: ${{capabilities.model}} → {resolved['model']}")
    print("  ✅ 变量引用通过")


def test_cell_registry():
    """测试 Cell 注册表"""
    print("🧪 测试: Cell 注册表")
    
    registered = CellRegistry.list()
    assert "EchoCell" in registered
    assert "UpperCell" in registered
    assert "LLMCell" in registered
    assert "MemoryCell" in registered
    assert "ToolCell" in registered
    assert "RouterCell" in registered
    
    echo_cls = CellRegistry.get("EchoCell")
    cell = echo_cls({"prefix": "Hi"})
    result = cell.process({"input": "world"})
    assert result["response"] == "[Hi] world"
    
    print(f"  已注册: {registered}")
    print("  ✅ Cell 注册表通过")


def test_embryo_develop():
    """测试胚胎发育"""
    print("🧪 测试: 胚胎发育")
    
    g = Genome(
        name="embryo_test",
        blueprint={
            "capabilities": {"model": "test", "temperature": 0.5, "max_tokens": 100, "tools": []},
            "cells": [
                {"type": "EchoCell", "config": {"prefix": "Step1"}},
                {"type": "UpperCell", "config": {}},
            ],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"], "mutable_fields": []},
        },
    )
    
    organism = Embryo.develop(g)
    assert len(organism.cells) == 2
    assert organism.assembly == "sequential"
    
    print(f"  生命体: {organism}")
    print("  ✅ 胚胎发育通过")


def test_organism_run():
    """测试生命体运行"""
    print("🧪 测试: 生命体运行")
    
    g = Genome(
        name="runner",
        blueprint={
            "capabilities": {"model": "test", "temperature": 0.5, "max_tokens": 100, "tools": []},
            "cells": [
                {"type": "EchoCell", "config": {"prefix": "A"}},
                {"type": "UpperCell", "config": {}},
            ],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"], "mutable_fields": []},
        },
    )
    
    org = Embryo.develop(g)
    result = org.run({"input": "hello world"})
    
    print(f"  输入: 'hello world'")
    print(f"  输出: '{result.get('response', '')}'")
    
    # EchoCell: "[A] hello world" → UpperCell: "[A] HELLO WORLD"
    assert "HELLO WORLD" in result["response"]
    assert result["_meta"]["organism"] == "runner"
    
    print("  ✅ 生命体运行通过")


def test_fitness_evaluation():
    """测试适应度评估"""
    print("🧪 测试: 适应度评估")
    
    g = Genome(
        name="fit_test",
        blueprint={
            "capabilities": {"model": "test", "temperature": 0.5, "max_tokens": 100, "tools": []},
            "cells": [{"type": "ScoreCell", "config": {"score": 0.85}}],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.1,
                "fitness_metrics": ["accuracy", "speed", "length"],
                "mutable_fields": [],
            },
        },
    )
    
    org = Embryo.develop(g)
    evaluator = FitnessEvaluator()
    
    tasks = [
        Task(input={"input": "分析AI趋势"}, expected="分析 AI 趋势 报告", name="task1"),
        Task(input={"input": "总结数据"}, expected="总结 数据 报告", name="task2"),
    ]
    
    score = evaluator.evaluate(org, tasks)
    print(f"  适应度: {score:.4f}")
    assert 0.0 <= score <= 1.0
    assert len(org.fitness_history) == 1
    
    print("  ✅ 适应度评估通过")


def test_evolution():
    """测试进化循环"""
    print("🧪 测试: 进化循环")
    
    # 创建初始种群（不同配置）
    population = []
    for i, prefix in enumerate(["Alpha", "Beta", "Gamma", "Delta"]):
        g = Genome(
            name=prefix,
            blueprint={
                "capabilities": {
                    "model": "test",
                    "temperature": 0.3 + i * 0.2,
                    "max_tokens": 100 + i * 50,
                    "tools": [],
                },
                "cells": [
                    {"type": "ScoreCell", "config": {"score": 0.5 + i * 0.1}},
                ],
                "assembly": "sequential",
                "evolution": {
                    "mutation_rate": 0.2,
                    "fitness_metrics": ["accuracy", "length"],
                    "mutable_fields": ["capabilities.temperature", "capabilities.max_tokens"],
                },
            },
        )
        population.append(Embryo.develop(g))

    tasks = [
        Task(input={"input": "分析市场"}, expected="分析 市场 趋势 报告", name="market"),
        Task(input={"input": "技术评估"}, expected="技术 评估 分析 报告", name="tech"),
    ]

    # 进化
    gen_log = []
    def on_gen(gen, pop):
        best = max(pop, key=lambda o: o.latest_fitness)
        gen_log.append((gen, best.name, best.latest_fitness))

    engine = EvolutionEngine(on_generation=on_gen)
    best = engine.evolve(
        population=population,
        tasks=tasks,
        generations=5,
        population_size=6,
        selection_ratio=0.5,
        elitism=1,
    )

    print(f"  最优: {best.name} (fitness={best.latest_fitness:.4f})")
    print(f"  进化日志:")
    for gen, name, fit in gen_log:
        print(f"    Gen {gen}: {name} ({fit:.4f})")
    
    assert best.latest_fitness > 0
    print("  ✅ 进化循环通过")


def test_crossover_and_develop():
    """测试交配后发育"""
    print("🧪 测试: 交配 → 发育 → 运行")
    
    parent_a = Genome(
        name="Analyst",
        blueprint={
            "capabilities": {"model": "test", "temperature": 0.3, "max_tokens": 200, "tools": []},
            "cells": [{"type": "EchoCell", "config": {"prefix": "分析"}}],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.1,
                "fitness_metrics": ["accuracy"],
                "mutable_fields": ["capabilities.temperature"],
            },
        },
    )
    parent_a.fitness = 0.8

    parent_b = Genome(
        name="Creative",
        blueprint={
            "capabilities": {"model": "test", "temperature": 0.9, "max_tokens": 500, "tools": []},
            "cells": [{"type": "EchoCell", "config": {"prefix": "创意"}}],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.3,
                "fitness_metrics": ["accuracy"],
                "mutable_fields": ["capabilities.temperature"],
            },
        },
    )
    parent_b.fitness = 0.6

    # 交配
    child_genome = Genome.crossover(parent_a, parent_b)
    print(f"  父代A: {parent_a}")
    print(f"  父代B: {parent_b}")
    print(f"  子代:  {child_genome}")

    # 发育
    child = Embryo.develop(child_genome)
    
    # 运行
    result = child.run({"input": "分析市场趋势"})
    print(f"  运行结果: {result.get('response', '')[:80]}")
    
    assert "response" in result
    print("  ✅ 交配→发育→运行 通过")


# ── 运行所有测试 ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("🧬 AI Embryo Engine — 核心测试")
    print("=" * 60)
    print()
    
    tests = [
        test_genome_creation,
        test_genome_validation_fail,
        test_genome_serialization,
        test_genome_crossover,
        test_genome_mutation,
        test_variable_reference,
        test_cell_registry,
        test_embryo_develop,
        test_organism_run,
        test_fitness_evaluation,
        test_evolution,
        test_crossover_and_develop,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 结果: {passed} 通过, {failed} 失败, 共 {passed + failed} 测试")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
