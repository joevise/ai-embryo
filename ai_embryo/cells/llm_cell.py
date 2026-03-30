"""
LLMCell — 语言模型调用细胞

职责：调用 LLM，返回响应。支持 OpenAI 兼容接口。
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
    
    配置项：
        model: 模型名称 (默认 "gpt-4")
        temperature: 温度 (默认 0.7)
        max_tokens: 最大输出 token (默认 2000)
        api_key: API Key (默认从环境变量)
        base_url: API 基础 URL
        system_prompt: 系统提示词
        tools: Function Calling 工具定义列表
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)

        # 从配置或能力基因中获取参数
        caps = self.config.get("_capabilities", {})
        
        self.model = self.config.get("model") or caps.get("model", "gpt-4")
        self.temperature = self.config.get("temperature") or caps.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens") or caps.get("max_tokens", 2000)
        
        self.api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = self.config.get("base_url") or os.environ.get("OPENAI_BASE_URL")
        
        # 从身份基因获取默认系统提示词
        identity = self.config.get("_identity", {})
        default_prompt = self._build_system_prompt(identity)
        self.system_prompt = self.config.get("system_prompt", default_prompt)
        
        self.tools = self.config.get("tools") or caps.get("tools", [])

        # 初始化客户端
        self._client = None

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        """调用 LLM
        
        Args:
            input: 包含以下可选键：
                - input: 用户输入文本
                - messages: 完整消息历史 (优先)
                - tools: 本次调用的工具定义
                
        Returns:
            - response: LLM 的文本回复
            - tool_calls: 工具调用请求列表 (如果有)
            - usage: token 用量信息
        """
        client = self._get_client()
        
        # 构建消息
        if "messages" in input:
            messages = input["messages"]
        else:
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            
            # 加入之前的上下文
            if "previous_response" in input:
                messages.append({"role": "assistant", "content": input["previous_response"]})
            
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
        if tools and isinstance(tools, list) and isinstance(tools[0], dict):
            kwargs["tools"] = tools

        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            result: dict[str, Any] = {
                "response": message.content or "",
                "finish_reason": choice.finish_reason,
            }

            # 工具调用
            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                    for tc in message.tool_calls
                ]

            # 用量
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
                raise CellError(
                    "需要安装 openai 包: pip install openai"
                )
            
            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url
                
            self._client = OpenAI(**kwargs)
        
        return self._client

    @staticmethod
    def _build_system_prompt(identity: dict[str, Any]) -> str:
        """从身份基因构建默认系统提示词"""
        if not identity:
            return ""

        parts = []
        
        purpose = identity.get("purpose", "")
        if purpose:
            parts.append(f"你的核心目标: {purpose}")

        personality = identity.get("personality", [])
        if personality:
            parts.append(f"你的性格特征: {'、'.join(personality)}")

        constraints = identity.get("constraints", [])
        if constraints:
            parts.append("约束条件:")
            for c in constraints:
                parts.append(f"  - {c}")

        return "\n".join(parts) if parts else ""
