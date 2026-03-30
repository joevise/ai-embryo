"""
Organism — 由基因组发育而来的可运行 AI 生命体

Organism = Genome + 已实例化的 Cells + 运行时状态
"""

from __future__ import annotations

import time
from typing import Any

from .cell import Cell
from .genome import Genome
from .exceptions import AIEmbryoError


class Organism:
    """生命体 — 从基因组发育而来的可运行 AI 实体
    
    Attributes:
        genome: 遗传密码
        cells: 已实例化的细胞列表
        assembly: 组装方式 (sequential/parallel/conditional)
        generation: 代数
        fitness_history: 适应度评分历史
        birth_time: 出生时间
    """

    def __init__(
        self,
        genome: Genome,
        cells: list[Cell],
        assembly: str = "sequential",
    ):
        self.genome = genome
        self.cells = cells
        self.assembly = assembly
        self.generation: int = 1
        self.fitness_history: list[float] = []
        self.birth_time: float = time.time()
        self._run_count: int = 0

    # ── 运行 ──────────────────────────────────────────────

    def run(self, input: dict[str, Any]) -> dict[str, Any]:
        """运行生命体处理输入
        
        根据 assembly 方式串联或并联 cells 执行。
        
        Args:
            input: 输入字典
            
        Returns:
            处理结果字典
        """
        self._run_count += 1
        start = time.time()

        try:
            if self.assembly == "sequential":
                result = self._run_sequential(input)
            elif self.assembly == "parallel":
                result = self._run_parallel(input)
            else:
                result = self._run_sequential(input)

            elapsed = time.time() - start
            result.setdefault("_meta", {})
            result["_meta"]["elapsed"] = round(elapsed, 3)
            result["_meta"]["run_count"] = self._run_count
            result["_meta"]["organism"] = self.genome.name
            result["_meta"]["generation"] = self.generation

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"生命体 {self.genome.name} 运行失败: {e}",
                "_meta": {
                    "elapsed": round(time.time() - start, 3),
                    "organism": self.genome.name,
                },
            }

    def _run_sequential(self, input: dict[str, Any]) -> dict[str, Any]:
        """顺序执行所有 Cell"""
        context = dict(input)

        for cell in self.cells:
            result = cell.process(context)
            
            # 将本步结果合并到上下文，供下一步使用
            if isinstance(result, dict):
                # 保留 response 作为下一步的可用输入
                if "response" in result:
                    context["previous_response"] = result["response"]
                # 合并其他字段
                for k, v in result.items():
                    if k not in ("_meta",):
                        context[k] = v

        # 最终结果取最后一个 Cell 的输出
        return result if isinstance(result, dict) else {"response": str(result)}

    def _run_parallel(self, input: dict[str, Any]) -> dict[str, Any]:
        """并行执行所有 Cell，合并结果"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}
        with ThreadPoolExecutor(max_workers=len(self.cells)) as executor:
            futures = {
                executor.submit(cell.process, dict(input)): cell
                for cell in self.cells
            }
            for future in as_completed(futures):
                cell = futures[future]
                cell_name = cell.__class__.__name__
                try:
                    results[cell_name] = future.result()
                except Exception as e:
                    results[cell_name] = {"error": str(e)}

        # 合并：优先取有 response 的结果
        merged = {"parallel_results": results}
        for name, res in results.items():
            if isinstance(res, dict) and "response" in res:
                merged["response"] = res["response"]
                break

        if "response" not in merged:
            merged["response"] = str(results)

        return merged

    # ── 属性 ──────────────────────────────────────────────

    @property
    def latest_fitness(self) -> float:
        """最新适应度"""
        return self.fitness_history[-1] if self.fitness_history else 0.0

    @property
    def name(self) -> str:
        return self.genome.name

    @property
    def age(self) -> float:
        """存活时间（秒）"""
        return time.time() - self.birth_time

    # ── 魔术方法 ──────────────────────────────────────────

    def __repr__(self) -> str:
        n = len(self.cells)
        return (
            f"Organism(name='{self.name}', gen={self.generation}, "
            f"cells={n}, fitness={self.latest_fitness:.3f})"
        )

    def __str__(self) -> str:
        n = len(self.cells)
        cell_types = [c.__class__.__name__ for c in self.cells]
        return (
            f"🦠 {self.name} (Gen {self.generation}) | "
            f"{n} cells: {cell_types} | "
            f"fitness={self.latest_fitness:.3f} | "
            f"runs={self._run_count}"
        )
