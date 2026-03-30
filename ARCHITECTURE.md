# AI Embryo Engine — 架构设计文档

**版本**: v1.0.0  
**日期**: 2026-03-30  
**定位**: 让 AI 系统从单细胞胚胎发育、进化、繁殖的底层引擎  

---

## 1. 核心哲学

### 从 FuturEmbryo 到 AI Embryo 的根本转变

| | FuturEmbryo (旧) | AI Embryo (新) |
|---|---|---|
| **思路** | 用生物隐喻装饰 Agent 框架 | 真正模拟生物发育过程 |
| **Cell** | 功能模块（665行，全副武装） | 最小可执行单元（轻量） |
| **基因** | 5种并列配置项 | 2层结构（身份+蓝图），驱动一切 |
| **Pipeline** | 硬编码编排策略 | 基因表达的自然结果 |
| **进化** | LifeGrower里的方法调用 | 独立的进化循环引擎 |
| **杂交** | 复杂的Cell合并逻辑 | 纯基因组层面的操作 |

### 三条铁律

1. **基因组是唯一真理** — 一个生命体的全部信息都在基因组里，发育是基因组的自动表达
2. **细胞是最轻的** — Cell 只做一件事：接收输入，产生输出。没有进化、没有记忆、没有社交
3. **进化在种群层面发生** — 单个生命体不会自己变好，是种群通过选择压力变好

---

## 2. 概念体系（只有6个核心概念）

```
Genome（基因组）     — AI 的遗传密码，YAML/JSON 定义
    ↓ 表达
Cell（细胞）         — 最小功能单元，只有 process() 方法
    ↓ 组装
Organism（生命体）   — 由多个 Cell 组成的可运行实体
    ↓ 评估
Fitness（适应度）    — 生命体在任务上的表现评分
    ↓ 选择 + 交配
Evolution（进化）    — 基因组层面的交叉、变异、选择
    ↓ 发育
新的 Organism       — 循环继续
```

没有 Pipeline、没有 LifeGrower、没有 ContextArchitecture、没有 IERT。

---

## 3. Genome（基因组）

### 3.1 两层结构

```yaml
# ai_agent.genome.yaml

name: "分析师Alpha"
version: "1.0.0"

# ═══ 身份基因（Identity Genes）— 稳定，不轻易改变 ═══
identity:
  purpose: "提供深度技术分析和战略建议"
  personality: ["专业", "直接", "有洞察力"]
  language: "zh-CN"
  constraints: ["保护隐私", "不提供医疗建议"]

# ═══ 蓝图基因（Blueprint Genes）— 可变，通过进化改变 ═══
blueprint:
  # 能力基因
  capabilities:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    tools: ["web_search", "calculator"]
    
  # 结构基因 — 定义 Cell 组成
  cells:
    - type: "MemoryCell"
      config:
        backend: "chromadb"
        collection: "agent_memory"
    - type: "LLMCell"
      config:
        model: "${capabilities.model}"      # 引用能力基因
        temperature: "${capabilities.temperature}"
    - type: "ToolCell"
      config:
        tools: "${capabilities.tools}"
  
  # 组装方式
  assembly: "sequential"  # sequential | parallel | conditional
  
  # 进化基因
  evolution:
    mutation_rate: 0.1
    fitness_metrics: ["accuracy", "speed", "user_satisfaction"]
    mutable_fields:              # 哪些字段允许变异
      - "capabilities.model"
      - "capabilities.temperature"
      - "capabilities.max_tokens"
      - "cells"
      - "assembly"
    immutable_fields:            # 哪些字段不允许变异（身份基因默认不可变）
      - "identity.*"
```

### 3.2 关键设计决策

- **身份基因 vs 蓝图基因的分离**：交配时身份基因从主要父代继承，蓝图基因可以自由交叉
- **`mutable_fields` 显式声明**：基因组自己定义哪些部分可以被进化改变
- **变量引用 `${}`**：Cell 配置可以引用上层基因值，避免重复定义
- **基因组就是 YAML**：人类可读、可编辑、可版本控制

---

## 4. Cell（细胞）

### 4.1 极简基类

```python
class Cell:
    """细胞 — AI Embryo 的最小功能单元"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def process(self, input: dict) -> dict:
        """唯一的核心方法：接收输入，产生输出"""
        raise NotImplementedError
```

就这么多。没有状态管理、没有进化历史、没有生命名片、没有上下文工程。

### 4.2 内置 Cell 类型

| Cell | 职责 | 输入 | 输出 |
|------|------|------|------|
| `LLMCell` | 调用语言模型 | messages, tools | response, tool_calls |
| `MemoryCell` | 存取记忆 | query / content | memories / stored |
| `ToolCell` | 执行工具调用 | tool_name, args | result |
| `RouterCell` | 路由决策 | input, conditions | selected_path |

### 4.3 自定义 Cell

```python
class SentimentCell(Cell):
    """情感分析细胞"""
    def process(self, input: dict) -> dict:
        text = input["text"]
        # ... 分析逻辑
        return {"sentiment": "positive", "score": 0.85}
```

---

## 5. Organism（生命体）

### 5.1 定义

Organism = Genome + 已实例化的 Cells + 运行时状态

```python
class Organism:
    """生命体 — 从基因组发育而来的可运行 AI 实体"""
    
    def __init__(self, genome: Genome, cells: list[Cell], assembly: str):
        self.genome = genome           # 遗传密码
        self.cells = cells             # 已实例化的细胞
        self.assembly = assembly       # 组装方式
        self.generation = 1            # 代数
        self.fitness_history = []      # 适应度历史
    
    def run(self, input: dict) -> dict:
        """运行生命体处理输入"""
        # 根据 assembly 方式串联/并联 cells
        ...
    
    def evaluate(self, task, expected) -> float:
        """评估适应度"""
        ...
```

### 5.2 发育过程（Genome → Organism）

```python
class Embryo:
    """胚胎 — 负责从基因组发育出生命体"""
    
    @staticmethod
    def develop(genome: Genome) -> Organism:
        """
        发育：基因组 → 生命体
        
        1. 解析基因组
        2. 实例化 Cells
        3. 确定组装方式
        4. 返回可运行的 Organism
        """
        cells = []
        for cell_def in genome.blueprint.cells:
            cell_class = CellRegistry.get(cell_def["type"])
            config = genome.resolve_references(cell_def.get("config", {}))
            cells.append(cell_class(config))
        
        return Organism(
            genome=genome,
            cells=cells,
            assembly=genome.blueprint.assembly
        )
```

关键点：**Embryo 是无状态的工厂**，不是 God Class。它就做一件事——把基因组变成生命体。

---

## 6. Evolution（进化引擎）

### 6.1 进化循环

```python
class EvolutionEngine:
    """进化引擎 — 在种群层面驱动进化"""
    
    def evolve(self, 
               population: list[Organism],
               tasks: list[Task],
               generations: int = 10,
               population_size: int = 8,
               selection_pressure: float = 0.5) -> Organism:
        """
        进化主循环
        
        Args:
            population: 初始种群
            tasks: 评估任务集
            generations: 迭代代数
            population_size: 种群大小
            selection_pressure: 选择压力（淘汰比例）
        
        Returns:
            最优生命体
        """
        for gen in range(generations):
            # 1. 评估：每个个体跑任务，得到适应度
            fitness_scores = self._evaluate_all(population, tasks)
            
            # 2. 选择：保留优秀个体
            survivors = self._select(population, fitness_scores, selection_pressure)
            
            # 3. 交配：优秀个体配对产生后代
            offspring_genomes = self._crossover(survivors)
            
            # 4. 变异：随机扰动
            mutated_genomes = self._mutate(offspring_genomes)
            
            # 5. 发育：新基因组 → 新生命体
            new_organisms = [Embryo.develop(g) for g in mutated_genomes]
            
            # 6. 组建新种群
            population = survivors + new_organisms
            population = population[:population_size]  # 控制种群规模
        
        # 返回最优个体
        return max(population, key=lambda o: o.fitness_history[-1])
```

### 6.2 交配（Crossover）

```python
def _crossover(self, parents: list[Organism]) -> list[Genome]:
    """基因组层面的交叉"""
    offspring = []
    
    for i in range(0, len(parents) - 1, 2):
        parent_a = parents[i].genome
        parent_b = parents[i + 1].genome
        
        child_genome = Genome.crossover(parent_a, parent_b)
        offspring.append(child_genome)
    
    return offspring
```

```python
# Genome 类的交叉方法
class Genome:
    @staticmethod
    def crossover(a: 'Genome', b: 'Genome') -> 'Genome':
        """
        基因交叉
        
        规则：
        - identity 从适应度更高的父代继承（主导父代）
        - blueprint 的每个字段随机从两个父代中选择
        - mutable_fields 中的字段才参与交叉
        """
        # 确定主导父代（适应度更高的）
        dominant = a if a.fitness >= b.fitness else b
        recessive = b if dominant is a else a
        
        child = Genome()
        
        # 身份基因：从主导父代继承
        child.identity = deepcopy(dominant.identity)
        
        # 蓝图基因：逐字段交叉
        child.blueprint = {}
        for field in dominant.blueprint:
            if random.random() < 0.5:
                child.blueprint[field] = deepcopy(dominant.blueprint[field])
            else:
                child.blueprint[field] = deepcopy(recessive.blueprint[field])
        
        return child
```

### 6.3 变异（Mutation）

```python
def _mutate(self, genomes: list[Genome]) -> list[Genome]:
    """对基因组进行随机变异"""
    for genome in genomes:
        mutation_rate = genome.blueprint.evolution.mutation_rate
        
        for field in genome.blueprint.evolution.mutable_fields:
            if random.random() < mutation_rate:
                genome.mutate_field(field)
    
    return genomes
```

变异策略示例：
- `capabilities.temperature`: 在 ±0.2 范围内随机浮动
- `capabilities.model`: 从候选模型列表中随机选择
- `cells`: 随机添加/删除/替换一个 Cell
- `assembly`: 在 sequential/parallel 间切换

---

## 7. 适应度评估（Fitness）

```python
class FitnessEvaluator:
    """适应度评估器"""
    
    def evaluate(self, organism: Organism, tasks: list[Task]) -> float:
        """
        评估一个生命体的适应度
        
        综合考虑基因组中定义的 fitness_metrics
        """
        scores = {}
        
        for task in tasks:
            result = organism.run(task.input)
            
            # 按指标打分
            if "accuracy" in organism.genome.blueprint.evolution.fitness_metrics:
                scores.setdefault("accuracy", []).append(
                    self._score_accuracy(result, task.expected)
                )
            
            if "speed" in organism.genome.blueprint.evolution.fitness_metrics:
                scores.setdefault("speed", []).append(
                    self._score_speed(result)
                )
            
            if "user_satisfaction" in organism.genome.blueprint.evolution.fitness_metrics:
                scores.setdefault("user_satisfaction", []).append(
                    self._score_satisfaction(result, task)
                )
        
        # 加权平均
        total = sum(sum(v) / len(v) for v in scores.values()) / len(scores)
        organism.fitness_history.append(total)
        return total
```

---

## 8. 目录结构

```
ai_embryo/                    # 包名（替换 futurembryo）
├── __init__.py
├── genome.py                 # Genome 定义与操作（加载/验证/交叉/变异）
├── cell.py                   # Cell 基类（极简）
├── cells/                    # 内置 Cell 实现
│   ├── __init__.py
│   ├── llm_cell.py          # LLM 调用
│   ├── memory_cell.py       # 记忆存取
│   ├── tool_cell.py         # 工具执行
│   └── router_cell.py       # 路由决策
├── organism.py               # Organism 生命体
├── embryo.py                 # Embryo 发育器（Genome → Organism）
├── evolution.py              # EvolutionEngine 进化引擎
├── fitness.py                # FitnessEvaluator 适应度评估
├── registry.py               # CellRegistry 细胞注册表
└── exceptions.py             # 异常定义
```

对比旧结构：
- 旧：30个文件，12000行
- 新：~12个文件，预计 2000-3000 行

---

## 9. 使用示例

### 9.1 最简单：创建并运行一个 Agent

```python
from ai_embryo import Genome, Embryo

# 从 YAML 加载基因组
genome = Genome.from_file("my_agent.genome.yaml")

# 发育成生命体
agent = Embryo.develop(genome)

# 运行
result = agent.run({"input": "分析一下AI行业趋势"})
print(result["response"])
```

### 9.2 进化：让 Agent 自动变好

```python
from ai_embryo import Genome, Embryo, EvolutionEngine

# 创建初始种群
genomes = [Genome.from_file(f"agent_{i}.genome.yaml") for i in range(4)]
population = [Embryo.develop(g) for g in genomes]

# 定义评估任务
tasks = [
    Task(input={"input": "什么是量子计算"}, expected="准确解释量子计算概念"),
    Task(input={"input": "对比Python和Rust"}, expected="客观对比两种语言"),
]

# 进化10代
engine = EvolutionEngine()
best_agent = engine.evolve(population, tasks, generations=10)

# 保存最优基因组
best_agent.genome.save("best_agent.genome.yaml")
```

### 9.3 手动交配：融合两个 Agent

```python
from ai_embryo import Genome, Embryo

analyst = Genome.from_file("analyst.genome.yaml")
creative = Genome.from_file("creative.genome.yaml")

# 交配
child_genome = Genome.crossover(analyst, creative)

# 发育
hybrid = Embryo.develop(child_genome)

# 测试
result = hybrid.run({"input": "用创意方式分析市场趋势"})
```

---

## 10. 从 FuturEmbryo 迁移

### 保留的核心价值
- ✅ 生物学启发的架构哲学
- ✅ Cell 作为最小单元的思想
- ✅ DNA/基因驱动配置的理念
- ✅ LLMCell、MemoryCell、ToolCell 的实现逻辑
- ✅ MCP 协议支持

### 删除的冗余
- ❌ IERT 元素系统（概念模糊，实际没用）
- ❌ ContextArchitecture 三层体系（过度设计）
- ❌ ContextBuilder（功能合并到 Organism）
- ❌ LifeGrower God Class（拆分为 Embryo + EvolutionEngine）
- ❌ DigitalLifeCard（概念好但实现鸡肋）
- ❌ AutonomousGrowthEngine（合并到 EvolutionEngine）
- ❌ Pipeline 智能响应选择（不需要，Cell 职责清晰后自然解决）
- ❌ MindCell（推理由 LLMCell 承担，不需要单独 Cell）
- ❌ UserProfileAdapter / MentionProcessorCell（不是框架核心）

---

## 11. 实施计划

### Phase 1: 核心骨架
1. 创建 `ai_embryo/` 包目录
2. 实现 `Genome` — 加载、验证、交叉、变异
3. 实现 `Cell` 基类（极简版）
4. 实现 `Embryo.develop()` — 基因组到生命体
5. 实现 `Organism.run()` — 生命体运行

### Phase 2: Cell 实现
6. 迁移 `LLMCell`（精简，保留核心调用逻辑）
7. 迁移 `MemoryCell`（保留 ChromaDB 集成）
8. 迁移 `ToolCell`（保留 MCP + Function Calling）
9. 新增 `RouterCell`

### Phase 3: 进化引擎
10. 实现 `FitnessEvaluator`
11. 实现 `EvolutionEngine` — 完整进化循环
12. 实现交配（Crossover）和变异（Mutation）

### Phase 4: 测试与示例
13. 基础功能测试
14. 进化循环测试
15. 杂交测试
16. 使用示例
