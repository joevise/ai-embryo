"""
AI Embryo Engine — 核心功能测试 v2

覆盖：Genome(mind+traits) / Cell / Embryo / Organism / Fitness / Evolution
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
    """回声细胞"""
    def process(self, input):
        text = input.get("input", "")
        prefix = self.config.get("prefix", "Echo")
        return {"response": f"[{prefix}] {text}"}


@CellRegistry.register()
class UpperCell(Cell):
    """大写细胞"""
    def process(self, input):
        prev = input.get("previous_response", input.get("input", ""))
        return {"response": prev.upper()}


@CellRegistry.register()
class ScoreCell(Cell):
    """评分细胞"""
    def process(self, input):
        score = self.config.get("score", 0.5)
        text = input.get("input", "")
        return {"response": f"分析结果: {text}。综合评分: {score}。这是一个详细的分析报告，包含多个维度的考量。"}


# ── 测试函数 ─────────────────────────────────────────────

def test_genome_with_mind():
    """测试带 mind 的基因组"""
    print("🧪 测试: 带 mind 的基因组")
    
    g = Genome(
        name="thinker",
        identity={
            "purpose": "提供深度技术分析",
            "constraints": ["保护隐私"],
            "mind": {
                "cognition": {
                    "thinking_style": "analytical",
                    "reasoning": "first_principles",
                    "depth": "deep",
                    "metacognition": {
                        "self_awareness": True,
                        "thinking_transparency": "on_demand",
                        "calibration": True,
                    },
                },
                "judgment": {
                    "decision_style": "decisive",
                    "risk_tolerance": "balanced",
                    "uncertainty": "acknowledge",
                    "priorities": ["accuracy", "actionability"],
                },
                "voice": {
                    "tone": "sharp",
                    "directness": "direct",
                    "verbosity": "concise",
                    "emotion": "restrained",
                },
                "character": {
                    "values": ["honesty", "curiosity", "pragmatism"],
                    "temperament": "calm",
                    "quirks": ["喜欢先给结论再说理由", "遇到模糊问题会主动追问"],
                    "worldview": "realistic",
                },
            },
        },
    )
    
    g.validate()
    
    # 验证 mind 结构
    mind = g.identity["mind"]
    assert mind["cognition"]["thinking_style"] == "analytical"
    assert mind["judgment"]["decision_style"] == "decisive"
    assert mind["voice"]["tone"] == "sharp"
    assert "honesty" in mind["character"]["values"]
    assert len(mind["character"]["quirks"]) == 2
    
    print(f"  mind.cognition.thinking_style = {mind['cognition']['thinking_style']}")
    print(f"  mind.voice.tone = {mind['voice']['tone']}")
    print(f"  mind.character.quirks = {mind['character']['quirks']}")
    print("  ✅ 带 mind 的基因组通过")


def test_compile_system_prompt():
    """测试从 mind + traits 编译系统提示词"""
    print("🧪 测试: 编译系统提示词")
    
    g = Genome(
        name="prompt_test",
        identity={
            "purpose": "技术分析和战略建议",
            "constraints": ["不提供投资建议"],
            "mind": {
                "cognition": {
                    "thinking_style": "systematic",
                    "reasoning": "first_principles",
                    "depth": "deep",
                },
                "judgment": {
                    "decision_style": "decisive",
                    "uncertainty": "acknowledge",
                    "priorities": ["accuracy", "speed"],
                },
                "voice": {
                    "tone": "sharp",
                    "directness": "direct",
                    "verbosity": "concise",
                },
                "character": {
                    "values": ["honesty"],
                    "temperament": "calm",
                    "quirks": ["喜欢用反问来引导思考"],
                    "worldview": "realistic",
                },
            },
        },
        blueprint={
            "model_config": {"model": "test", "temperature": 0.7, "max_tokens": 100},
            "traits": [
                {
                    "id": "style_concise",
                    "type": "prompt:style",
                    "name": "简洁风格",
                    "content": "回答简洁有力，先给结论再说理由。",
                    "weight": 0.8,
                },
                {
                    "id": "knowledge_ai",
                    "type": "prompt:knowledge",
                    "name": "AI领域知识",
                    "content": "你对大语言模型和 AI Agent 框架有深入了解。",
                    "weight": 0.6,
                },
            ],
            "cells": [{"type": "EchoCell", "config": {}}],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"],
                          "trait_evolution": {"mutable_types": ["prompt:style"], "immutable_types": ["prompt:role"]}},
        },
    )
    
    prompt = g.compile_system_prompt()
    
    # 验证 mind 部分被编译
    assert "系统型" in prompt, f"应包含思维风格，got: {prompt[:200]}"
    assert "果断" in prompt, f"应包含决策风格"
    assert "犀利" in prompt, f"应包含语气"
    assert "诚实" in prompt or "honesty" in prompt, f"应包含价值观"
    
    # 验证 identity 基础字段
    assert "技术分析" in prompt
    assert "投资建议" in prompt
    
    # 验证 traits 被编译
    assert "简洁风格" in prompt
    assert "AI领域知识" in prompt or "AI Agent" in prompt
    
    print(f"  提示词长度: {len(prompt)} 字符")
    print(f"  前200字: {prompt[:200]}...")
    print("  ✅ 编译系统提示词通过")


def test_traits_operations():
    """测试 trait 操作"""
    print("🧪 测试: Trait 操作")
    
    g = Genome(name="trait_test")
    g.blueprint["traits"] = [
        {"id": "t1", "type": "prompt:role", "name": "角色", "content": "你是分析师"},
        {"id": "t2", "type": "prompt:style", "name": "风格", "content": "简洁", "weight": 0.8},
        {"id": "t3", "type": "tool:function", "name": "搜索", "config": {"function_name": "search"}},
        {"id": "t4", "type": "tool:function", "name": "计算", "config": {"function_name": "calc"}},
        {"id": "t5", "type": "tool:mcp", "name": "文件MCP", "config": {"command": "npx"}},
        {"id": "t6", "type": "skill", "name": "代码审查", "config": {"path": "skills/review"}},
        {"id": "t7", "type": "behavior:guard", "name": "隐私", "config": {"rules": ["不泄露"]}},
    ]
    
    # 按类型过滤
    prompt_traits = g.get_traits("prompt:*")
    assert len(prompt_traits) == 2
    
    tool_fn = g.get_traits("tool:function")
    assert len(tool_fn) == 2
    
    tool_all = g.get_traits("tool:*")
    assert len(tool_all) == 3  # 2 function + 1 mcp
    
    # 按 id 获取
    t3 = g.get_trait_by_id("t3")
    assert t3["name"] == "搜索"
    
    # 编译工具
    tools = g.compile_tools()
    assert len(tools) == 2
    assert tools[0]["function"]["name"] == "search"
    
    print(f"  prompt traits: {len(prompt_traits)}")
    print(f"  tool:function: {len(tool_fn)}")
    print(f"  tool:* (含MCP): {len(tool_all)}")
    print(f"  compiled tools: {len(tools)}")
    print("  ✅ Trait 操作通过")


def test_trait_crossover():
    """测试 trait 级别的交叉"""
    print("🧪 测试: Trait 级别交叉")
    
    parent_a = Genome(
        name="Analyst",
        identity={
            "purpose": "技术分析",
            "constraints": [],
            "mind": {
                "voice": {"tone": "sharp", "verbosity": "concise"},
                "character": {"values": ["honesty"], "quirks": ["爱用数据说话"]},
            },
        },
        blueprint={
            "model_config": {"model": "gpt-4", "temperature": 0.3, "max_tokens": 200},
            "traits": [
                {"id": "role_analyst", "type": "prompt:role", "name": "分析师", "content": "你是分析师"},
                {"id": "style_concise", "type": "prompt:style", "name": "简洁", "content": "简洁回答"},
                {"id": "tool_search", "type": "tool:function", "name": "搜索", "config": {"function_name": "search"}},
                {"id": "tool_calc", "type": "tool:function", "name": "计算", "config": {"function_name": "calc"}},
                {"id": "guard_privacy", "type": "behavior:guard", "name": "隐私", "config": {}},
            ],
            "cells": [{"type": "EchoCell", "config": {}}],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.1,
                "fitness_metrics": ["accuracy"],
                "trait_evolution": {
                    "mutable_types": ["prompt:style", "tool:function", "skill"],
                    "immutable_types": ["prompt:role", "behavior:guard"],
                },
            },
        },
    )
    parent_a.fitness = 0.9

    parent_b = Genome(
        name="Creative",
        identity={
            "purpose": "创意内容",
            "constraints": [],
            "mind": {
                "voice": {"tone": "warm", "verbosity": "thorough"},
                "character": {"values": ["creativity"], "quirks": ["喜欢用比喻"]},
            },
        },
        blueprint={
            "model_config": {"model": "gpt-4o", "temperature": 0.9, "max_tokens": 500},
            "traits": [
                {"id": "role_creative", "type": "prompt:role", "name": "创意师", "content": "你是创意师"},
                {"id": "style_detailed", "type": "prompt:style", "name": "详细", "content": "详细回答"},
                {"id": "tool_search", "type": "tool:function", "name": "搜索", "config": {"function_name": "search"}},
                {"id": "skill_writing", "type": "skill", "name": "写作", "config": {"path": "skills/writing"}},
            ],
            "cells": [{"type": "EchoCell", "config": {}}],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.1,
                "fitness_metrics": ["accuracy"],
                "trait_evolution": {
                    "mutable_types": ["prompt:style", "tool:function", "skill"],
                    "immutable_types": ["prompt:role", "behavior:guard"],
                },
            },
        },
    )
    parent_b.fitness = 0.7

    child = Genome.crossover(parent_a, parent_b)
    
    # 身份基因从主导父代（A）继承
    assert child.identity["purpose"] == "技术分析"
    
    # prompt:role 是 immutable，应从主导父代
    child_roles = child.get_traits("prompt:role")
    assert len(child_roles) == 1
    assert child_roles[0]["id"] == "role_analyst"
    
    # behavior:guard 是 immutable，应从主导父代
    child_guards = child.get_traits("behavior:guard")
    assert len(child_guards) == 1
    
    # tool_search 两边都有（同 id），应保留
    child_tools = child.get_traits("tool:function")
    tool_ids = [t["id"] for t in child_tools]
    assert "tool_search" in tool_ids
    
    # 输出子代 traits
    child_all = child.get_traits()
    print(f"  父代A traits: {[t['id'] for t in parent_a.blueprint['traits']]}")
    print(f"  父代B traits: {[t['id'] for t in parent_b.blueprint['traits']]}")
    print(f"  子代 traits:  {[t.get('id', '?') for t in child_all]}")
    print(f"  子代 identity.purpose = {child.identity['purpose']}")
    
    # 检查 mind voice 可能有混入
    child_voice = child.identity.get("mind", {}).get("voice", {})
    print(f"  子代 voice.tone = {child_voice.get('tone', '?')}")
    
    print("  ✅ Trait 级别交叉通过")


def test_mind_inheritance():
    """测试 mind 在交叉中的继承"""
    print("🧪 测试: Mind 继承")
    
    # 运行多次交叉，验证 mind 主体从主导父代继承
    parent_a = Genome(name="A", identity={
        "purpose": "分析",
        "mind": {
            "cognition": {"thinking_style": "analytical", "depth": "deep"},
            "judgment": {"decision_style": "decisive"},
            "voice": {"tone": "sharp"},
            "character": {"values": ["honesty"], "quirks": ["爱追问"]},
        },
    })
    parent_a.fitness = 0.9

    parent_b = Genome(name="B", identity={
        "purpose": "创意",
        "mind": {
            "cognition": {"thinking_style": "creative", "depth": "surface"},
            "judgment": {"decision_style": "collaborative"},
            "voice": {"tone": "warm"},
            "character": {"values": ["creativity"], "quirks": ["爱用比喻"]},
        },
    })
    parent_b.fitness = 0.5

    # 多次交叉，核心认知应始终从 A 继承
    for i in range(10):
        child = Genome.crossover(parent_a, parent_b)
        child_mind = child.identity.get("mind", {})
        # 认知和决策从主导父代继承（不会变）
        assert child_mind["cognition"]["thinking_style"] == "analytical", \
            f"Round {i}: thinking_style should be analytical"
        assert child_mind["judgment"]["decision_style"] == "decisive", \
            f"Round {i}: decision_style should be decisive"
    
    print("  10次交叉中，cognition/judgment 始终从主导父代继承 ✓")
    print("  ✅ Mind 继承通过")


def test_genome_creation():
    """测试基因组创建和验证"""
    print("🧪 测试: 基因组创建")
    g = Genome(
        name="test_agent",
        identity={
            "purpose": "测试用 AI",
            "constraints": [],
            "mind": {"voice": {"tone": "warm"}},
        },
        blueprint={
            "model_config": {"model": "gpt-4", "temperature": 0.7, "max_tokens": 100},
            "traits": [{"id": "t1", "type": "prompt:style", "name": "test", "content": "be nice"}],
            "cells": [{"type": "EchoCell", "config": {"prefix": "Test"}}],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"],
                          "trait_evolution": {"mutable_types": [], "immutable_types": []}},
        },
    )
    g.validate()
    assert g.name == "test_agent"
    assert len(g.blueprint["traits"]) == 1
    print("  ✅ 基因组创建和验证通过")


def test_genome_validation_fail():
    """测试基因组验证失败"""
    print("🧪 测试: 基因组验证失败")
    g = Genome(name="bad", identity={"purpose": ""})
    error_caught = False
    try:
        g.validate()
    except GenomeValidationError:
        error_caught = True
    assert error_caught
    print("  ✅ 正确抛出 GenomeValidationError")


def test_genome_serialization():
    """测试基因组序列化"""
    print("🧪 测试: 基因组序列化")
    g = Genome(name="serial_test")
    d = g.to_dict()
    g2 = Genome.from_dict(d)
    assert g.name == g2.name
    assert g.identity["mind"]["cognition"]["thinking_style"] == g2.identity["mind"]["cognition"]["thinking_style"]
    
    path = "/tmp/test_genome_v2.yaml"
    g.save(path)
    g3 = Genome.from_file(path)
    assert g3.name == "serial_test"
    assert "mind" in g3.identity
    os.remove(path)
    print("  ✅ 序列化/反序列化通过（含 mind）")


def test_genome_mutation():
    """测试基因变异"""
    print("🧪 测试: 基因变异")
    g = Genome(name="mutable")
    original_temp = g.blueprint["model_config"]["temperature"]
    g.mutate(mutation_rate=1.0)
    new_temp = g.blueprint["model_config"]["temperature"]
    print(f"  温度: {original_temp} → {new_temp}")
    print("  ✅ 基因变异通过")


def test_cell_registry():
    """测试 Cell 注册表"""
    print("🧪 测试: Cell 注册表")
    registered = CellRegistry.list()
    assert "EchoCell" in registered
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
            "model_config": {"model": "test", "temperature": 0.5, "max_tokens": 100},
            "traits": [],
            "cells": [
                {"type": "EchoCell", "config": {"prefix": "Step1"}},
                {"type": "UpperCell", "config": {}},
            ],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"],
                          "trait_evolution": {"mutable_types": [], "immutable_types": []}},
        },
    )
    organism = Embryo.develop(g)
    assert len(organism.cells) == 2
    print(f"  生命体: {organism}")
    print("  ✅ 胚胎发育通过")


def test_organism_run():
    """测试生命体运行"""
    print("🧪 测试: 生命体运行")
    g = Genome(
        name="runner",
        blueprint={
            "model_config": {"model": "test", "temperature": 0.5, "max_tokens": 100},
            "traits": [],
            "cells": [
                {"type": "EchoCell", "config": {"prefix": "A"}},
                {"type": "UpperCell", "config": {}},
            ],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"],
                          "trait_evolution": {"mutable_types": [], "immutable_types": []}},
        },
    )
    org = Embryo.develop(g)
    result = org.run({"input": "hello world"})
    assert "HELLO WORLD" in result["response"]
    print(f"  输入: 'hello world' → 输出: '{result['response']}'")
    print("  ✅ 生命体运行通过")


def test_fitness_evaluation():
    """测试适应度评估"""
    print("🧪 测试: 适应度评估")
    g = Genome(
        name="fit_test",
        blueprint={
            "model_config": {"model": "test", "temperature": 0.5, "max_tokens": 100},
            "traits": [],
            "cells": [{"type": "ScoreCell", "config": {"score": 0.85}}],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy", "speed", "length"],
                          "trait_evolution": {"mutable_types": [], "immutable_types": []}},
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
    print("  ✅ 适应度评估通过")


def test_evolution():
    """测试进化循环"""
    print("🧪 测试: 进化循环")
    population = []
    for i, name in enumerate(["Alpha", "Beta", "Gamma", "Delta"]):
        g = Genome(
            name=name,
            blueprint={
                "model_config": {"model": "test", "temperature": 0.3 + i * 0.2, "max_tokens": 100 + i * 50},
                "traits": [
                    {"id": f"style_{name}", "type": "prompt:style", "name": f"{name}风格", "content": f"{name}的风格"},
                ],
                "cells": [{"type": "ScoreCell", "config": {"score": 0.5 + i * 0.1}}],
                "assembly": "sequential",
                "evolution": {
                    "mutation_rate": 0.2,
                    "fitness_metrics": ["accuracy", "length"],
                    "trait_evolution": {
                        "mutable_types": ["prompt:style"],
                        "immutable_types": ["prompt:role"],
                    },
                },
            },
        )
        population.append(Embryo.develop(g))

    tasks = [
        Task(input={"input": "分析市场"}, expected="分析 市场 趋势 报告", name="market"),
        Task(input={"input": "技术评估"}, expected="技术 评估 分析 报告", name="tech"),
    ]

    gen_log = []
    def on_gen(gen, pop):
        best = max(pop, key=lambda o: o.latest_fitness)
        gen_log.append((gen, best.name, best.latest_fitness))

    engine = EvolutionEngine(on_generation=on_gen)
    best = engine.evolve(population=population, tasks=tasks, generations=5, population_size=6)

    print(f"  最优: {best.name} (fitness={best.latest_fitness:.4f})")
    for gen, name, fit in gen_log:
        print(f"    Gen {gen}: {name} ({fit:.4f})")
    assert best.latest_fitness > 0
    print("  ✅ 进化循环通过")


def test_crossover_and_develop():
    """测试交配后发育"""
    print("🧪 测试: 交配 → 发育 → 运行")
    parent_a = Genome(
        name="Analyst",
        identity={"purpose": "分析", "constraints": [],
                  "mind": {"voice": {"tone": "sharp"}, "character": {"quirks": ["爱追问"]}}},
        blueprint={
            "model_config": {"model": "test", "temperature": 0.3, "max_tokens": 200},
            "traits": [{"id": "s1", "type": "prompt:style", "content": "简洁"}],
            "cells": [{"type": "EchoCell", "config": {"prefix": "分析"}}],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.1, "fitness_metrics": ["accuracy"],
                          "trait_evolution": {"mutable_types": ["prompt:style"], "immutable_types": []}},
        },
    )
    parent_a.fitness = 0.8

    parent_b = Genome(
        name="Creative",
        identity={"purpose": "创意", "constraints": [],
                  "mind": {"voice": {"tone": "warm"}, "character": {"quirks": ["爱用比喻"]}}},
        blueprint={
            "model_config": {"model": "test", "temperature": 0.9, "max_tokens": 500},
            "traits": [{"id": "s2", "type": "prompt:style", "content": "详细"}],
            "cells": [{"type": "EchoCell", "config": {"prefix": "创意"}}],
            "assembly": "sequential",
            "evolution": {"mutation_rate": 0.3, "fitness_metrics": ["accuracy"],
                          "trait_evolution": {"mutable_types": ["prompt:style"], "immutable_types": []}},
        },
    )
    parent_b.fitness = 0.6

    child_genome = Genome.crossover(parent_a, parent_b)
    child = Embryo.develop(child_genome)
    result = child.run({"input": "测试"})
    
    print(f"  父代A: {parent_a}")
    print(f"  父代B: {parent_b}")
    print(f"  子代:  {child_genome}")
    print(f"  运行结果: {result.get('response', '')[:80]}")
    assert "response" in result
    print("  ✅ 交配→发育→运行 通过")


# ── 运行所有测试 ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("🧬 AI Embryo Engine — 核心测试 v2 (mind + traits)")
    print("=" * 60)
    print()
    
    tests = [
        test_genome_with_mind,
        test_compile_system_prompt,
        test_traits_operations,
        test_trait_crossover,
        test_mind_inheritance,
        test_genome_creation,
        test_genome_validation_fail,
        test_genome_serialization,
        test_genome_mutation,
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
