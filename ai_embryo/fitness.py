"""
Fitness — 适应度评估

评估一个 Organism 在给定任务上的表现。
适应度是进化的驱动力——分数高的个体有更大的交配权。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .organism import Organism


@dataclass
class Task:
    """评估任务
    
    Attributes:
        input: 给生命体的输入
        expected: 期望输出（用于评估准确性）
        name: 任务名称
        weight: 任务权重（默认1.0）
    """
    input: dict[str, Any]
    expected: str = ""
    name: str = ""
    weight: float = 1.0


class FitnessEvaluator:
    """适应度评估器
    
    支持多种评估维度：
    - accuracy: 输出与期望的匹配度
    - speed: 响应速度
    - length: 输出长度合理性
    - custom: 用户自定义评估函数
    """

    def __init__(
        self,
        custom_scorers: dict[str, Callable] | None = None,
    ):
        """
        Args:
            custom_scorers: 自定义评分函数字典
                key: 指标名称
                value: 函数签名 (result: dict, task: Task) -> float (0.0-1.0)
        """
        self._scorers: dict[str, Callable] = {
            "accuracy": self._score_accuracy,
            "speed": self._score_speed,
            "length": self._score_length,
        }
        if custom_scorers:
            self._scorers.update(custom_scorers)

    def evaluate(self, organism: Organism, tasks: list[Task]) -> float:
        """评估一个生命体的适应度
        
        Args:
            organism: 要评估的生命体
            tasks: 评估任务列表
            
        Returns:
            综合适应度分数 (0.0 - 1.0)
        """
        # 获取基因组定义的评估指标
        metrics = organism.genome.blueprint.get("evolution", {}).get(
            "fitness_metrics", ["accuracy"]
        )

        all_scores: list[float] = []

        for task in tasks:
            # 运行任务
            start = time.time()
            result = organism.run(task.input)
            elapsed = time.time() - start

            # 附加时间信息
            result["_eval_elapsed"] = elapsed

            # 按指标打分
            task_scores = []
            for metric in metrics:
                scorer = self._scorers.get(metric)
                if scorer:
                    score = scorer(result, task)
                    task_scores.append(max(0.0, min(1.0, score)))

            if task_scores:
                # 任务的加权分数
                task_avg = sum(task_scores) / len(task_scores)
                all_scores.append(task_avg * task.weight)

        # 综合分数
        if not all_scores:
            total = 0.0
        else:
            total_weight = sum(t.weight for t in tasks)
            total = sum(all_scores) / total_weight if total_weight > 0 else 0.0

        # 记录到 Organism
        organism.fitness_history.append(round(total, 4))
        organism.genome.fitness = round(total, 4)

        return total

    # ── 内置评分函数 ──────────────────────────────────────

    @staticmethod
    def _score_accuracy(result: dict, task: Task) -> float:
        """评估准确性：响应与期望的重叠度"""
        if not task.expected:
            return 0.5  # 没有期望值时给中间分

        response = str(result.get("response", ""))
        expected = task.expected

        if not response:
            return 0.0

        # 关键词匹配：期望文本中的词在响应中出现的比例
        expected_words = set(expected.lower().split())
        response_lower = response.lower()

        if not expected_words:
            return 0.5

        matches = sum(1 for w in expected_words if w in response_lower)
        return matches / len(expected_words)

    @staticmethod
    def _score_speed(result: dict, task: Task) -> float:
        """评估速度：越快分数越高"""
        elapsed = result.get("_eval_elapsed", result.get("_meta", {}).get("elapsed", 10))
        
        # 1秒以内满分，10秒以上0分，线性插值
        if elapsed <= 1.0:
            return 1.0
        elif elapsed >= 10.0:
            return 0.0
        else:
            return 1.0 - (elapsed - 1.0) / 9.0

    @staticmethod
    def _score_length(result: dict, task: Task) -> float:
        """评估输出长度合理性"""
        response = str(result.get("response", ""))
        length = len(response)

        # 太短或太长都扣分，50-500 字符是最佳区间
        if length < 10:
            return 0.1
        elif length < 50:
            return 0.5
        elif length <= 500:
            return 1.0
        elif length <= 2000:
            return 0.7
        else:
            return 0.4
