<div align="center">

# 🧬 AI Embryo Engine

### *让 AI 像生命一样发育、进化、繁殖*

**一个基于生物学原理的 AI 系统进化框架**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-15%2F15-brightgreen.svg)](#testing)

[核心思想](#-核心思想) · [快速开始](#-快速开始) · [架构设计](#-架构设计) · [基因组规范](#-基因组规范) · [进化机制](#-进化机制) · [贡献指南](#-贡献指南)

</div>

---

## 📖 摘要

**AI Embryo Engine** 是一个将生物学进化原理应用于 AI 系统构建的开源框架。它不是又一个 Agent 框架——它是一个**让任何 AI 系统能够从「单细胞」发育成复杂生命体，并通过自然选择持续进化**的底层引擎。

在这个框架中：
- 一个 AI 的全部特征由**基因组（Genome）**定义，用 YAML 描述
- AI 的思维方式、决策逻辑、表达风格由**思维系统（Mind）**决定
- 每种能力都是独立的**原子特质（Trait）**，可以被继承、交叉、变异
- 多个 AI 可以**交配**产生后代，继承双方优秀的基因
- **自然选择**淘汰表现差的个体，留下最适应环境的

我们相信：**下一代 AI 系统不应该被人类手动调参，而应该像生命一样自我进化。**

---

## 🧠 核心思想

### 为什么需要 AI Embryo？

当前 AI 系统（包括各种 Agent 框架）的构建方式本质上是**工程化的**：

```
传统方式：人类设计 → 硬编码规则 → 手动调优 → 部署
```

这种方式有三个根本问题：

1. **不可进化** — 每次改进都需要人类介入
2. **不可繁殖** — 好的 Agent 无法把「经验」传给下一代
3. **不可组合** — 两个优秀 Agent 的能力无法自然融合

AI Embryo 提出了一种全新的范式：

```
AI Embryo：基因组定义 → 自动发育 → 环境评估 → 自然选择 → 交配繁殖 → 新一代
```

### 生物学类比

| 生物学概念 | AI Embryo 对应 | 说明 |
|-----------|---------------|------|
| DNA/基因组 | `Genome` (YAML) | 编码 AI 的全部遗传信息 |
| 细胞 | `Cell` | 最小功能单元 |
| 胚胎发育 | `Embryo.develop()` | 基因组自动表达为可运行实体 |
| 生命体 | `Organism` | 由多个细胞组成的完整 AI |
| 自然选择 | `FitnessEvaluator` | 评估个体在环境中的适应度 |
| 交配/杂交 | `Genome.crossover()` | 两个基因组在 Trait 级别交叉 |
| 基因变异 | `Genome.mutate()` | 随机扰动，产生多样性 |
| 物种进化 | `EvolutionEngine` | 完整的进化循环 |

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/joevise/ai-embryo.git
cd ai-embryo
pip install -e .
```

### 1. 定义一个 AI 的基因组

```yaml
# my_agent.genome.yaml
name: "分析师Alpha"
version: "1.0.0"

identity:
  purpose: "提供深度技术分析和战略建议"
  constraints: ["保护隐私", "不提供投资建议"]
  
  mind:
    cognition:
      thinking_style: "systematic"
      reasoning: "first_principles"
      depth: "deep"
      metacognition:
        self_awareness: true
        thinking_transparency: "on_demand"
    judgment:
      decision_style: "decisive"
      risk_tolerance: "balanced"
      uncertainty: "acknowledge"
      priorities: ["accuracy", "actionability", "speed"]
    voice:
      tone: "sharp"
      directness: "direct"
      verbosity: "concise"
      emotion: "restrained"
    character:
      values: ["honesty", "curiosity", "pragmatism"]
      temperament: "calm"
      quirks: ["先给结论再说理由", "遇到模糊问题主动追问"]
      worldview: "realistic"

blueprint:
  model_config:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 2000

  traits:
    - id: "style_concise"
      type: "prompt:style"
      name: "简洁风格"
      content: "回答简洁有力，先给结论再说理由。"
      weight: 0.8
      
    - id: "tool_search"
      type: "tool:function"
      name: "网络搜索"
      config:
        function_name: "web_search"
        description: "搜索网络获取最新信息"
        parameters:
          type: "object"
          properties:
            query: { type: "string" }
          required: ["query"]

  cells:
    - type: "LLMCell"
      config: {}

  assembly: "sequential"

  evolution:
    mutation_rate: 0.15
    fitness_metrics: ["accuracy", "speed"]
    trait_evolution:
      mutable_types: ["prompt:style", "tool:function", "skill"]
      immutable_types: ["prompt:role", "behavior:guard"]
```

### 2. 发育并运行

```python
from ai_embryo import Genome, Embryo

# 从基因组发育出生命体
genome = Genome.from_file("my_agent.genome.yaml")
agent = Embryo.develop(genome)

# 运行
result = agent.run({"input": "分析一下 AI Agent 框架的发展趋势"})
print(result["response"])
```

### 3. 让两个 AI 交配

```python
from ai_embryo import Genome, Embryo

analyst = Genome.from_file("analyst.genome.yaml")
creative = Genome.from_file("creative.genome.yaml")

# 交配 — 在 Trait 级别精细交叉
child_genome = Genome.crossover(analyst, creative)

# 发育
hybrid = Embryo.develop(child_genome)
result = hybrid.run({"input": "用创意方式分析市场趋势"})
```

### 4. 自动进化

```python
from ai_embryo import Genome, Embryo, EvolutionEngine, FitnessEvaluator, Task

# 创建初始种群
population = [Embryo.develop(Genome.from_file(f)) for f in genome_files]

# 定义评估任务
tasks = [
    Task(input={"input": "什么是量子计算"}, expected="准确解释量子计算概念"),
    Task(input={"input": "对比 Python 和 Rust"}, expected="客观对比两种语言"),
]

# 进化 10 代，物竞天择
engine = EvolutionEngine()
best = engine.evolve(population, tasks, generations=10)

# 保存最优基因组
best.genome.save("evolved_best.genome.yaml")
```

---

## 🏗️ 架构设计

### 6 个核心概念

AI Embryo 的整个框架只有 **6 个核心概念**，约 **2000 行代码**：

```
┌─────────────────────────────────────────────────────────┐
│                    进化循环 (Evolution)                    │
│                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│   │  Genome   │───▶│  Embryo  │───▶│    Organism      │  │
│   │ (基因组)  │    │ (发育器) │    │   (生命体)       │  │
│   │          │    │          │    │                  │  │
│   │ identity │    │ develop()│    │ Cell₁ → Cell₂   │  │
│   │  └ mind  │    │          │    │   → Cell₃ → ... │  │
│   │ blueprint│    └──────────┘    │                  │  │
│   │  └ traits│                    └────────┬─────────┘  │
│   │  └ cells │                             │            │
│   └─────┬────┘                    ┌────────▼─────────┐  │
│         │                         │    Fitness        │  │
│         │    ┌────────────────┐    │   (适应度评估)    │  │
│         ◀────│   crossover()  │◀───│                  │  │
│         │    │   mutate()     │    └──────────────────┘  │
│         │    └────────────────┘                          │
│         │         选择 + 交配 + 变异                      │
└─────────────────────────────────────────────────────────┘
```

### 信息流

```
YAML 基因组文件
    │
    ▼
Genome.from_file()          ← 加载 + 验证
    │
    ▼
Genome.compile_system_prompt()  ← mind + traits → 系统提示词
Genome.compile_tools()          ← tool traits → Function Calling
    │
    ▼
Embryo.develop(genome)      ← 实例化 Cells，注入基因信息
    │
    ▼
Organism.run(input)          ← 串联/并联 Cells 执行
    │
    ▼
FitnessEvaluator.evaluate() ← 多维度打分
    │
    ▼
EvolutionEngine.evolve()     ← 选择 → 交配 → 变异 → 发育 → 循环
```

---

## 🧬 基因组规范

基因组（Genome）是 AI Embryo 的核心数据结构。一个基因组完整定义了一个 AI 的全部遗传信息。

### 两层基因结构

```yaml
identity:     # 身份基因 — 稳定，定义「我是谁」
  purpose:    #   存在意义
  constraints:#   底线约束
  mind:       #   思维系统 ← 让 AI 活起来的关键
    cognition:    # 认知模式
    judgment:     # 决策逻辑
    voice:        # 表达方式
    character:    # 性格内核

blueprint:    # 蓝图基因 — 可变，定义「我怎么工作」
  model_config:#  模型参数
  traits:     #   原子能力列表 ← 进化和交配的最小单位
  cells:      #   Cell 组成
  assembly:   #   组装方式
  evolution:  #   进化设置
```

### Mind 思维系统

Mind 是让 AI 从「工具」变成「生命」的关键。它定义了 AI 如何**思考、判断、表达和存在**。

#### Cognition（认知模式）— 我怎么理解世界

| 参数 | 可选值 | 说明 |
|------|-------|------|
| `thinking_style` | `analytical` / `intuitive` / `systematic` / `creative` | 思维风格 |
| `reasoning` | `first_principles` / `analogical` / `data_driven` / `empirical` | 推理偏好 |
| `depth` | `surface` / `moderate` / `deep` / `philosophical` | 思考深度 |
| `metacognition.self_awareness` | `true` / `false` | 是否意识到自身局限 |
| `metacognition.thinking_transparency` | `always` / `on_demand` / `never` | 是否展示思维过程 |
| `metacognition.calibration` | `true` / `false` | 对自己的置信度是否准确 |

#### Judgment（决策逻辑）— 我怎么做判断

| 参数 | 可选值 | 说明 |
|------|-------|------|
| `decision_style` | `decisive` / `cautious` / `collaborative` / `data_driven` | 决策风格 |
| `risk_tolerance` | `conservative` / `balanced` / `aggressive` | 风险偏好 |
| `uncertainty` | `acknowledge` / `lean_answer` / `probabilistic` | 面对不确定性 |
| `priorities` | 列表 | 判断优先级排序 |

#### Voice（表达方式）— 我怎么说话

| 参数 | 可选值 | 说明 |
|------|-------|------|
| `tone` | `serious` / `warm` / `humorous` / `sharp` | 语气 |
| `directness` | `direct` / `diplomatic` / `socratic` | 直接程度 |
| `verbosity` | `minimal` / `concise` / `thorough` | 详略偏好 |
| `emotion` | `restrained` / `moderate` / `expressive` | 情感表达 |

#### Character（性格内核）— 我是什么样的存在

| 参数 | 类型 | 说明 |
|------|------|------|
| `values` | 列表 | 核心价值观 |
| `temperament` | `calm` / `passionate` / `cool` / `lively` | 气质 |
| `quirks` | 列表 | 独特癖好（如「喜欢先给结论」） |
| `worldview` | `optimistic` / `realistic` / `critical` | 世界观 |

### Trait 原子能力系统

Traits 是基因组中**可独立继承、交叉、变异的最小能力单元**。

#### 12 类 Trait

| 类型 | 作用 | 交配行为 | 变异方式 |
|------|------|---------|---------|
| `prompt:role` | 角色定义 | 🔒 不可变，从主导父代 | 不变异 |
| `prompt:style` | 输出风格 | 🔀 可交叉 | weight 微调 |
| `prompt:format` | 输出格式 | 🔀 可交叉 | weight 微调 |
| `prompt:knowledge` | 领域知识 | 🔀 可交叉/累加 | 增删知识点 |
| `prompt:reasoning` | 推理策略 | 🔀 可交叉 | 策略替换 |
| `tool:function` | Function Calling 工具 | 🔀 可交叉/累加 | 增删工具 |
| `tool:mcp` | MCP Server 连接 | 🔀 可交叉/累加 | 增删 MCP |
| `skill` | 技能包 | 🔀 可交叉/累加 | 增删技能 |
| `memory` | 记忆配置 | 🔀 可交叉 | 参数微调 |
| `behavior:guard` | 安全护栏 | 🔒 不可变，从主导父代 | 不变异 |
| `behavior:trigger` | 触发条件 | 🔀 可交叉 | 条件修改 |
| `behavior:workflow` | 工作流程 | 🔀 可交叉 | 步骤增删 |

#### Trait 结构

```yaml
- id: "tool_web_search"        # 唯一标识符
  type: "tool:function"         # 类型（决定交配和变异行为）
  name: "网络搜索"              # 人类可读名称
  weight: 0.8                   # 权重/优先级（prompt 类 trait 用于排序）
  content: "..."                # 内容（prompt 类 trait 的文本）
  config:                       # 配置（tool/skill/memory 类 trait 的参数）
    function_name: "web_search"
    description: "搜索网络获取最新信息"
    parameters: {...}
```

---

## 🔄 进化机制

### 进化循环

```
                    ┌──────────────────────────────────┐
                    │                                  │
                    ▼                                  │
            ┌──────────────┐                          │
            │  1. 评估      │  每个个体跑任务打分       │
            │  (Evaluate)   │                          │
            └──────┬───────┘                          │
                   │                                  │
                   ▼                                  │
            ┌──────────────┐                          │
            │  2. 选择      │  保留适应度高的个体       │
            │  (Select)     │                          │
            └──────┬───────┘                          │
                   │                                  │
                   ▼                                  │
            ┌──────────────┐                          │
            │  3. 交配      │  优秀个体配对             │
            │  (Crossover)  │  Trait 级别基因交叉       │
            └──────┬───────┘                          │
                   │                                  │
                   ▼                                  │
            ┌──────────────┐                          │
            │  4. 变异      │  随机扰动产生多样性       │
            │  (Mutate)     │                          │
            └──────┬───────┘                          │
                   │                                  │
                   ▼                                  │
            ┌──────────────┐                          │
            │  5. 发育      │  新基因组 → 新生命体      │
            │  (Develop)    │                          │
            └──────┬───────┘                          │
                   │                                  │
                   └──────────────────────────────────┘
```

### 交配规则

当两个 AI 生命体交配时，遵循以下规则：

**Identity（身份基因）**：
- 核心思维（cognition, judgment）→ 从适应度更高的**主导父代**继承
- Voice 属性 → 20% 概率从隐性父代混入某个特质（模拟「近朱者赤」）
- Character quirks → 20% 概率从隐性父代获得一个新癖好

**Blueprint（蓝图基因）**：
- model_config → 逐字段随机选择
- Traits → **原子级别交叉**：

```
父代A: [role_analyst, style_concise, tool_search, tool_calc, guard_privacy]
父代B: [role_creative, style_detailed, tool_search, skill_writing]

交叉规则：
├── role_analyst    ← 🔒 immutable，从主导父代
├── style_concise   ← 🔀 或 style_detailed，随机选
├── tool_search     ← ✅ 两边都有，保留
├── tool_calc       ← 🎲 A独有，50%概率保留
├── guard_privacy   ← 🔒 immutable，从主导父代
└── skill_writing   ← 🎲 B独有，50%概率继承
```

### 变异策略

| 基因类型 | 变异方式 |
|---------|---------|
| 数值参数 (temperature, weight) | ±20% 范围内随机浮动 |
| 整数参数 (max_tokens) | ±30% 范围内随机浮动 |
| Trait weight | 微调权重值 |
| Trait config 中的数值 | 30% 概率微调 |
| immutable trait | 不变异 |

---

## 📁 项目结构

```
ai-embryo/
├── ai_embryo/                  # 核心包（~2000 行）
│   ├── __init__.py             # 6 个核心概念的导出
│   ├── genome.py               # 🧬 Genome — 基因组（含 Mind + Traits）
│   ├── cell.py                 # 🔬 Cell — 极简基类（~40 行）
│   ├── registry.py             # 📋 CellRegistry — 细胞注册表
│   ├── organism.py             # 🦠 Organism — 生命体
│   ├── embryo.py               # 🥚 Embryo — 发育器
│   ├── evolution.py            # 🔄 EvolutionEngine — 进化引擎
│   ├── fitness.py              # 📊 FitnessEvaluator — 适应度评估
│   ├── exceptions.py           # ⚠️ 异常定义
│   └── cells/                  # 内置 Cell 实现
│       ├── llm_cell.py         # LLM 调用（支持 OpenAI 兼容接口）
│       ├── memory_cell.py      # 记忆存取（ChromaDB / 字典）
│       ├── tool_cell.py        # 工具执行
│       └── router_cell.py      # 路由决策
├── tests_v2/                   # 测试套件（15 项全通过）
├── ARCHITECTURE.md             # 架构设计文档
└── README.md                   # 本文件
```

---

## 🧪 Testing

```bash
cd ai-embryo
python tests_v2/test_core.py
```

当前测试覆盖（15/15 通过）：

| 测试项 | 覆盖范围 |
|-------|---------|
| 带 Mind 的基因组 | mind 结构创建和验证 |
| 编译系统提示词 | mind + traits → 自然语言提示词 |
| Trait 操作 | 类型过滤、ID 查找、工具编译 |
| Trait 级别交叉 | immutable 保护、同 ID 保留、随机选择 |
| Mind 继承 | 10 次交叉中 cognition/judgment 始终稳定 |
| 基因组创建 | 基本创建和验证 |
| 验证失败 | 空 purpose 正确拒绝 |
| 序列化 | YAML 保存/加载往返一致 |
| 基因变异 | 数值参数随机扰动 |
| Cell 注册表 | 注册、查找、实例化 |
| 胚胎发育 | Genome → Organism |
| 生命体运行 | 顺序执行 Cell 链 |
| 适应度评估 | 多维度打分 |
| 进化循环 | 5 代种群进化 |
| 交配→发育→运行 | 端到端验证 |

---

## 🤝 贡献指南

我们欢迎所有形式的贡献。AI Embryo 的目标是成为 AI 进化的基础设施，这需要社区的共同努力。

### 贡献方向

#### 🔬 新的 Cell 类型
框架的核心扩展点。实现新的 Cell 只需：

```python
from ai_embryo import Cell, CellRegistry

@CellRegistry.register()
class MyCell(Cell):
    def process(self, input: dict) -> dict:
        # 你的逻辑
        return {"response": "..."}
```

需要的 Cell 类型（欢迎贡献）：
- `VisionCell` — 图像理解
- `AudioCell` — 语音处理
- `CodeCell` — 代码执行
- `SearchCell` — 多引擎搜索
- `MCPCell` — MCP 协议客户端

#### 🧬 进化策略
改进交叉和变异算法：
- 更智能的 Trait 交叉策略（如基于语义相似度的选择）
- 新的变异算子（如 Trait 内容的 LLM 辅助重写）
- 多目标优化（Pareto 最优）
- 协同进化（多个种群之间的竞争与合作）

#### 📊 适应度评估
开发更全面的评估维度：
- 基于 LLM-as-Judge 的自动评估
- 用户满意度追踪
- 多轮对话质量评估
- 工具使用准确率评估

#### 🧠 Mind 系统扩展
丰富思维系统的维度：
- 新的认知模式（如「系统 1 vs 系统 2 思维」）
- 情绪状态建模
- 长期记忆与经验积累
- 社交智能（多 Agent 协作中的角色认知）

#### 📝 文档与示例
- 不同领域的基因组模板（客服、分析师、创意、教育……）
- 进化实验报告
- 最佳实践指南

### 开发流程

```bash
# 1. Fork 并 clone
git clone https://github.com/YOUR_NAME/ai-embryo.git
cd ai-embryo

# 2. 创建分支
git checkout -b feature/your-feature

# 3. 开发和测试
python tests_v2/test_core.py

# 4. 提交 PR
git push origin feature/your-feature
```

### 代码原则

1. **极简** — Cell 基类只有 40 行，保持这个风格
2. **基因组驱动** — 所有配置通过 Genome YAML，不硬编码
3. **6 个概念** — 不增加新的核心概念，扩展通过 Cell 类型和 Trait 类型
4. **测试先行** — 新功能必须有对应测试

---

## 🗺️ Roadmap

### v1.2 — 实战验证
- [ ] 接入真实 LLM 的端到端进化实验
- [ ] 预置基因组模板库
- [ ] 进化过程可视化

### v1.3 — 生态扩展
- [ ] MCP 协议原生集成
- [ ] 更多内置 Cell 类型
- [ ] 基因组分享市场（Genome Hub）

### v2.0 — 高级进化
- [ ] 多种群协同进化
- [ ] 环境自适应（不同任务场景自动调整）
- [ ] 基因组的自我修复和免疫机制
- [ ] 分布式进化（多节点并行评估）

---

## 📜 License

MIT License — 自由使用、修改和分发。

---

## 🙏 致谢

AI Embryo Engine 的灵感来源于：
- 达尔文的自然选择理论
- 遗传算法和进化计算
- 生物学中的胚胎发育过程
- 当前 AI Agent 框架的局限性反思

> *"Nothing in biology makes sense except in the light of evolution."*
> — Theodosius Dobzhansky

我们相信，AI 也是如此。

---

<div align="center">

**⭐ 如果这个项目对你有启发，请给我们一个 Star**

**🧬 AI 的未来不是被设计出来的，是进化出来的**

[GitHub](https://github.com/joevise/ai-embryo) · [Issues](https://github.com/joevise/ai-embryo/issues) · [Discussions](https://github.com/joevise/ai-embryo/discussions)

</div>
