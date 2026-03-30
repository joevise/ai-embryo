"""
Genome — AI 的遗传密码

两层结构：
    Identity Genes（身份基因）— 稳定，定义 "我是谁"
    Blueprint Genes（蓝图基因）— 可变，定义 "我怎么工作"

基因组是 YAML/JSON 文件，人类可读、可编辑、可版本控制。
所有进化操作（交叉、变异）都在基因组层面进行。
"""

from __future__ import annotations

import copy
import json
import random
import re
from pathlib import Path
from typing import Any

import yaml

from .exceptions import GenomeError, GenomeValidationError


class Genome:
    """基因组 — AI 生命体的遗传密码
    
    Attributes:
        name: 名称
        version: 版本
        identity: 身份基因（稳定）
        blueprint: 蓝图基因（可变）
        fitness: 最新适应度评分
    """

    def __init__(
        self,
        name: str = "unnamed",
        version: str = "1.0.0",
        identity: dict[str, Any] | None = None,
        blueprint: dict[str, Any] | None = None,
    ):
        self.name = name
        self.version = version
        self.identity = identity or self._default_identity()
        self.blueprint = blueprint or self._default_blueprint()
        self.fitness: float = 0.0

    # ── 工厂方法 ──────────────────────────────────────────

    @classmethod
    def from_file(cls, path: str | Path) -> Genome:
        """从 YAML/JSON 文件加载基因组"""
        path = Path(path)
        if not path.exists():
            raise GenomeError(f"基因组文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                raise GenomeError(f"不支持的文件格式: {path.suffix}")

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Genome:
        """从字典创建基因组"""
        genome = cls(
            name=data.get("name", "unnamed"),
            version=data.get("version", "1.0.0"),
            identity=data.get("identity"),
            blueprint=data.get("blueprint"),
        )
        genome.validate()
        return genome

    # ── 序列化 ────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """转为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "identity": copy.deepcopy(self.identity),
            "blueprint": copy.deepcopy(self.blueprint),
        }

    def save(self, path: str | Path) -> None:
        """保存为 YAML 文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.to_dict(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
            )

    # ── 验证 ──────────────────────────────────────────────

    def validate(self) -> bool:
        """验证基因组有效性
        
        Raises:
            GenomeValidationError: 验证失败
        """
        # 基础字段
        if not self.name or not isinstance(self.name, str):
            raise GenomeValidationError("name 必须是非空字符串")

        # 身份基因
        identity = self.identity
        if not isinstance(identity, dict):
            raise GenomeValidationError("identity 必须是字典")
        purpose = identity.get("purpose", "")
        if not isinstance(purpose, str) or not purpose.strip():
            raise GenomeValidationError("identity.purpose 不能为空")

        # 蓝图基因
        bp = self.blueprint
        if not isinstance(bp, dict):
            raise GenomeValidationError("blueprint 必须是字典")

        # capabilities
        caps = bp.get("capabilities", {})
        if not isinstance(caps, dict):
            raise GenomeValidationError("blueprint.capabilities 必须是字典")

        # cells 定义
        cells = bp.get("cells", [])
        if not isinstance(cells, list):
            raise GenomeValidationError("blueprint.cells 必须是列表")
        for i, cell_def in enumerate(cells):
            if not isinstance(cell_def, dict):
                raise GenomeValidationError(f"blueprint.cells[{i}] 必须是字典")
            if "type" not in cell_def:
                raise GenomeValidationError(f"blueprint.cells[{i}] 缺少 type 字段")

        # assembly
        assembly = bp.get("assembly", "sequential")
        valid_assemblies = {"sequential", "parallel", "conditional"}
        if assembly not in valid_assemblies:
            raise GenomeValidationError(
                f"blueprint.assembly 必须是 {valid_assemblies} 之一，got '{assembly}'"
            )

        # evolution
        evo = bp.get("evolution", {})
        if isinstance(evo, dict):
            mr = evo.get("mutation_rate", 0.1)
            if not (0.0 <= mr <= 1.0):
                raise GenomeValidationError("evolution.mutation_rate 必须在 0.0-1.0 之间")

        return True

    # ── 变量引用解析 ──────────────────────────────────────

    def resolve_references(self, config: dict[str, Any]) -> dict[str, Any]:
        """解析配置中的 ${} 变量引用
        
        Examples:
            config = {"model": "${capabilities.model}"}
            → {"model": "gpt-4"}  (从 blueprint.capabilities.model 取值)
        """
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str) and "${" in value:
                resolved[key] = self._resolve_ref(value)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_references(value)
            else:
                resolved[key] = value
        return resolved

    def _resolve_ref(self, value: str) -> Any:
        """解析单个 ${path} 引用"""
        pattern = r"\$\{([^}]+)\}"
        match = re.fullmatch(pattern, value.strip())
        if match:
            path = match.group(1)
            return self._get_by_path(path)
        # 如果是部分替换（字符串中嵌入引用），做字符串替换
        def replacer(m):
            return str(self._get_by_path(m.group(1)))
        return re.sub(pattern, replacer, value)

    def _get_by_path(self, path: str) -> Any:
        """通过点分路径获取值，先查 blueprint 再查 identity"""
        for root in [self.blueprint, self.identity]:
            try:
                obj = root
                for part in path.split("."):
                    if isinstance(obj, dict):
                        obj = obj[part]
                    elif isinstance(obj, list):
                        obj = obj[int(part)]
                    else:
                        raise KeyError
                return obj
            except (KeyError, IndexError, ValueError, TypeError):
                continue
        raise GenomeError(f"无法解析引用: ${{{path}}}")

    # ── 进化操作 ──────────────────────────────────────────

    @staticmethod
    def crossover(a: Genome, b: Genome) -> Genome:
        """基因交叉 — 两个基因组产生一个子代
        
        规则：
        - identity 从适应度更高的父代继承
        - blueprint 中每个可变字段随机从两个父代选择
        - 不可变字段从主导父代继承
        
        Args:
            a: 父代A
            b: 父代B
            
        Returns:
            子代基因组
        """
        # 确定主导父代
        dominant = a if a.fitness >= b.fitness else b
        recessive = b if dominant is a else a

        child = Genome()
        child.name = f"{dominant.name}×{recessive.name}"
        child.version = "1.0.0"

        # 身份基因：从主导父代继承
        child.identity = copy.deepcopy(dominant.identity)

        # 蓝图基因：逐字段交叉
        child.blueprint = copy.deepcopy(dominant.blueprint)
        
        # 获取可变字段列表
        mutable = set(
            dominant.blueprint.get("evolution", {}).get("mutable_fields", [])
        )
        
        # 对可变字段进行交叉
        recessive_bp = recessive.blueprint
        for field in mutable:
            if random.random() < 0.5:
                # 从隐性父代继承该字段
                try:
                    val = Genome._get_field(recessive_bp, field)
                    Genome._set_field(child.blueprint, field, copy.deepcopy(val))
                except (KeyError, IndexError):
                    pass  # 隐性父代没有此字段，保留主导父代的

        return child

    def mutate(self, mutation_rate: float | None = None) -> None:
        """对基因组进行变异（就地修改）
        
        Args:
            mutation_rate: 变异概率，None 则使用基因组内定义的值
        """
        evo = self.blueprint.get("evolution", {})
        rate = mutation_rate if mutation_rate is not None else evo.get("mutation_rate", 0.1)
        mutable = evo.get("mutable_fields", [])

        for field in mutable:
            if random.random() < rate:
                self._mutate_field(field)

    def _mutate_field(self, field_path: str) -> None:
        """对单个字段进行变异"""
        try:
            current = self._get_field(self.blueprint, field_path)
        except (KeyError, IndexError):
            return

        if isinstance(current, float):
            # 浮点数：在 ±20% 范围内波动
            delta = current * 0.2 * (random.random() * 2 - 1)
            new_val = max(0.0, min(1.0, current + delta))
            self._set_field(self.blueprint, field_path, round(new_val, 3))

        elif isinstance(current, int):
            # 整数：在 ±30% 范围内波动
            delta = max(1, int(current * 0.3))
            new_val = current + random.randint(-delta, delta)
            self._set_field(self.blueprint, field_path, max(1, new_val))

        elif isinstance(current, str):
            # 字符串类型的字段通常需要候选列表来变异
            # 暂时不做随机变异，留给用户通过 mutation_candidates 配置
            pass

        elif isinstance(current, list):
            # 列表：随机移除或复制一个元素
            if len(current) > 1 and random.random() < 0.5:
                current.pop(random.randint(0, len(current) - 1))
            elif current:
                current.append(copy.deepcopy(random.choice(current)))

    @staticmethod
    def _get_field(obj: dict, path: str) -> Any:
        """通过点分路径获取字段值"""
        for part in path.split("."):
            if isinstance(obj, dict):
                obj = obj[part]
            elif isinstance(obj, list):
                obj = obj[int(part)]
            else:
                raise KeyError(f"Cannot traverse into {type(obj)} at '{part}'")
        return obj

    @staticmethod
    def _set_field(obj: dict, path: str, value: Any) -> None:
        """通过点分路径设置字段值"""
        parts = path.split(".")
        for part in parts[:-1]:
            if isinstance(obj, dict):
                obj = obj.setdefault(part, {})
            elif isinstance(obj, list):
                obj = obj[int(part)]
            else:
                raise KeyError(f"Cannot traverse into {type(obj)} at '{part}'")
        
        last = parts[-1]
        if isinstance(obj, dict):
            obj[last] = value
        elif isinstance(obj, list):
            obj[int(last)] = value

    # ── 默认值 ────────────────────────────────────────────

    @staticmethod
    def _default_identity() -> dict[str, Any]:
        return {
            "purpose": "通用 AI 助手",
            "personality": ["helpful"],
            "language": "zh-CN",
            "constraints": [],
        }

    @staticmethod
    def _default_blueprint() -> dict[str, Any]:
        return {
            "capabilities": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
                "tools": [],
            },
            "cells": [
                {"type": "LLMCell", "config": {}},
            ],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.1,
                "fitness_metrics": ["accuracy"],
                "mutable_fields": [
                    "capabilities.temperature",
                    "capabilities.max_tokens",
                ],
            },
        }

    # ── 魔术方法 ──────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Genome(name='{self.name}', version='{self.version}', fitness={self.fitness:.3f})"

    def __str__(self) -> str:
        purpose = self.identity.get("purpose", "?")
        n_cells = len(self.blueprint.get("cells", []))
        return f"🧬 {self.name} v{self.version} | {purpose} | {n_cells} cells | fitness={self.fitness:.3f}"
