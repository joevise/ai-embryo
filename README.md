<div align="center">

# 🧬 AI Embryo Engine

### *Making AI systems grow, evolve, and reproduce — like life itself*

**A biology-inspired framework for AI system evolution**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-15%2F15-brightgreen.svg)](#testing)

[Core Ideas](#-core-ideas) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [Genome Spec](#-genome-specification) · [Evolution](#-evolution-mechanism) · [Contributing](#-contributing)

**[中文文档 / Chinese Documentation](README_CN.md)**

</div>

---

## 📖 Abstract

**AI Embryo Engine** is an open-source framework that applies biological evolution principles to AI system construction. It is not just another Agent framework — it is a foundational engine that enables **any AI system to develop from a "single cell" into a complex organism, and continuously evolve through natural selection**.

In this framework:
- An AI's complete characteristics are defined by a **Genome** in YAML
- Its thinking patterns, decision logic, and expression style are governed by a **Mind system**
- Each capability is an independent **atomic Trait** that can be inherited, crossed over, and mutated
- Multiple AIs can **mate** to produce offspring that inherit superior genes from both parents
- **Natural selection** eliminates underperformers and preserves the fittest

We believe: **The next generation of AI systems should not be manually tuned by humans — they should evolve like life.**

---

## 🧠 Core Ideas

### Why AI Embryo?

Current AI systems (including various Agent frameworks) are built in an essentially **engineering** way:

```
Traditional: Human designs → Hardcoded rules → Manual tuning → Deploy
```

This approach has three fundamental problems:

1. **Not evolvable** — Every improvement requires human intervention
2. **Not reproducible** — Great Agents can't pass their "experience" to the next generation
3. **Not composable** — Capabilities of two excellent Agents can't naturally merge

AI Embryo proposes a completely new paradigm:

```
AI Embryo: Genome definition → Auto development → Environmental evaluation
         → Natural selection → Mating & reproduction → Next generation
```

### Biological Analogy

| Biology | AI Embryo | Description |
|---------|-----------|-------------|
| DNA / Genome | `Genome` (YAML) | Encodes all hereditary information |
| Cell | `Cell` | Minimal functional unit |
| Embryonic development | `Embryo.develop()` | Genome auto-expresses into a runnable entity |
| Organism | `Organism` | Complete AI composed of multiple cells |
| Natural selection | `FitnessEvaluator` | Evaluates individual fitness in the environment |
| Mating / Hybridization | `Genome.crossover()` | Two genomes cross over at the Trait level |
| Genetic mutation | `Genome.mutate()` | Random perturbation for diversity |
| Species evolution | `EvolutionEngine` | Complete evolution loop |

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/joevise/ai-embryo.git
cd ai-embryo
pip install -e .
```

### 1. Define an AI's Genome

```yaml
# my_agent.genome.yaml
name: "Analyst Alpha"
version: "1.0.0"

identity:
  purpose: "Provide deep technical analysis and strategic advice"
  constraints: ["Protect privacy", "No investment advice"]
  
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
      quirks: ["Leads with conclusions", "Asks clarifying questions proactively"]
      worldview: "realistic"

blueprint:
  model_config:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 2000

  traits:
    - id: "style_concise"
      type: "prompt:style"
      name: "Concise style"
      content: "Answer concisely. Lead with conclusions, then reasoning."
      weight: 0.8
      
    - id: "tool_search"
      type: "tool:function"
      name: "Web search"
      config:
        function_name: "web_search"
        description: "Search the web for latest information"
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

### 2. Develop and Run

```python
from ai_embryo import Genome, Embryo

# Develop an organism from genome
genome = Genome.from_file("my_agent.genome.yaml")
agent = Embryo.develop(genome)

# Run
result = agent.run({"input": "Analyze AI Agent framework trends"})
print(result["response"])
```

### 3. Mate Two AIs

```python
from ai_embryo import Genome, Embryo

analyst = Genome.from_file("analyst.genome.yaml")
creative = Genome.from_file("creative.genome.yaml")

# Crossover — fine-grained at the Trait level
child_genome = Genome.crossover(analyst, creative)

# Develop
hybrid = Embryo.develop(child_genome)
result = hybrid.run({"input": "Analyze market trends creatively"})
```

### 4. Auto-Evolution

```python
from ai_embryo import Genome, Embryo, EvolutionEngine, Task

# Create initial population
population = [Embryo.develop(Genome.from_file(f)) for f in genome_files]

# Define evaluation tasks
tasks = [
    Task(input={"input": "What is quantum computing?"}, expected="Accurate explanation of quantum computing"),
    Task(input={"input": "Compare Python and Rust"}, expected="Objective comparison of both languages"),
]

# Evolve for 10 generations — survival of the fittest
engine = EvolutionEngine()
best = engine.evolve(population, tasks, generations=10)

# Save the fittest genome
best.genome.save("evolved_best.genome.yaml")
```

---

## 🏗️ Architecture

### 6 Core Concepts

The entire framework has only **6 core concepts** in ~**2000 lines of code**:

```
┌──────────────────────────────────────────────────────────┐
│                   Evolution Loop                          │
│                                                          │
│   ┌──────────┐    ┌──────────┐    ┌───────────────────┐  │
│   │  Genome   │───▶│  Embryo  │───▶│    Organism       │  │
│   │          │    │          │    │                   │  │
│   │ identity │    │develop() │    │ Cell₁ → Cell₂    │  │
│   │  └ mind  │    │          │    │   → Cell₃ → ...  │  │
│   │ blueprint│    └──────────┘    │                   │  │
│   │  └ traits│                    └────────┬──────────┘  │
│   │  └ cells │                             │             │
│   └─────┬────┘                    ┌────────▼──────────┐  │
│         │                         │    Fitness         │  │
│         │    ┌────────────────┐    │   Evaluator       │  │
│         ◀────│   crossover()  │◀───│                   │  │
│         │    │   mutate()     │    └───────────────────┘  │
│         │    └────────────────┘                           │
│         │      Select + Mate + Mutate                    │
└──────────────────────────────────────────────────────────┘
```

### Information Flow

```
YAML Genome File
    │
    ▼
Genome.from_file()              ← Load + Validate
    │
    ▼
Genome.compile_system_prompt()  ← Mind + Traits → System prompt
Genome.compile_tools()          ← Tool Traits → Function Calling defs
    │
    ▼
Embryo.develop(genome)          ← Instantiate Cells, inject genome info
    │
    ▼
Organism.run(input)             ← Chain/parallel Cells execution
    │
    ▼
FitnessEvaluator.evaluate()     ← Multi-dimensional scoring
    │
    ▼
EvolutionEngine.evolve()        ← Select → Mate → Mutate → Develop → Loop
```

---

## 🧬 Genome Specification

The Genome is AI Embryo's core data structure. It completely defines all hereditary information of an AI.

### Two-Layer Gene Structure

```yaml
identity:     # Identity Genes — stable, defines "who I am"
  purpose:    #   Reason for existence
  constraints:#   Hard boundaries
  mind:       #   Mind system ← the key to making AI "alive"
    cognition:    # How I understand the world
    judgment:     # How I make decisions
    voice:        # How I express myself
    character:    # Who I am as a being

blueprint:    # Blueprint Genes — mutable, defines "how I work"
  model_config:#  Model parameters
  traits:     #   Atomic capability list ← smallest unit for evolution & mating
  cells:      #   Cell composition
  assembly:   #   Assembly mode
  evolution:  #   Evolution settings
```

### Mind System

Mind is the key that transforms AI from a "tool" into a "living being". It defines how an AI **thinks, judges, expresses, and exists**.

#### Cognition — How I understand the world

| Parameter | Options | Description |
|-----------|---------|-------------|
| `thinking_style` | `analytical` / `intuitive` / `systematic` / `creative` | Thinking style |
| `reasoning` | `first_principles` / `analogical` / `data_driven` / `empirical` | Reasoning preference |
| `depth` | `surface` / `moderate` / `deep` / `philosophical` | Thinking depth |
| `metacognition.self_awareness` | `true` / `false` | Awareness of own limitations |
| `metacognition.thinking_transparency` | `always` / `on_demand` / `never` | Whether to show reasoning process |
| `metacognition.calibration` | `true` / `false` | Accurate confidence estimation |

#### Judgment — How I make decisions

| Parameter | Options | Description |
|-----------|---------|-------------|
| `decision_style` | `decisive` / `cautious` / `collaborative` / `data_driven` | Decision style |
| `risk_tolerance` | `conservative` / `balanced` / `aggressive` | Risk preference |
| `uncertainty` | `acknowledge` / `lean_answer` / `probabilistic` | Facing uncertainty |
| `priorities` | List | Decision priority ordering |

#### Voice — How I express myself

| Parameter | Options | Description |
|-----------|---------|-------------|
| `tone` | `serious` / `warm` / `humorous` / `sharp` | Tone |
| `directness` | `direct` / `diplomatic` / `socratic` | Directness level |
| `verbosity` | `minimal` / `concise` / `thorough` | Detail preference |
| `emotion` | `restrained` / `moderate` / `expressive` | Emotional expression |

#### Character — Who I am as a being

| Parameter | Type | Description |
|-----------|------|-------------|
| `values` | List | Core values |
| `temperament` | `calm` / `passionate` / `cool` / `lively` | Temperament |
| `quirks` | List | Unique habits (e.g., "always leads with conclusions") |
| `worldview` | `optimistic` / `realistic` / `critical` | Worldview |

### Trait: Atomic Capability System

Traits are the **smallest independently inheritable, crossable, and mutable capability units** in a genome.

#### 12 Trait Types

| Type | Purpose | Mating Behavior | Mutation |
|------|---------|-----------------|----------|
| `prompt:role` | Role definition | 🔒 Immutable, from dominant parent | No mutation |
| `prompt:style` | Output style | 🔀 Crossable | Weight tuning |
| `prompt:format` | Output format | 🔀 Crossable | Weight tuning |
| `prompt:knowledge` | Domain knowledge | 🔀 Crossable / Additive | Add/remove items |
| `prompt:reasoning` | Reasoning strategy | 🔀 Crossable | Strategy swap |
| `tool:function` | Function Calling tool | 🔀 Crossable / Additive | Add/remove tools |
| `tool:mcp` | MCP Server connection | 🔀 Crossable / Additive | Add/remove MCPs |
| `skill` | Skill package | 🔀 Crossable / Additive | Add/remove skills |
| `memory` | Memory config | 🔀 Crossable | Parameter tuning |
| `behavior:guard` | Safety guardrails | 🔒 Immutable, from dominant parent | No mutation |
| `behavior:trigger` | Trigger conditions | 🔀 Crossable | Condition change |
| `behavior:workflow` | Workflow rules | 🔀 Crossable | Step add/remove |

---

## 🔄 Evolution Mechanism

### Evolution Loop

```
                    ┌──────────────────────────────────┐
                    │                                  │
                    ▼                                  │
            ┌──────────────┐                          │
            │  1. Evaluate  │  Run tasks, score each   │
            └──────┬───────┘                          │
                   ▼                                  │
            ┌──────────────┐                          │
            │  2. Select    │  Keep the fittest        │
            └──────┬───────┘                          │
                   ▼                                  │
            ┌──────────────┐                          │
            │  3. Crossover │  Pair winners, cross     │
            │               │  genes at Trait level    │
            └──────┬───────┘                          │
                   ▼                                  │
            ┌──────────────┐                          │
            │  4. Mutate    │  Random perturbation     │
            └──────┬───────┘                          │
                   ▼                                  │
            ┌──────────────┐                          │
            │  5. Develop   │  New genome → new life   │
            └──────┬───────┘                          │
                   │                                  │
                   └──────────────────────────────────┘
```

### Crossover Rules

When two AI organisms mate:

**Identity (stable genes)**:
- Core mind (cognition, judgment) → inherited from the **dominant parent** (higher fitness)
- Voice attributes → 20% chance of mixing in a trait from the recessive parent
- Character quirks → 20% chance of inheriting a new quirk

**Blueprint (mutable genes)**:
- model_config → field-level random selection
- Traits → **atomic-level crossover**:

```
Parent A: [role_analyst, style_concise, tool_search, tool_calc, guard_privacy]
Parent B: [role_creative, style_detailed, tool_search, skill_writing]

Crossover:
├── role_analyst    ← 🔒 Immutable, from dominant parent
├── style_concise   ← 🔀 or style_detailed, random pick
├── tool_search     ← ✅ Both have it, keep
├── tool_calc       ← 🎲 A-only, 50% chance to keep
├── guard_privacy   ← 🔒 Immutable, from dominant parent
└── skill_writing   ← 🎲 B-only, 50% chance to inherit
```

---

## 📁 Project Structure

```
ai-embryo/
├── ai_embryo/                  # Core package (~2000 lines)
│   ├── __init__.py             # 6 core concepts
│   ├── genome.py               # 🧬 Genome (Mind + Traits)
│   ├── cell.py                 # 🔬 Minimal Cell base (~40 lines)
│   ├── registry.py             # 📋 CellRegistry
│   ├── organism.py             # 🦠 Organism
│   ├── embryo.py               # 🥚 Embryo (development)
│   ├── evolution.py            # 🔄 EvolutionEngine
│   ├── fitness.py              # 📊 FitnessEvaluator
│   ├── exceptions.py           # ⚠️ Exceptions
│   └── cells/                  # Built-in Cells
│       ├── llm_cell.py         # LLM calls (OpenAI compatible)
│       ├── memory_cell.py      # Memory (ChromaDB / dict)
│       ├── tool_cell.py        # Tool execution
│       └── router_cell.py      # Routing decisions
├── examples/                   # Example genomes
│   ├── analyst.genome.yaml
│   └── creative.genome.yaml
├── tests/
│   └── test_core.py            # 15/15 tests passing
├── pyproject.toml
├── LICENSE                     # MIT
└── README.md
```

---

## 🧪 Testing

```bash
python tests/test_core.py
```

Current coverage (15/15 passing):

| Test | Coverage |
|------|----------|
| Genome with Mind | Mind structure creation & validation |
| System prompt compilation | Mind + Traits → natural language prompt |
| Trait operations | Type filtering, ID lookup, tool compilation |
| Trait-level crossover | Immutable protection, same-ID keep, random selection |
| Mind inheritance | Cognition/judgment stable across 10 crossovers |
| Genome creation | Basic creation and validation |
| Validation failure | Empty purpose correctly rejected |
| Serialization | YAML save/load round-trip consistency |
| Mutation | Numeric parameter perturbation |
| Cell registry | Registration, lookup, instantiation |
| Embryo development | Genome → Organism |
| Organism execution | Sequential Cell chain |
| Fitness evaluation | Multi-dimensional scoring |
| Evolution loop | 5-generation population evolution |
| Mate → Develop → Run | End-to-end verification |

---

## 🤝 Contributing

We welcome all forms of contribution. AI Embryo aims to become the infrastructure for AI evolution — this requires community effort.

### Contribution Areas

#### 🔬 New Cell Types

The core extension point. Implementing a new Cell is simple:

```python
from ai_embryo import Cell, CellRegistry

@CellRegistry.register()
class MyCell(Cell):
    def process(self, input: dict) -> dict:
        return {"response": "..."}
```

Wanted Cell types:
- `VisionCell` — Image understanding
- `AudioCell` — Audio processing
- `CodeCell` — Code execution
- `SearchCell` — Multi-engine search
- `MCPCell` — MCP protocol client

#### 🧬 Evolution Strategies
- Smarter Trait crossover (e.g., semantic similarity-based selection)
- New mutation operators (e.g., LLM-assisted Trait content rewriting)
- Multi-objective optimization (Pareto optimal)
- Co-evolution (competition & cooperation between populations)

#### 📊 Fitness Evaluation
- LLM-as-Judge automatic evaluation
- User satisfaction tracking
- Multi-turn conversation quality
- Tool usage accuracy

#### 🧠 Mind System Extensions
- New cognitive modes (e.g., "System 1 vs System 2 thinking")
- Emotional state modeling
- Long-term memory & experience accumulation
- Social intelligence (role awareness in multi-agent collaboration)

#### 📝 Documentation & Examples
- Genome templates for different domains (customer service, analyst, creative, education...)
- Evolution experiment reports
- Best practices guide

### Development Flow

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_NAME/ai-embryo.git

# 2. Create branch
git checkout -b feature/your-feature

# 3. Develop and test
python tests/test_core.py

# 4. Submit PR
git push origin feature/your-feature
```

### Code Principles

1. **Minimal** — Cell base class is ~40 lines. Keep it that way.
2. **Genome-driven** — All configuration through Genome YAML, no hardcoding.
3. **6 concepts** — Don't add new core concepts. Extend through Cell types and Trait types.
4. **Test first** — New features must have corresponding tests.

---

## 🗺️ Roadmap

### v1.2 — Real-World Validation
- [ ] End-to-end evolution experiments with real LLMs
- [ ] Pre-built genome template library
- [ ] Evolution process visualization

### v1.3 — Ecosystem
- [ ] Native MCP protocol integration
- [ ] More built-in Cell types
- [ ] Genome sharing marketplace (Genome Hub)

### v2.0 — Advanced Evolution
- [ ] Multi-population co-evolution
- [ ] Environmental adaptation (auto-adjust to different task scenarios)
- [ ] Genome self-repair and immune mechanisms
- [ ] Distributed evolution (multi-node parallel evaluation)

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgments

AI Embryo Engine is inspired by:
- Darwin's theory of natural selection
- Genetic algorithms and evolutionary computation
- Biological embryonic development
- Reflections on current AI Agent framework limitations

> *"Nothing in biology makes sense except in the light of evolution."*
> — Theodosius Dobzhansky

We believe the same applies to AI.

---

<div align="center">

**⭐ Star this project if it inspires you**

**🧬 The future of AI is not designed — it's evolved**

[GitHub](https://github.com/joevise/ai-embryo) · [Issues](https://github.com/joevise/ai-embryo/issues) · [Discussions](https://github.com/joevise/ai-embryo/discussions)

</div>
