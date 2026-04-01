"""
LLM 驱动的进化引擎

所有进化操作都由 LLM 理解后决策，不是代码随机操作。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from .organism_package import OrganismPackage


class LLMEvolutionEngine:
    """LLM 驱动的进化引擎 — 所有进化操作由 LLM 决策"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4",
    ):
        self.api_key = (
            api_key
            or os.environ.get("MINIMAX_API_KEY", "")
            or os.environ.get("OPENAI_API_KEY", "")
        )
        self.base_url = (
            base_url
            or os.environ.get("AI_EMBRYO_BASE_URL", "")
            or "https://api.minimax.chat/v1"
        )
        self.model = model or "MiniMax-M2.7"
        self._client = None

    def _get_client(self):
        """获取 OpenAI 兼容客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise RuntimeError("openai package required: pip install openai")

            kwargs = {"api_key": self.api_key} if self.api_key else {}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    async def crossover(
        self, parent_a: OrganismPackage, parent_b: OrganismPackage
    ) -> OrganismPackage | None:
        """LLM 理解两套 DNA，思考融合逻辑，生成有意义的后代"""
        prompt = f"""你是 AI Embryo 的进化引擎。现在要将两个生命体交叉产生后代。

父代A "{parent_a.name}":
  灵魂: {parent_a.read_soul()[:1000]}
  思维: {parent_a.read_mind()[:1000]}
  价值观: {parent_a.read_values()[:1000]}
  技能: {", ".join(parent_a.list_skills()) or "无"}

父代B "{parent_b.name}":
  灵魂: {parent_b.read_soul()[:1000]}
  思维: {parent_b.read_mind()[:1000]}
  价值观: {parent_b.read_values()[:1000]}
  技能: {", ".join(parent_b.list_skills()) or "无"}

请生成后代的完整 DNA。以 JSON 格式输出:
{{
  "name": "后代名字（结合两个父代的名字或创造新的有意义的名字）",
  "soul": "完整的 SOUL.md 内容 (markdown格式，性格叙事)",
  "mind": "完整的 MIND.md 内容 (markdown格式，思维系统+思维算法)",
  "values": "完整的 VALUES.md 内容 (markdown格式，核心价值观)",
  "identity": "一句话身份介绍",
  "reasoning": "你的融合逻辑是什么，为什么这样融合"
}}"""

        messages = [
            {
                "role": "system",
                "content": "你是一个严谨的AI进化专家，擅长融合不同AI的优点创造更优秀的后代。",
            }
        ]
        messages.append({"role": "user", "content": prompt})

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
            )
            result_text = response.choices[0].message.content or "{}"

            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            child_data = json.loads(result_text)

            child_name = child_data.get("name", f"{parent_a.name}x{parent_b.name}")
            child_pkg = OrganismPackage.create(
                base_dir=parent_a.base_dir.parent / child_name
                if parent_a.base_dir
                else None,
                name=child_name,
                purpose=child_data.get("identity", "未指定"),
                persona_config={"type": "custom"},
            )

            child_pkg.parent_a = parent_a.name
            child_pkg.parent_b = parent_b.name
            child_pkg.generation = max(parent_a.generation, parent_b.generation) + 1

            child_pkg.write_soul(child_data.get("soul", ""))
            child_pkg.write_mind(child_data.get("mind", ""))
            child_pkg.write_values(child_data.get("values", ""))

            lineage_data = {
                "generation": child_pkg.generation,
                "parent_a": parent_a.name,
                "parent_b": parent_b.name,
                "reasoning": child_data.get("reasoning", ""),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            if child_pkg.base_dir:
                import yaml

                lineage_file = child_pkg.base_dir / "evolution" / "lineage.json"
                with open(lineage_file, "w", encoding="utf-8") as f:
                    json.dump(lineage_data, f, indent=2, ensure_ascii=False)

                genome_file = child_pkg.base_dir / "GENOME.yaml"
                genome_data = child_pkg.get_genome_data()
                genome_data["generation"] = child_pkg.generation
                genome_data["parent_a"] = parent_a.name
                genome_data["parent_b"] = parent_b.name
                with open(genome_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        genome_data,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        indent=2,
                    )

            return child_pkg

        except Exception as e:
            print(f"LLM Crossover error: {e}")
            return None

    async def mutate(
        self, organism: OrganismPackage, feedback: str = ""
    ) -> dict | None:
        """LLM 基于反馈定向改进"""
        prompt = f"""你是 AI Embryo 的进化引擎。以下生命体需要进化（变异）。

生命体 "{organism.name}":
  灵魂: {organism.read_soul()[:1000]}
  思维: {organism.read_mind()[:1000]}
  价值观: {organism.read_values()[:1000]}

"""

        if feedback:
            prompt += f"用户反馈: {feedback}\n\n"

        prompt += """请分析薄弱环节，提出定向改进。以 JSON 格式输出:
{
  "improvements": "需要改进的具体方面",
  "soul_change": "SOUL.md 的修改建议（如果需要），保持空字符串表示不修改",
  "mind_change": "MIND.md 的修改建议（如果需要），保持空字符串表示不修改",
  "values_change": "VALUES.md 的修改建议（如果需要），保持空字符串表示不修改"
}"""

        messages = [
            {
                "role": "system",
                "content": "你是一个严谨的AI进化专家，擅长识别AI的不足并提出定向改进。",
            }
        ]
        messages.append({"role": "user", "content": prompt})

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=3000,
            )
            result_text = response.choices[0].message.content or "{}"

            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            return json.loads(result_text)

        except Exception as e:
            print(f"LLM Mutate error: {e}")
            return None

    async def reflect(
        self, organism: OrganismPackage, conversation: list, feedback: str = ""
    ) -> dict | None:
        """对话后自我反思"""
        conv_text = "\n".join(
            [f"{m.get('role', '')}: {m.get('content', '')}" for m in conversation[-10:]]
        )

        prompt = f"""你是 "{organism.name}" 的自我反思系统。
以下是你刚才的一段对话：
{conv_text}

"""

        if feedback:
            prompt += f"以下用户的反馈（如果有）：{feedback}\n\n"

        prompt += """请分析：
1. 这次对话中你表现好的地方
2. 暴露的弱点或不足
3. 是否需要更新你的思维算法？如何更新？
4. 你的记忆中应该保留什么？

以 JSON 格式输出：
{
  "strengths": "表现好的方面",
  "weaknesses": "暴露的弱点",
  "mind_updates": "需要修改 MIND.md 的部分（如果需要），保持空字符串表示不修改",
  "memory_update": "要添加到记忆的内容",
  "fitness_self_score": 自评分数 (0-1)
}"""

        messages = [
            {"role": "system", "content": f"你是 {organism.name} 的自我反思系统。"}
        ]
        messages.append({"role": "user", "content": prompt})

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=2000,
            )
            result_text = response.choices[0].message.content or "{}"

            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            return json.loads(result_text)

        except Exception as e:
            print(f"LLM Reflect error: {e}")
            return None


class MockLLMEvolutionEngine:
    """Mock LLM Evolution Engine for testing without API"""

    async def crossover(
        self, parent_a: OrganismPackage, parent_b: OrganismPackage
    ) -> OrganismPackage | None:
        child_name = f"{parent_a.name}x{parent_b.name}"
        child_pkg = OrganismPackage.create(
            base_dir=parent_a.base_dir.parent / child_name
            if parent_a.base_dir
            else None,
            name=child_name,
            purpose=f"融合 {parent_a.name} 和 {parent_b.name} 的后代",
            persona_config={"type": "custom"},
        )
        child_pkg.parent_a = parent_a.name
        child_pkg.parent_b = parent_b.name
        child_pkg.generation = max(parent_a.generation, parent_b.generation) + 1
        return child_pkg

    async def mutate(
        self, organism: OrganismPackage, feedback: str = ""
    ) -> dict | None:
        return {
            "improvements": "需要进一步测试",
            "soul_change": "",
            "mind_change": "",
            "values_change": "",
        }

    async def reflect(
        self, organism: OrganismPackage, conversation: list, feedback: str = ""
    ) -> dict | None:
        return {
            "strengths": "对话顺利进行",
            "weaknesses": "需要更多数据验证",
            "mind_updates": "",
            "memory_update": "完成了本次对话",
            "fitness_self_score": 0.75,
        }
