"""
LLMCell — 语言模型调用细胞

职责：调用 LLM，返回响应。支持 OpenAI 兼容接口。
自动从 Genome 的 identity.mind + prompt traits 编译系统提示词。
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from ..cell import Cell
from ..registry import CellRegistry
from ..exceptions import CellError

logger = logging.getLogger("ai_embryo.cells.llm")

try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@CellRegistry.register()
class LLMCell(Cell):
    """LLM 调用细胞

    配置项（优先从 config 取，其次从 _genome 注入）：
        model: 模型名称
        temperature: 温度
        max_tokens: 最大输出 token
        api_key: API Key
        base_url: API 基础 URL
        system_prompt: 系统提示词（如果不提供，自动从 genome 编译）
        tools: Function Calling 工具定义列表（如果不提供，自动从 genome traits 编译）
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)

        # 从 _genome 注入的信息（Embryo 发育时注入）
        genome_data = self.config.get("_genome")

        # model_config
        mc = self.config.get("_model_config", {})
        self.model = self.config.get("model") or mc.get("model", "gpt-4")
        self.temperature = self.config.get("temperature") or mc.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens") or mc.get("max_tokens", 2000)

        # API Key 配置（支持多种环境变量）
        minimax_key = os.environ.get("MINIMAX_API_KEY", "")
        self.api_key = (
            self.config.get("api_key")
            or minimax_key
            or os.environ.get("OPENAI_API_KEY", "")
        )

        # Base URL 配置：优先使用 config 中的值，否则检查 MINIMAX_API_KEY 自动设置
        self.base_url = (
            self.config.get("base_url")
            or mc.get("base_url")
            or os.environ.get("OPENAI_BASE_URL")
            or ""
        )
        # 当检测到 MINIMAX_API_KEY 时自动设置 base_url
        if minimax_key and not self.base_url:
            self.base_url = "https://api.minimax.chat/v1"

        # 系统提示词：优先用显式配置，否则从 genome 自动编译
        if "system_prompt" in self.config:
            self.system_prompt = self.config["system_prompt"]
        elif genome_data:
            # 在 Embryo 发育时，genome 会被注入到 config["_genome"]
            from ..genome import Genome

            g = Genome()
            g.identity = genome_data.get("identity", {})
            g.blueprint = genome_data.get("blueprint", {})
            self.system_prompt = g.compile_system_prompt()
            # 自动编译工具
            self._compiled_tools = g.compile_tools()
        else:
            # 从 _identity 构建基础提示词（向后兼容）
            identity = self.config.get("_identity", {})
            self.system_prompt = self._build_basic_prompt(identity)
            self._compiled_tools = []

        self.tools = self.config.get("tools") or getattr(self, "_compiled_tools", [])
        self._client = None

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        """调用 LLM"""
        client = self._get_client()

        # 构建消息
        if "messages" in input:
            messages = input["messages"]
        else:
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})

            if "previous_response" in input:
                messages.append(
                    {"role": "assistant", "content": input["previous_response"]}
                )

            user_input = input.get("input", "")
            if user_input:
                messages.append({"role": "user", "content": user_input})

        if not messages:
            return {"response": "", "error": "没有输入内容"}

        # 构建请求参数
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        # Function Calling
        tools = input.get("tools") or self.tools
        if (
            tools
            and isinstance(tools, list)
            and len(tools) > 0
            and isinstance(tools[0], dict)
        ):
            kwargs["tools"] = tools

        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            result: dict[str, Any] = {
                "response": message.content or "",
                "finish_reason": choice.finish_reason,
            }

            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                    for tc in message.tool_calls
                ]

            if response.usage:
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return result

        except Exception as e:
            raise CellError(f"LLM 调用失败: {e}") from e

    def _get_client(self) -> Any:
        """获取或创建 OpenAI 客户端"""
        if self._client is None:
            if not HAS_OPENAI:
                raise CellError("需要安装 openai 包: pip install openai")

            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = OpenAI(**kwargs)
        return self._client

    @staticmethod
    def _build_basic_prompt(identity: dict[str, Any]) -> str:
        """从身份基因构建基础系统提示词（向后兼容，无 mind 时使用）"""
        if not identity:
            return ""
        parts = []
        purpose = identity.get("purpose", "")
        if purpose:
            parts.append(f"你的核心目标: {purpose}")
        constraints = identity.get("constraints", [])
        if constraints:
            parts.append("约束条件:\n" + "\n".join(f"  - {c}" for c in constraints))
        return "\n".join(parts) if parts else ""
