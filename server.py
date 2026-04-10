"""
AI Embryo Engine — Petri Dish Web Server
FastAPI backend for the AI Petri Dish visualization interface.
"""

import json
import os
import random
import time
import asyncio
import copy
from pathlib import Path
from typing import Any

import yaml
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# AI Embryo imports
from ai_embryo import (
    Genome,
    Cell,
    CellRegistry,
    Organism,
    Embryo,
    EvolutionEngine,
    FitnessEvaluator,
    Task,
)
from ai_embryo.config_manager import ConfigManager
from ai_embryo.organism_package import OrganismPackage
from ai_embryo.evolution_llm import LLMEvolutionEngine, MockLLMEvolutionEngine

# ── Configuration ──────────────────────────────────────────

config = ConfigManager()
config.load()

# ── Register a mock LLM Cell ──────────────────────────────


@CellRegistry.register("LLMCell")
class MockLLMCell(Cell):
    """Mock LLM Cell that generates personality-appropriate responses."""

    RESPONSE_TEMPLATES = {
        "sharp": [
            "核心结论：{topic}。理由很简单——",
            "直说吧：{topic}。不需要绕弯子。",
            "三个要点：第一，{topic}；第二，需要验证；第三，立即行动。",
        ],
        "warm": [
            "这是个很好的问题！让我用一个比喻来解释{topic}——就像种子需要阳光和水分一样 🌱",
            "我觉得{topic}特别有意思！想象一下这样的场景...",
            "💡 关于{topic}，我有几个创意想法想和你分享...",
        ],
        "serious": [
            "经过系统分析，{topic}的核心问题在于以下几个方面。",
            "从数据来看，{topic}呈现出明确的趋势。需要关注三个关键指标。",
            "关于{topic}，有必要从多个维度进行严谨的评估。",
        ],
        "humorous": [
            "哈！{topic}？这个问题让我想起一个笑话... 好吧言归正传 😄",
            "如果{topic}是一道菜，它大概是... 算了，认真回答：",
            "关于{topic}——先别笑——其实挺有意思的！",
        ],
    }

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        identity = self.config.get("_identity", {})
        mind = identity.get("mind", {})
        tone = mind.get("voice", {}).get("tone", "warm")
        purpose = identity.get("purpose", "通用助手")

        user_input = input.get("input", input.get("message", "你好"))
        topic = user_input[:50] if len(user_input) > 50 else user_input

        templates = self.RESPONSE_TEMPLATES.get(tone, self.RESPONSE_TEMPLATES["warm"])
        response = random.choice(templates).format(topic=topic)

        # Add personality flavor
        quirks = mind.get("character", {}).get("quirks", [])
        if quirks:
            response += f"\n\n（{random.choice(quirks)}）"

        values = mind.get("character", {}).get("values", [])
        if values:
            response += f"\n\n[核心价值观驱动: {', '.join(values[:3])}]"

        return {"response": response, "success": True}


# ── Real LLM Cell ──────────────────────────────────────────


class RealLLMCell(Cell):
    """Real LLM Cell that calls OpenAI-compatible API."""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise RuntimeError("openai package required: pip install openai")

            cfg = ConfigManager()
            api_key = self.config.get("api_key") or cfg.get("llm.api_key", "")
            base_url = (
                self.config.get("base_url") or cfg.get("llm.base_url", "") or None
            )

            kwargs = {}
            if api_key:
                kwargs["api_key"] = api_key
            if base_url:
                kwargs["base_url"] = base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        cfg = ConfigManager()
        model = self.config.get("model") or cfg.get("llm.model", "gpt-4")
        temperature = self.config.get("temperature") or cfg.get("llm.temperature", 0.7)
        max_tokens = self.config.get("max_tokens") or cfg.get("llm.max_tokens", 2000)

        # Build messages
        messages = input.get("messages", [])
        if not messages:
            system_prompt = self.config.get("system_prompt", "")
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Include conversation history if provided
            history = input.get("history", [])
            if history:
                messages.extend(history)

            user_input = input.get("input", input.get("message", ""))
            if user_input:
                messages.append({"role": "user", "content": user_input})

        if not messages:
            return {"response": "", "error": "没有输入内容"}

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choice = response.choices[0]
            result = {
                "response": choice.message.content or "",
                "finish_reason": choice.finish_reason,
                "success": True,
            }
            if response.usage:
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return result
        except Exception as e:
            return {"response": f"LLM 调用失败: {e}", "success": False, "error": str(e)}


def _has_any_api_key() -> bool:
    """检查是否有任何 API key 配置（config、MINIMAX_API_KEY、AI_EMBRYO_API_KEY）"""
    if config.has_api_key():
        return True
    if os.environ.get("MINIMAX_API_KEY", ""):
        return True
    if os.environ.get("AI_EMBRYO_API_KEY", ""):
        return True
    return False


# ── LLM Evolution Engine ────────────────────────────────────


def _create_evolution_engine():
    """Create LLM evolution engine based on API key availability"""
    if _has_any_api_key():
        return LLMEvolutionEngine(
            api_key=config.get("llm.api_key", "")
            or os.environ.get("MINIMAX_API_KEY", ""),
            base_url=config.get("llm.base_url", "")
            or os.environ.get("AI_EMBRYO_BASE_URL", ""),
            model=config.get("llm.model", "MiniMax-M2.7"),
        )
    return MockLLMEvolutionEngine()


evolution_engine = _create_evolution_engine()


def register_llm_cell():
    """Register RealLLMCell or MockLLMCell based on config."""
    if _has_any_api_key():
        CellRegistry._registry["LLMCell"] = RealLLMCell
        print("  🔗 Using RealLLMCell (API key configured)")
    else:
        CellRegistry._registry["LLMCell"] = MockLLMCell
        print("  🧪 Using MockLLMCell (no API key)")


# ── App Setup ──────────────────────────────────────────────

app = FastAPI(title="AI Embryo Engine — Petri Dish")

PROJECT_ROOT = Path(__file__).parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
WEB_DIR = PROJECT_ROOT / "web"
ORGANISMS_DIR = PROJECT_ROOT / "data" / "organisms"

# Runtime storage
genomes_store: dict[str, Genome] = {}
organisms_store: dict[str, Organism] = {}
chat_history: dict[str, list[dict]] = {}  # per-organism chat history
package_store: dict[str, OrganismPackage] = {}  # filesystem-based organism packages


def load_example_genomes():
    """Load all example genome files."""
    if not EXAMPLES_DIR.exists():
        return
    for f in EXAMPLES_DIR.glob("*.genome.yaml"):
        try:
            g = Genome.from_file(f)
            genomes_store[g.name] = g
        except Exception as e:
            print(f"Warning: failed to load {f}: {e}")

    for f in EXAMPLES_DIR.glob("*.genome.json"):
        try:
            g = Genome.from_file(f)
            genomes_store[g.name] = g
        except Exception as e:
            print(f"Warning: failed to load {f}: {e}")


load_example_genomes()


def load_organism_packages():
    """Load all organism packages from filesystem."""
    if not ORGANISMS_DIR.exists():
        ORGANISMS_DIR.mkdir(parents=True, exist_ok=True)
        return

    for org_dir in ORGANISMS_DIR.iterdir():
        if org_dir.is_dir():
            try:
                pkg = OrganismPackage.load(org_dir)
                if pkg:
                    package_store[pkg.name] = pkg
                    print(f"  📦 Loaded package: {pkg.name}")
            except Exception as e:
                print(f"  ⚠️ Failed to load package {org_dir.name}: {e}")


load_organism_packages()


def auto_develop_genomes():
    """Auto-develop all loaded genomes into organisms on startup."""
    register_llm_cell()
    for name, g in list(genomes_store.items()):
        if name not in organisms_store:
            try:
                org = Embryo.develop(g)
                organisms_store[name] = org
                print(f"  🧬 Auto-developed: {name}")
            except Exception as e:
                print(f"  ⚠️ Failed to develop {name}: {e}")


auto_develop_genomes()


def genome_to_info(g: Genome) -> dict:
    """Convert genome to API-friendly dict."""
    mind = g.identity.get("mind", {})
    traits = g.blueprint.get("traits", [])
    return {
        "name": g.name,
        "version": g.version,
        "fitness": g.fitness,
        "purpose": g.identity.get("purpose", ""),
        "mind": mind,
        "traits": [
            {
                "id": t.get("id", ""),
                "type": t.get("type", ""),
                "name": t.get("name", ""),
                "weight": t.get("weight", 0.5),
            }
            for t in traits
        ],
        "trait_count": len(traits),
        "model_config": g.blueprint.get("model_config", {}),
        "constraints": g.identity.get("constraints", []),
        "evolution": g.blueprint.get("evolution", {}),
        "raw": g.to_dict(),
    }


def organism_to_info(o: Organism) -> dict:
    """Convert organism to API-friendly dict."""
    info = genome_to_info(o.genome)
    info.update(
        {
            "generation": o.generation,
            "fitness_history": o.fitness_history,
            "birth_time": o.birth_time,
            "age": round(o.age, 1),
            "run_count": o._run_count,
            "cell_count": len(o.cells),
            "assembly": o.assembly,
        }
    )
    return info


def _get_organism_system_prompt(org: Organism) -> str:
    """Get compiled system prompt from organism's genome."""
    try:
        return org.genome.compile_system_prompt()
    except Exception:
        return ""


def _run_with_real_llm(
    org: Organism, input_data: dict[str, Any], history: list[dict] | None = None
) -> dict[str, Any]:
    """Run organism with real LLM if configured, otherwise fallback to normal run."""
    if not _has_any_api_key():
        return org.run(input_data)

    cell = RealLLMCell(
        {
            "system_prompt": _get_organism_system_prompt(org),
        }
    )
    cell_input = dict(input_data)
    if history:
        cell_input["history"] = history
    return cell.process(cell_input)


async def _trigger_reflection(
    name: str, pkg: OrganismPackage, history: list[dict]
) -> dict | None:
    """Trigger reflection for an organism after conversation milestones."""
    try:
        reflection_result = await evolution_engine.reflect(pkg, history)
        if reflection_result:
            memory_update = reflection_result.get("memory_update", "")
            if memory_update:
                pkg.add_reflection(
                    f"# 定期反思\n\n{memory_update}\n\n自评分数: {reflection_result.get('fitness_self_score', 0.5)}"
                )

            changes = {}
            mind_updates = reflection_result.get("mind_updates", "")
            if mind_updates:
                current_mind = pkg.read_mind()
                new_mind = current_mind + f"\n\n# 更新\n{mind_updates}"
                pkg.write_mind(new_mind)
                changes["mind"] = mind_updates

            soul_updates = reflection_result.get("soul_updates", "")
            if soul_updates:
                current_soul = pkg.read_soul()
                new_soul = current_soul + f"\n\n# 更新\n{soul_updates}"
                pkg.write_soul(new_soul)
                changes["soul"] = soul_updates

            fitness_self_score = reflection_result.get("fitness_self_score", 0.5)
            if fitness_self_score:
                old_fitness = pkg.fitness
                pkg.fitness = old_fitness * 0.7 + fitness_self_score * 0.3
                pkg.save()

            if changes:
                reasoning = f"反思结果：strengths={reflection_result.get('strengths', '')}, weaknesses={reflection_result.get('weaknesses', '')}"
                pkg.add_changelog("反思进化", changes, reasoning)

            return reflection_result
        return None
    except Exception as e:
        print(f"Reflection error for {name}: {e}")
        return None


# ── Config API Routes ──────────────────────────────────────


@app.get("/api/config")
def get_config():
    return {
        "config": config.get_masked_config(),
        "mode": "live" if _has_any_api_key() else "demo",
    }


@app.post("/api/config")
async def update_config(request: Request):
    body = await request.json()
    updated = []
    for key in ["api_key", "model", "base_url", "provider"]:
        if key in body:
            config.set(f"llm.{key}", body[key])
            updated.append(key)
    config.save()
    # Re-register LLM cell and evolution engine based on new config
    register_llm_cell()
    global evolution_engine
    evolution_engine = _create_evolution_engine()
    return {"status": "ok", "updated": updated, "config": config.get_masked_config()}


@app.get("/api/config/models")
def get_suggested_models():
    return {
        "models": {
            "openai": [
                "gpt-4",
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-3.5-turbo",
                "o1",
                "o1-mini",
            ],
            "anthropic": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-3-5-sonnet-20241022",
            ],
            "custom": ["(enter your model name)"],
        }
    }


@app.post("/api/config/test")
async def test_llm_connection():
    if not _has_any_api_key():
        return {"status": "error", "message": "No API key configured"}
    try:
        cell = RealLLMCell({})
        result = cell.process({"input": "Say 'hello' in one word."})
        if result.get("success"):
            return {
                "status": "ok",
                "response": result.get("response", ""),
                "usage": result.get("usage"),
            }
        else:
            return {"status": "error", "message": result.get("error", "Unknown error")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── API Routes ─────────────────────────────────────────────


@app.get("/api/genomes")
def list_genomes():
    return {"genomes": [genome_to_info(g) for g in genomes_store.values()]}


@app.post("/api/genomes")
async def create_genome(request: Request):
    body = await request.json()
    if isinstance(body, str):
        data = yaml.safe_load(body)
    elif "yaml" in body:
        data = yaml.safe_load(body["yaml"])
    else:
        data = body

    try:
        g = Genome.from_dict(data)

        discovered_tools = body.get("discovered_tools", [])
        for tool in discovered_tools:
            tool_name = tool.get("name", "")
            g.blueprint.setdefault("traits", []).append(
                {
                    "id": f"tool_{tool_name.replace(' ', '_').lower()}",
                    "type": "tool:function",
                    "name": tool_name,
                    "config": {
                        "function_name": tool_name.replace(" ", "_").lower(),
                        "description": tool.get("description", ""),
                        "source": tool.get("source", "clawhub"),
                    },
                    "weight": 0.6,
                }
            )

        genomes_store[g.name] = g
        return {"status": "ok", "genome": genome_to_info(g)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/genomes/{name}")
def get_genome(name: str):
    g = genomes_store.get(name)
    if not g:
        raise HTTPException(status_code=404, detail=f"Genome '{name}' not found")
    return genome_to_info(g)


@app.post("/api/develop")
async def develop_genome(request: Request):
    body = await request.json()
    name = body.get("name", "")
    g = genomes_store.get(name)
    if not g:
        raise HTTPException(status_code=404, detail=f"Genome '{name}' not found")
    try:
        org = Embryo.develop(g)
        organisms_store[g.name] = org
        return {"status": "ok", "organism": organism_to_info(org)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/run")
async def run_organism(request: Request):
    body = await request.json()
    name = body.get("name", "")
    input_data = body.get("input", {})
    if isinstance(input_data, str):
        input_data = {"input": input_data}

    org = organisms_store.get(name)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    result = _run_with_real_llm(org, input_data)
    return {"status": "ok", "result": result}


@app.post("/api/crossover")
async def crossover_genomes(request: Request):
    body = await request.json()
    name_a = body.get("parent_a", "") or body.get("name_a", "")
    name_b = body.get("parent_b", "") or body.get("name_b", "")

    pkg_a = package_store.get(name_a)
    pkg_b = package_store.get(name_b)
    ga = genomes_store.get(name_a)
    gb = genomes_store.get(name_b)

    if pkg_a and pkg_b:
        try:
            child_pkg = await evolution_engine.crossover(pkg_a, pkg_b)
            if child_pkg:
                package_store[child_pkg.name] = child_pkg
                return {
                    "status": "ok",
                    "child": child_pkg.to_info(),
                    "organism": child_pkg.to_info(),
                    "reasoning": "LLM-driven crossover",
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Crossover failed: {e}")

    if not ga:
        raise HTTPException(status_code=404, detail=f"Genome '{name_a}' not found")
    if not gb:
        raise HTTPException(status_code=404, detail=f"Genome '{name_b}' not found")

    try:
        child = Genome.crossover(ga, gb)
        child.fitness = (ga.fitness + gb.fitness) / 2 * random.uniform(0.8, 1.2)
        genomes_store[child.name] = child
        org = Embryo.develop(child)
        org.generation = (
            max(
                organisms_store.get(name_a, Organism(ga, [])).generation,
                organisms_store.get(name_b, Organism(gb, [])).generation,
            )
            + 1
        )
        organisms_store[child.name] = org
        return {
            "status": "ok",
            "child": organism_to_info(org),
            "organism": organism_to_info(org),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mutate")
async def mutate_genome(request: Request):
    body = await request.json()
    name = body.get("name", "")
    rate = body.get("mutation_rate", None)

    g = genomes_store.get(name)
    if not g:
        raise HTTPException(status_code=404, detail=f"Genome '{name}' not found")

    mutated = copy.deepcopy(g)
    mutated.mutate(rate)
    mutated.name = f"{g.name}_mut"
    genomes_store[mutated.name] = mutated

    try:
        org = Embryo.develop(mutated)
        organisms_store[mutated.name] = org
        return {
            "status": "ok",
            "mutated": organism_to_info(org),
            "organism": organism_to_info(org),
        }
    except Exception as e:
        return {
            "status": "ok",
            "mutated": genome_to_info(mutated),
            "develop_error": str(e),
        }


@app.post("/api/evolve")
async def evolve_population(request: Request):
    body = await request.json()
    generations = body.get(
        "generations", config.get("evolution.default_generations", 5)
    )
    population_size = body.get(
        "population_size", config.get("evolution.default_population_size", 6)
    )

    async def event_stream():
        population = []
        for name, org in list(organisms_store.items()):
            population.append(org)
        if len(population) < 2:
            for name, g in list(genomes_store.items()):
                if name not in organisms_store:
                    try:
                        org = Embryo.develop(g)
                        organisms_store[name] = org
                        population.append(org)
                    except:
                        pass

        if len(population) < 2:
            yield f"data: {json.dumps({'error': 'Need at least 2 organisms to evolve'})}\n\n"
            return

        tasks = [
            Task(
                input={"input": "分析当前AI技术的发展趋势"},
                expected="AI 技术 趋势 发展 大模型",
                name="分析任务",
                weight=1.0,
            ),
            Task(
                input={"input": "提出一个创新的产品想法"},
                expected="创新 产品 用户 体验 设计",
                name="创意任务",
                weight=1.0,
            ),
            Task(
                input={"input": "如何提高团队效率"},
                expected="效率 团队 协作 流程 优化",
                name="效率任务",
                weight=1.0,
            ),
        ]

        evaluator = FitnessEvaluator()

        for gen in range(1, generations + 1):
            fitness_map = {}
            for org in population:
                score = evaluator.evaluate(org, tasks)
                fitness_map[id(org)] = score

            population.sort(key=lambda o: fitness_map[id(o)], reverse=True)

            gen_data = {
                "generation": gen,
                "total_generations": generations,
                "population": [
                    {
                        "name": o.name,
                        "fitness": round(fitness_map[id(o)], 4),
                        "generation": o.generation,
                        "trait_count": len(o.genome.blueprint.get("traits", [])),
                    }
                    for o in population
                ],
                "best": population[0].name,
                "best_fitness": round(fitness_map[id(population[0])], 4),
            }
            yield f"data: {json.dumps(gen_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.5)

            if gen == generations:
                break

            n_survivors = max(2, len(population) // 2)
            survivors = population[:n_survivors]
            elites = population[:1]

            new_orgs = []
            for _ in range(population_size - 1):
                if len(survivors) >= 2:
                    p1, p2 = random.sample(survivors, 2)
                    child_g = Genome.crossover(p1.genome, p2.genome)
                    child_g.mutate()
                    try:
                        child_org = Embryo.develop(child_g)
                        child_org.generation = gen + 1
                        new_orgs.append(child_org)
                    except:
                        pass

            population = list(elites) + new_orgs
            population = population[:population_size]

        for org in population:
            genomes_store[org.name] = org.genome
            organisms_store[org.name] = org

        final = {
            "done": True,
            "best": organism_to_info(population[0]) if population else None,
            "population_size": len(population),
        }
        yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/organisms")
def list_organisms():
    return {"organisms": [organism_to_info(o) for o in organisms_store.values()]}


@app.post("/api/discover")
async def discover_tools(request: Request):
    """调用 DiscoveryCell 发现工具"""
    body = await request.json()
    task = body.get("task", "")
    source = body.get("source", "all")

    try:
        from ai_embryo.cells.discovery_cell import DiscoveryCell

        cell = DiscoveryCell(
            {
                "source": source,
                "max_tools": 10,
                "preference_domains": [],
            }
        )
        result = cell.process({"task": task})
        return result
    except Exception as e:
        return {
            "available_tools": [],
            "recommended_tools": [],
            "response": f"Discovery error: {str(e)}",
            "source": source,
            "task": task,
        }


@app.post("/api/chat")
async def chat_with_organism(request: Request):
    body = await request.json()
    name = body.get("name", "")
    message = body.get("message", "")

    pkg = _get_or_create_package(name)
    org = organisms_store.get(name)

    if not pkg and not org:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    if name not in chat_history:
        chat_history[name] = []

    history = chat_history[name]
    evolution_signal = {"triggered": False}

    if _has_any_api_key():
        if pkg:
            system_prompt = pkg.compile_system_prompt()
            cell = RealLLMCell({"system_prompt": system_prompt})
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": message})
            result = cell.process({"messages": messages})
        else:
            result = _run_with_real_llm(
                org, {"input": message, "message": message}, history=history
            )

        history.append({"role": "user", "content": message})
        resp_text = result.get("response", "...")
        history.append({"role": "assistant", "content": resp_text})

        if pkg:
            pkg.update_memory({"user": message, "assistant": resp_text})

            if len(history) >= 3 and len(history) % 3 == 0:
                reflection_result = await _trigger_reflection(name, pkg, history)
                if reflection_result:
                    evolution_signal = {
                        "triggered": True,
                        "summary": f"学会了新知识，自评分数 {reflection_result.get('fitness_self_score', 0.5):.2f}",
                        "fitness_delta": reflection_result.get(
                            "fitness_self_score", 0.5
                        )
                        - 0.5,
                    }

        if len(history) > 50:
            chat_history[name] = history[-50:]
    else:
        if org:
            result = org.run({"input": message, "message": message})
        else:
            result = {"response": "No organism found and no API key configured"}

    return {
        "status": "ok",
        "response": result.get("response", "..."),
        "meta": result.get("_meta", {}),
        "evolution_signal": evolution_signal,
    }


# ── Organism Package API ──────────────────────────────────


@app.post("/api/genomes")
async def create_genome(request: Request):
    """Create new genome - uses OrganismPackage when package-based creation is requested."""
    body = await request.json()

    use_package = body.get("use_package", False)
    name = body.get("name", "")
    purpose = body.get("purpose", "")
    persona = body.get("persona", {})

    if use_package and name and purpose:
        pkg = OrganismPackage.create(
            base_dir=ORGANISMS_DIR / name,
            name=name,
            purpose=purpose,
            persona_config=persona,
        )
        package_store[pkg.name] = pkg
        return {"status": "ok", "package": pkg.to_info()}

    if isinstance(body, str):
        data = yaml.safe_load(body)
    elif "yaml" in body:
        data = yaml.safe_load(body["yaml"])
    else:
        data = body

    try:
        g = Genome.from_dict(data)

        discovered_tools = body.get("discovered_tools", [])
        for tool in discovered_tools:
            tool_name = tool.get("name", "")
            g.blueprint.setdefault("traits", []).append(
                {
                    "id": f"tool_{tool_name.replace(' ', '_').lower()}",
                    "type": "tool:function",
                    "name": tool_name,
                    "config": {
                        "function_name": tool_name.replace(" ", "_").lower(),
                        "description": tool.get("description", ""),
                        "source": tool.get("source", "clawhub"),
                    },
                    "weight": 0.6,
                }
            )

        genomes_store[g.name] = g
        return {"status": "ok", "genome": genome_to_info(g)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/organisms")
def list_organisms():
    """List all organisms from filesystem packages."""
    organisms = []
    for name, pkg in package_store.items():
        organisms.append(pkg.to_info())
    for name, org in organisms_store.items():
        if name not in package_store:
            organisms.append(organism_to_info(org))
    return {"organisms": organisms}


@app.get("/api/organisms/{name}/package")
def get_organism_package(name: str):
    """Get full package info for an organism."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")
    return pkg.to_info()


@app.get("/api/organisms/{name}/soul")
def get_organism_soul(name: str):
    """Get SOUL.md content for an organism."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")
    return {"name": name, "soul": pkg.read_soul()}


@app.put("/api/organisms/{name}/soul")
async def update_organism_soul(name: str, request: Request):
    """Update SOUL.md content for an organism."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    body = await request.json()
    content = body.get("soul", "")
    pkg.write_soul(content)
    return {"status": "ok", "name": name}


@app.get("/api/organisms/{name}/mind")
def get_organism_mind(name: str):
    """Get MIND.md content for an organism."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")
    return {"name": name, "mind": pkg.read_mind()}


@app.put("/api/organisms/{name}/mind")
async def update_organism_mind(name: str, request: Request):
    """Update MIND.md content for an organism."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    body = await request.json()
    content = body.get("mind", "")
    pkg.write_mind(content)
    return {"status": "ok", "name": name}


@app.get("/api/organisms/{name}/values")
def get_organism_values(name: str):
    """Get VALUES.md content for an organism."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")
    return {"name": name, "values": pkg.read_values()}


@app.put("/api/organisms/{name}/values")
async def update_organism_values(name: str, request: Request):
    """Update VALUES.md content for an organism."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    body = await request.json()
    content = body.get("values", "")
    pkg.write_values(content)
    return {"status": "ok", "name": name}


@app.post("/api/organisms/{name}/feedback")
async def submit_feedback(name: str, request: Request):
    """Submit feedback for an organism to trigger reflection and DNA update."""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    body = await request.json()
    feedback = body.get("feedback", "")
    rating = body.get("rating", 0)

    reflection_content = f"# 反馈反思\n\n"
    reflection_content += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    reflection_content += f"反馈类型: {'👍 好评' if rating > 0 else '👎 差评' if rating < 0 else '文字反馈'}\n\n"
    if feedback:
        reflection_content += f"反馈内容: {feedback}\n\n"
    reflection_content += f"触发反思: 请分析这次反馈，考虑是否需要更新DNA。\n"

    pkg.add_reflection(reflection_content)

    return {"status": "ok", "message": "Feedback recorded"}


@app.post("/api/organisms/{name}/instruct")
async def instruct_organism(name: str, request: Request):
    """用户通过自然语言指令让生命体进化"""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    body = await request.json()
    instruction = body.get("instruction", "")

    if not instruction:
        raise HTTPException(status_code=400, detail="instruction is required")

    try:
        result = await evolution_engine.instruct(pkg, instruction)
        if result:
            changes = {}
            if result.get("soul_update"):
                pkg.write_soul(result["soul_update"])
                changes["soul"] = result["soul_update"]
            if result.get("mind_update"):
                pkg.write_mind(result["mind_update"])
                changes["mind"] = result["mind_update"]
            if result.get("values_update"):
                pkg.write_values(result["values_update"])
                changes["values"] = result["values_update"]

            if changes:
                pkg.add_changelog(
                    "指令进化",
                    changes,
                    result.get("reasoning", ""),
                )

            return {
                "status": "ok",
                "changes": changes,
                "reasoning": result.get("reasoning", ""),
                "changes_summary": result.get("changes_summary", ""),
            }
        return {
            "status": "ok",
            "changes": {},
            "reasoning": "No result from evolution engine",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instruct error: {e}")


def _get_or_create_package(name: str) -> OrganismPackage | None:
    """Get package from store, or auto-create from genome-based organism."""
    pkg = package_store.get(name)
    if pkg:
        return pkg
    org = organisms_store.get(name)
    if not org:
        return None
    pkg = OrganismPackage.create(
        base_dir=ORGANISMS_DIR / name,
        name=name,
        purpose=org.genome.identity.get("purpose", ""),
        persona_config={"type": "custom"},
    )
    try:
        prompt = org.genome.compile_system_prompt()
        if prompt:
            pkg.write_soul(prompt[:2000])
        mind = org.genome.identity.get("mind", {})
        if mind:
            import json as _json
            pkg.write_mind(f"# 思维系统\n\n```yaml\n{yaml.dump(mind, allow_unicode=True)}```")
    except Exception:
        pass
    package_store[name] = pkg
    return pkg


@app.get("/api/organisms/{name}/evolution")
def get_organism_evolution(name: str):
    """返回完整进化档案"""
    pkg = _get_or_create_package(name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    return {
        "name": name,
        "changelog": pkg.get_changelog(),
        "stats": pkg.get_evolution_stats(),
        "reflections": pkg._memory_reflections,
        "fitness": pkg.fitness,
    }


# ── Static files ───────────────────────────────────────────


@app.get("/")
def serve_index():
    index = WEB_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>web/index.html not found</h1>", status_code=404)


if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")


if __name__ == "__main__":
    print("🧬 AI Embryo Engine — Petri Dish")
    port = config.get("server.port", 8010)
    host = config.get("server.host", "0.0.0.0")
    print(f"   http://localhost:{port}/")
    register_llm_cell()
    uvicorn.run(app, host=host, port=port)
