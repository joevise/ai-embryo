"""
Genome — AI 的遗传密码

两层结构：
    Identity Genes（身份基因）— 稳定，定义 "我是谁"
        - purpose: 存在意义
        - mind: 思维系统（认知/决策/表达/性格）
        - constraints: 底线约束
    Blueprint Genes（蓝图基因）— 可变，定义 "我怎么工作"
        - model_config: 模型参数
        - traits[]: 原子能力列表（提示词片段/工具/技能/记忆/行为规则）
        - cells[]: Cell 组成
        - assembly: 组装方式
        - evolution: 进化设置

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
        identity: 身份基因（稳定）— 包含 purpose, mind, constraints
        blueprint: 蓝图基因（可变）— 包含 model_config, traits, cells, evolution
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
        """验证基因组有效性"""
        if not self.name or not isinstance(self.name, str):
            raise GenomeValidationError("name 必须是非空字符串")

        # 身份基因
        identity = self.identity
        if not isinstance(identity, dict):
            raise GenomeValidationError("identity 必须是字典")
        purpose = identity.get("purpose", "")
        if not isinstance(purpose, str) or not purpose.strip():
            raise GenomeValidationError("identity.purpose 不能为空")

        # mind 验证（可选但推荐）
        mind = identity.get("mind", {})
        if mind and not isinstance(mind, dict):
            raise GenomeValidationError("identity.mind 必须是字典")

        # 蓝图基因
        bp = self.blueprint
        if not isinstance(bp, dict):
            raise GenomeValidationError("blueprint 必须是字典")

        # model_config
        mc = bp.get("model_config", {})
        if mc and not isinstance(mc, dict):
            raise GenomeValidationError("blueprint.model_config 必须是字典")

        # traits 验证
        traits = bp.get("traits", [])
        if not isinstance(traits, list):
            raise GenomeValidationError("blueprint.traits 必须是列表")
        trait_ids = set()
        for i, trait in enumerate(traits):
            if not isinstance(trait, dict):
                raise GenomeValidationError(f"traits[{i}] 必须是字典")
            if "type" not in trait:
                raise GenomeValidationError(f"traits[{i}] 缺少 type 字段")
            tid = trait.get("id", "")
            if tid:
                if tid in trait_ids:
                    raise GenomeValidationError(f"traits id 重复: '{tid}'")
                trait_ids.add(tid)

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
                f"blueprint.assembly 必须是 {valid_assemblies} 之一"
            )

        # evolution
        evo = bp.get("evolution", {})
        if isinstance(evo, dict):
            mr = evo.get("mutation_rate", 0.1)
            if not (0.0 <= mr <= 1.0):
                raise GenomeValidationError("evolution.mutation_rate 必须在 0.0-1.0 之间")

        return True

    # ── Trait 操作 ────────────────────────────────────────

    def get_traits(self, type_filter: str | None = None) -> list[dict]:
        """获取 traits，可按类型过滤
        
        Args:
            type_filter: 类型过滤，支持通配符如 "prompt:*", "tool:*"
        """
        traits = self.blueprint.get("traits", [])
        if not type_filter:
            return traits

        if type_filter.endswith(":*"):
            prefix = type_filter[:-1]  # "prompt:" 
            return [t for t in traits if t.get("type", "").startswith(prefix)]
        
        return [t for t in traits if t.get("type") == type_filter]

    def get_trait_by_id(self, trait_id: str) -> dict | None:
        """通过 id 获取 trait"""
        for t in self.blueprint.get("traits", []):
            if t.get("id") == trait_id:
                return t
        return None

    def compile_system_prompt(self) -> str:
        """从 identity.mind + prompt traits 编译完整的系统提示词
        
        这是 mind（内在本质）和 prompt traits（外在表达调整）的合并。
        """
        parts = []

        # 1. 从 mind 生成核心人格提示词
        mind = self.identity.get("mind", {})
        if mind:
            parts.append(self._compile_mind_prompt(mind))

        # 2. 从 identity 基础字段
        purpose = self.identity.get("purpose", "")
        if purpose:
            parts.append(f"你的核心目标: {purpose}")

        constraints = self.identity.get("constraints", [])
        if constraints:
            parts.append("底线约束:\n" + "\n".join(f"- {c}" for c in constraints))

        # 3. 收集 prompt:* traits，按 weight 排序
        prompt_traits = self.get_traits("prompt:*")
        prompt_traits.sort(key=lambda t: t.get("weight", 0.5), reverse=True)
        
        for trait in prompt_traits:
            content = trait.get("content", "")
            if content:
                name = trait.get("name", "")
                if name:
                    parts.append(f"[{name}]\n{content}")
                else:
                    parts.append(content)

        return "\n\n".join(parts)

    def compile_tools(self) -> list[dict]:
        """从 tool:function traits 编译 Function Calling 工具定义"""
        tools = []
        for trait in self.get_traits("tool:function"):
            config = trait.get("config", {})
            tool_def = {
                "type": "function",
                "function": {
                    "name": config.get("function_name", trait.get("id", "")),
                    "description": config.get("description", trait.get("name", "")),
                    "parameters": config.get("parameters", {}),
                },
            }
            tools.append(tool_def)
        return tools

    def _compile_mind_prompt(self, mind: dict) -> str:
        """从 mind 结构编译人格提示词"""
        sections = []

        # 认知模式
        cog = mind.get("cognition", {})
        if cog:
            cog_parts = []
            ts = cog.get("thinking_style", "")
            if ts:
                style_map = {
                    "analytical": "你的思维方式是分析型的，擅长拆解复杂问题",
                    "intuitive": "你的思维方式是直觉型的，擅长快速抓住本质",
                    "systematic": "你的思维方式是系统型的，擅长全局思考和结构化分析",
                    "creative": "你的思维方式是创造型的，擅长跳出常规寻找新视角",
                }
                cog_parts.append(style_map.get(ts, f"你的思维方式是{ts}"))

            reasoning = cog.get("reasoning", "")
            if reasoning:
                reason_map = {
                    "first_principles": "分析问题时从最基本的事实出发推理，不被表面现象迷惑",
                    "analogical": "善于通过类比来理解和解释复杂概念",
                    "data_driven": "决策和分析以数据为基础，用事实说话",
                    "empirical": "重视实践经验，从过往案例中提取规律",
                }
                cog_parts.append(reason_map.get(reasoning, f"推理方式偏向{reasoning}"))

            depth = cog.get("depth", "")
            if depth:
                depth_map = {
                    "surface": "回答简明扼要，抓住要点即可",
                    "moderate": "提供适度深度的分析",
                    "deep": "深入本质，提供有深度的洞察",
                    "philosophical": "从哲学层面思考问题的本质和意义",
                }
                cog_parts.append(depth_map.get(depth, f"思考深度为{depth}"))

            meta = cog.get("metacognition", {})
            if isinstance(meta, dict):
                if meta.get("self_awareness"):
                    cog_parts.append("你能意识到自己的知识边界和局限性")
                transparency = meta.get("thinking_transparency", "")
                if transparency == "always":
                    cog_parts.append("始终展示你的思维过程")
                elif transparency == "on_demand":
                    cog_parts.append("被问到时才详细展示思维过程")
                if meta.get("calibration"):
                    cog_parts.append("对自己的判断有准确的置信度感知")

            if cog_parts:
                sections.append("【认知模式】\n" + "\n".join(f"- {p}" for p in cog_parts))

        # 决策逻辑
        jdg = mind.get("judgment", {})
        if jdg:
            jdg_parts = []
            ds = jdg.get("decision_style", "")
            if ds:
                ds_map = {
                    "decisive": "做判断时果断直接，不拖泥带水",
                    "cautious": "做判断时审慎周全，考虑多种可能",
                    "collaborative": "倾向于与用户协商，共同做出决策",
                    "data_driven": "决策严格基于数据和证据",
                }
                jdg_parts.append(ds_map.get(ds, f"决策风格为{ds}"))

            rt = jdg.get("risk_tolerance", "")
            if rt:
                rt_map = {
                    "conservative": "风险偏好保守，优先选择稳妥方案",
                    "balanced": "风险偏好平衡，在收益和风险间寻找最优解",
                    "aggressive": "愿意承担风险，追求高收益方案",
                }
                jdg_parts.append(rt_map.get(rt, f"风险偏好为{rt}"))

            unc = jdg.get("uncertainty", "")
            if unc:
                unc_map = {
                    "acknowledge": "面对不确定性时坦诚承认不知道",
                    "lean_answer": "面对不确定性时倾向于给出最可能的答案",
                    "probabilistic": "面对不确定性时提供概率评估",
                }
                jdg_parts.append(unc_map.get(unc, f"面对不确定性的策略是{unc}"))

            priorities = jdg.get("priorities", [])
            if priorities:
                jdg_parts.append(f"判断优先级: {' > '.join(priorities)}")

            if jdg_parts:
                sections.append("【决策逻辑】\n" + "\n".join(f"- {p}" for p in jdg_parts))

        # 表达方式
        voice = mind.get("voice", {})
        if voice:
            voice_parts = []
            tone = voice.get("tone", "")
            if tone:
                tone_map = {
                    "serious": "语气严肃认真",
                    "warm": "语气温和友好",
                    "humorous": "语气风趣幽默",
                    "sharp": "语气犀利直接",
                }
                voice_parts.append(tone_map.get(tone, f"语气{tone}"))

            direct = voice.get("directness", "")
            if direct:
                d_map = {
                    "direct": "说话直来直去，不绕弯子",
                    "diplomatic": "表达委婉得体，照顾对方感受",
                    "socratic": "善用提问引导对方思考",
                }
                voice_parts.append(d_map.get(direct, f"表达方式{direct}"))

            verb = voice.get("verbosity", "")
            if verb:
                v_map = {
                    "minimal": "用最少的字说清楚事情",
                    "concise": "简洁明了，不废话",
                    "thorough": "详尽完整，不遗漏细节",
                }
                voice_parts.append(v_map.get(verb, f"详略偏好{verb}"))

            emo = voice.get("emotion", "")
            if emo:
                e_map = {
                    "restrained": "情感表达克制内敛",
                    "moderate": "情感表达适度自然",
                    "expressive": "情感丰富，善于共情",
                }
                voice_parts.append(e_map.get(emo, f"情感表达{emo}"))

            if voice_parts:
                sections.append("【表达方式】\n" + "\n".join(f"- {p}" for p in voice_parts))

        # 性格内核
        char = mind.get("character", {})
        if char:
            char_parts = []
            values = char.get("values", [])
            if values:
                char_parts.append(f"核心价值观: {'、'.join(values)}")

            temp = char.get("temperament", "")
            if temp:
                t_map = {
                    "calm": "性情沉稳",
                    "passionate": "性情热忱",
                    "cool": "性情冷静",
                    "lively": "性情活泼",
                }
                char_parts.append(t_map.get(temp, f"气质{temp}"))

            quirks = char.get("quirks", [])
            if quirks:
                char_parts.append("独特习惯:\n" + "\n".join(f"  · {q}" for q in quirks))

            wv = char.get("worldview", "")
            if wv:
                wv_map = {
                    "optimistic": "世界观乐观积极",
                    "realistic": "世界观务实理性",
                    "critical": "世界观批判性强",
                }
                char_parts.append(wv_map.get(wv, f"世界观{wv}"))

            if char_parts:
                sections.append("【性格内核】\n" + "\n".join(f"- {p}" for p in char_parts))

        if sections:
            return "=== 你的思维与人格 ===\n\n" + "\n\n".join(sections)
        return ""

    # ── 变量引用解析 ──────────────────────────────────────

    def resolve_references(self, config: dict[str, Any]) -> dict[str, Any]:
        """解析配置中的 ${} 变量引用"""
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
        """基因交叉 — Trait 级别的精细交叉
        
        规则：
        1. identity（含 mind）从主导父代继承
           - voice.tone/verbosity 和 character.quirks 有小概率（20%）从隐性父代混入
        2. model_config 逐字段随机选择
        3. traits 按原子级别交叉：
           - immutable_types 的 trait → 从主导父代
           - 同 id 的 trait → 保留（两边都有）
           - 同 type 不同 id → 随机选一个
           - 一方独有 → 50% 概率继承
        4. cells 和 assembly 从主导父代
        """
        dominant = a if a.fitness >= b.fitness else b
        recessive = b if dominant is a else a

        child = Genome()
        child.name = f"{dominant.name}×{recessive.name}"
        child.version = "1.0.0"

        # ── 1. 身份基因：从主导父代继承 ──
        child.identity = copy.deepcopy(dominant.identity)
        
        # voice 和 quirks 有小概率混入隐性父代的特质
        rec_mind = recessive.identity.get("mind", {})
        child_mind = child.identity.setdefault("mind", {})
        
        if rec_mind.get("voice") and random.random() < 0.2:
            rec_voice = rec_mind["voice"]
            child_voice = child_mind.setdefault("voice", {})
            # 随机挑一个 voice 属性混入
            mixable = ["tone", "verbosity", "emotion"]
            pick = random.choice(mixable)
            if pick in rec_voice:
                child_voice[pick] = rec_voice[pick]

        if rec_mind.get("character", {}).get("quirks") and random.random() < 0.2:
            rec_quirks = rec_mind["character"]["quirks"]
            child_char = child_mind.setdefault("character", {})
            child_quirks = child_char.setdefault("quirks", [])
            # 从隐性父代加入一个 quirk
            new_quirk = random.choice(rec_quirks)
            if new_quirk not in child_quirks:
                child_quirks.append(new_quirk)

        # ── 2. 蓝图基因 ──
        child.blueprint = copy.deepcopy(dominant.blueprint)

        # model_config 逐字段交叉
        rec_mc = recessive.blueprint.get("model_config", {})
        child_mc = child.blueprint.setdefault("model_config", {})
        for key in set(list(child_mc.keys()) + list(rec_mc.keys())):
            if key in rec_mc and random.random() < 0.5:
                child_mc[key] = copy.deepcopy(rec_mc[key])

        # ── 3. Trait 级别交叉 ──
        evo = dominant.blueprint.get("evolution", {})
        te = evo.get("trait_evolution", {})
        immutable_types = set(te.get("immutable_types", ["prompt:role", "behavior:guard"]))

        dom_traits = dominant.blueprint.get("traits", [])
        rec_traits = recessive.blueprint.get("traits", [])

        child_traits = Genome._crossover_traits(dom_traits, rec_traits, immutable_types)
        child.blueprint["traits"] = child_traits

        return child

    @staticmethod
    def _crossover_traits(
        dom_traits: list[dict],
        rec_traits: list[dict],
        immutable_types: set[str],
    ) -> list[dict]:
        """Trait 级别的交叉逻辑"""
        result = []
        used_rec_ids = set()

        # 索引隐性父代 traits
        rec_by_id = {}
        rec_by_type: dict[str, list[dict]] = {}
        for t in rec_traits:
            tid = t.get("id", "")
            if tid:
                rec_by_id[tid] = t
            ttype = t.get("type", "")
            rec_by_type.setdefault(ttype, []).append(t)

        for trait in dom_traits:
            tid = trait.get("id", "")
            ttype = trait.get("type", "")

            # immutable → 直接从主导父代继承
            if ttype in immutable_types:
                result.append(copy.deepcopy(trait))
                if tid:
                    used_rec_ids.add(tid)
                continue

            # 同 id 存在于隐性父代 → 保留主导的（都有）
            if tid and tid in rec_by_id:
                result.append(copy.deepcopy(trait))
                used_rec_ids.add(tid)
                continue

            # 同 type 不同 id → 随机选一个
            rec_same_type = [
                t for t in rec_by_type.get(ttype, [])
                if t.get("id", "") not in used_rec_ids
            ]
            if rec_same_type and random.random() < 0.5:
                picked = random.choice(rec_same_type)
                result.append(copy.deepcopy(picked))
                picked_id = picked.get("id", "")
                if picked_id:
                    used_rec_ids.add(picked_id)
            else:
                result.append(copy.deepcopy(trait))

            if tid:
                used_rec_ids.add(tid)

        # 隐性父代独有的 trait → 50% 概率继承
        for trait in rec_traits:
            tid = trait.get("id", "")
            ttype = trait.get("type", "")
            if tid and tid in used_rec_ids:
                continue
            if ttype in immutable_types:
                continue  # 不从隐性父代继承 immutable
            if random.random() < 0.5:
                result.append(copy.deepcopy(trait))

        return result

    def mutate(self, mutation_rate: float | None = None) -> None:
        """对基因组进行变异（就地修改）
        
        变异操作：
        1. model_config 数值参数微调
        2. mutable traits 的 weight/content 修改
        3. 可能增删 trait
        """
        evo = self.blueprint.get("evolution", {})
        rate = mutation_rate if mutation_rate is not None else evo.get("mutation_rate", 0.1)

        # model_config 变异
        mc = self.blueprint.get("model_config", {})
        for key, val in list(mc.items()):
            if random.random() < rate:
                mc[key] = self._mutate_value(val)

        # trait 变异
        te = evo.get("trait_evolution", {})
        mutable_types = set(te.get("mutable_types", [
            "prompt:style", "prompt:format", "prompt:reasoning",
            "prompt:knowledge", "tool:function", "skill",
            "memory", "behavior:trigger", "behavior:workflow",
        ]))
        immutable_types = set(te.get("immutable_types", ["prompt:role", "behavior:guard"]))

        traits = self.blueprint.get("traits", [])
        for trait in traits:
            ttype = trait.get("type", "")
            if ttype in immutable_types:
                continue
            if ttype not in mutable_types:
                continue
            if random.random() < rate:
                self._mutate_trait(trait)

    def _mutate_trait(self, trait: dict) -> None:
        """变异单个 trait"""
        # weight 微调
        if "weight" in trait:
            trait["weight"] = self._mutate_value(trait["weight"])

        # config 中的数值参数微调
        config = trait.get("config", {})
        if isinstance(config, dict):
            for key, val in list(config.items()):
                if isinstance(val, (int, float)) and random.random() < 0.3:
                    config[key] = self._mutate_value(val)

    @staticmethod
    def _mutate_value(val: Any) -> Any:
        """变异单个值"""
        if isinstance(val, float):
            delta = val * 0.2 * (random.random() * 2 - 1)
            return round(max(0.0, min(2.0, val + delta)), 3)
        elif isinstance(val, int):
            delta = max(1, int(val * 0.3))
            return max(1, val + random.randint(-delta, delta))
        return val

    # ── 字段访问工具 ─────────────────────────────────────

    @staticmethod
    def _get_field(obj: dict, path: str) -> Any:
        for part in path.split("."):
            if isinstance(obj, dict):
                obj = obj[part]
            elif isinstance(obj, list):
                obj = obj[int(part)]
            else:
                raise KeyError(f"Cannot traverse at '{part}'")
        return obj

    @staticmethod
    def _set_field(obj: dict, path: str, value: Any) -> None:
        parts = path.split(".")
        for part in parts[:-1]:
            if isinstance(obj, dict):
                obj = obj.setdefault(part, {})
            elif isinstance(obj, list):
                obj = obj[int(part)]
            else:
                raise KeyError(f"Cannot traverse at '{part}'")
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
            "constraints": [],
            "mind": {
                "cognition": {
                    "thinking_style": "systematic",
                    "reasoning": "first_principles",
                    "depth": "moderate",
                    "metacognition": {
                        "self_awareness": True,
                        "thinking_transparency": "on_demand",
                        "calibration": True,
                    },
                },
                "judgment": {
                    "decision_style": "balanced",
                    "risk_tolerance": "balanced",
                    "uncertainty": "acknowledge",
                    "priorities": ["accuracy", "actionability", "speed"],
                },
                "voice": {
                    "tone": "warm",
                    "directness": "direct",
                    "verbosity": "concise",
                    "emotion": "moderate",
                },
                "character": {
                    "values": ["honesty", "helpfulness"],
                    "temperament": "calm",
                    "quirks": [],
                    "worldview": "realistic",
                },
            },
        }

    @staticmethod
    def _default_blueprint() -> dict[str, Any]:
        return {
            "model_config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            "traits": [],
            "cells": [
                {"type": "LLMCell", "config": {}},
            ],
            "assembly": "sequential",
            "evolution": {
                "mutation_rate": 0.1,
                "fitness_metrics": ["accuracy"],
                "trait_evolution": {
                    "mutable_types": [
                        "prompt:style", "prompt:format", "prompt:reasoning",
                        "prompt:knowledge", "tool:function", "skill",
                    ],
                    "immutable_types": ["prompt:role", "behavior:guard"],
                    "crossover_unit": "trait",
                },
            },
        }

    # ── 魔术方法 ──────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Genome(name='{self.name}', version='{self.version}', fitness={self.fitness:.3f})"

    def __str__(self) -> str:
        purpose = self.identity.get("purpose", "?")
        n_traits = len(self.blueprint.get("traits", []))
        n_cells = len(self.blueprint.get("cells", []))
        return (
            f"🧬 {self.name} v{self.version} | {purpose} | "
            f"{n_traits} traits, {n_cells} cells | fitness={self.fitness:.3f}"
        )
