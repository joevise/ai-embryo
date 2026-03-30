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
    Genome, Cell, CellRegistry, Organism, Embryo,
    EvolutionEngine, FitnessEvaluator, Task,
)

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


# ── App Setup ──────────────────────────────────────────────

app = FastAPI(title="AI Embryo Engine — Petri Dish")

PROJECT_ROOT = Path(__file__).parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
WEB_DIR = PROJECT_ROOT / "web"

# Runtime storage
genomes_store: dict[str, Genome] = {}
organisms_store: dict[str, Organism] = {}


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
        "traits": [{"id": t.get("id", ""), "type": t.get("type", ""), "name": t.get("name", ""), "weight": t.get("weight", 0.5)} for t in traits],
        "trait_count": len(traits),
        "model_config": g.blueprint.get("model_config", {}),
        "constraints": g.identity.get("constraints", []),
        "evolution": g.blueprint.get("evolution", {}),
        "raw": g.to_dict(),
    }


def organism_to_info(o: Organism) -> dict:
    """Convert organism to API-friendly dict."""
    info = genome_to_info(o.genome)
    info.update({
        "generation": o.generation,
        "fitness_history": o.fitness_history,
        "birth_time": o.birth_time,
        "age": round(o.age, 1),
        "run_count": o._run_count,
        "cell_count": len(o.cells),
        "assembly": o.assembly,
    })
    return info


# ── API Routes ─────────────────────────────────────────────

@app.get("/api/genomes")
def list_genomes():
    return {"genomes": [genome_to_info(g) for g in genomes_store.values()]}


@app.post("/api/genomes")
async def create_genome(request: Request):
    body = await request.json()
    # body can be raw YAML string or dict
    if isinstance(body, str):
        data = yaml.safe_load(body)
    elif "yaml" in body:
        data = yaml.safe_load(body["yaml"])
    else:
        data = body

    try:
        g = Genome.from_dict(data)
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

    result = org.run(input_data)
    return {"status": "ok", "result": result}


@app.post("/api/crossover")
async def crossover_genomes(request: Request):
    body = await request.json()
    name_a = body.get("parent_a", "")
    name_b = body.get("parent_b", "")

    ga = genomes_store.get(name_a)
    gb = genomes_store.get(name_b)
    if not ga:
        raise HTTPException(status_code=404, detail=f"Genome '{name_a}' not found")
    if not gb:
        raise HTTPException(status_code=404, detail=f"Genome '{name_b}' not found")

    try:
        child = Genome.crossover(ga, gb)
        child.fitness = (ga.fitness + gb.fitness) / 2 * random.uniform(0.8, 1.2)
        genomes_store[child.name] = child
        # Auto-develop
        org = Embryo.develop(child)
        org.generation = max(
            organisms_store.get(name_a, Organism(ga, [])).generation,
            organisms_store.get(name_b, Organism(gb, [])).generation,
        ) + 1
        organisms_store[child.name] = org
        return {"status": "ok", "child": organism_to_info(org)}
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
        return {"status": "ok", "mutated": organism_to_info(org)}
    except Exception as e:
        return {"status": "ok", "mutated": genome_to_info(mutated), "develop_error": str(e)}


@app.post("/api/evolve")
async def evolve_population(request: Request):
    body = await request.json()
    generations = body.get("generations", 5)
    population_size = body.get("population_size", 6)

    async def event_stream():
        # Build initial population from all organisms, or develop from genomes
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

        # Create simple tasks for evaluation
        tasks = [
            Task(input={"input": "分析当前AI技术的发展趋势"}, expected="AI 技术 趋势 发展 大模型", name="分析任务", weight=1.0),
            Task(input={"input": "提出一个创新的产品想法"}, expected="创新 产品 用户 体验 设计", name="创意任务", weight=1.0),
            Task(input={"input": "如何提高团队效率"}, expected="效率 团队 协作 流程 优化", name="效率任务", weight=1.0),
        ]

        evaluator = FitnessEvaluator()

        for gen in range(1, generations + 1):
            # Evaluate
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

            # Select top half
            n_survivors = max(2, len(population) // 2)
            survivors = population[:n_survivors]
            elites = population[:1]

            # Crossover
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

        # Update stores with final population
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


@app.post("/api/chat")
async def chat_with_organism(request: Request):
    body = await request.json()
    name = body.get("name", "")
    message = body.get("message", "")

    org = organisms_store.get(name)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organism '{name}' not found")

    result = org.run({"input": message, "message": message})
    return {
        "status": "ok",
        "response": result.get("response", "..."),
        "meta": result.get("_meta", {}),
    }


# ── Static files ───────────────────────────────────────────

@app.get("/")
def serve_index():
    index = WEB_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>web/index.html not found</h1>", status_code=404)


# Mount web dir for any other static assets
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")


if __name__ == "__main__":
    print("🧬 AI Embryo Engine — Petri Dish")
    print("   http://localhost:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
