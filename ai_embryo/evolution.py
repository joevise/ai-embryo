"""
Evolution — 进化引擎

在种群层面驱动进化：评估 → 选择 → 交配 → 变异 → 发育 → 循环
"""

from __future__ import annotations

import copy
import logging
import random
from typing import Any, Callable

from .genome import Genome
from .organism import Organism
from .embryo import Embryo
from .fitness import FitnessEvaluator, Task
from .exceptions import EvolutionError

logger = logging.getLogger("ai_embryo.evolution")


class EvolutionEngine:
    """进化引擎 — 物竞天择，适者生存
    
    核心循环：
        1. 评估（Evaluate）— 每个个体跑任务打分
        2. 选择（Select）  — 保留优秀个体
        3. 交配（Crossover）— 优秀个体配对产生后代
        4. 变异（Mutate）   — 基因组随机扰动
        5. 发育（Develop）  — 新基因组 → 新生命体
        6. 淘汰             — 控制种群规模
    """

    def __init__(
        self,
        evaluator: FitnessEvaluator | None = None,
        on_generation: Callable[[int, list[Organism]], None] | None = None,
    ):
        """
        Args:
            evaluator: 适应度评估器，默认使用内置评估器
            on_generation: 每代回调函数，用于日志/监控
        """
        self.evaluator = evaluator or FitnessEvaluator()
        self.on_generation = on_generation

    def evolve(
        self,
        population: list[Organism],
        tasks: list[Task],
        generations: int = 10,
        population_size: int = 8,
        selection_ratio: float = 0.5,
        elitism: int = 1,
    ) -> Organism:
        """进化主循环
        
        Args:
            population: 初始种群
            tasks: 评估任务集
            generations: 迭代代数
            population_size: 种群大小上限
            selection_ratio: 选择比例（保留多少比例的个体）
            elitism: 精英保留数（直接进入下一代的最优个体数）
            
        Returns:
            最优生命体
            
        Raises:
            EvolutionError: 进化失败
        """
        if not population:
            raise EvolutionError("初始种群不能为空")
        if not tasks:
            raise EvolutionError("评估任务不能为空")

        logger.info(
            f"🧬 进化开始: {len(population)} 个体, {len(tasks)} 任务, "
            f"{generations} 代, 种群上限 {population_size}"
        )

        best_ever: Organism | None = None

        for gen in range(1, generations + 1):
            logger.info(f"── Generation {gen}/{generations} ──")

            # 1. 评估
            fitness_map = {}
            for org in population:
                score = self.evaluator.evaluate(org, tasks)
                fitness_map[id(org)] = score
                logger.debug(f"  {org.name}: fitness={score:.4f}")

            # 按适应度排序
            population.sort(key=lambda o: fitness_map[id(o)], reverse=True)

            # 记录当代最优
            gen_best = population[0]
            gen_best_score = fitness_map[id(gen_best)]
            logger.info(
                f"  🏆 Gen {gen} 最优: {gen_best.name} "
                f"(fitness={gen_best_score:.4f})"
            )

            if best_ever is None or gen_best_score > best_ever.latest_fitness:
                best_ever = gen_best

            # 回调
            if self.on_generation:
                self.on_generation(gen, population)

            # 最后一代不需要再进化
            if gen == generations:
                break

            # 2. 选择
            n_survivors = max(2, int(len(population) * selection_ratio))
            survivors = population[:n_survivors]

            # 3. 精英保留
            elites = population[:elitism]

            # 4. 交配产生后代
            offspring_genomes = self._crossover_pool(survivors, population_size - elitism)

            # 5. 变异
            for genome in offspring_genomes:
                genome.mutate()

            # 6. 发育
            new_organisms = []
            for genome in offspring_genomes:
                try:
                    org = Embryo.develop(genome)
                    org.generation = gen + 1
                    new_organisms.append(org)
                except Exception as e:
                    logger.warning(f"  ⚠️ 发育失败: {e}")
                    # 交配失败 — 自然现象，跳过

            # 7. 组建新种群
            population = list(elites) + new_organisms
            population = population[:population_size]

            logger.info(
                f"  种群更新: {len(elites)} 精英 + "
                f"{len(new_organisms)} 后代 = {len(population)} 个体"
            )

        logger.info(
            f"🎉 进化完成! 最优: {best_ever.name} "
            f"(fitness={best_ever.latest_fitness:.4f})"
        )

        return best_ever

    # ── 内部方法 ──────────────────────────────────────────

    def _crossover_pool(
        self,
        parents: list[Organism],
        n_offspring: int,
    ) -> list[Genome]:
        """从父代池中交配产生 n 个后代基因组"""
        offspring = []

        for _ in range(n_offspring):
            if len(parents) < 2:
                # 种群太小，用变异代替交配
                parent = random.choice(parents)
                child = copy.deepcopy(parent.genome)
                child.name = f"{parent.name}_clone"
                offspring.append(child)
            else:
                # 随机选两个不同的父代
                p1, p2 = random.sample(parents, 2)
                child = Genome.crossover(p1.genome, p2.genome)
                offspring.append(child)

        return offspring
