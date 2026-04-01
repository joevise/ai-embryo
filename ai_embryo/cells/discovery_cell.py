"""
DiscoveryCell — 工具发现细胞

职责：从外部市场发现可用工具，支持 ClawHub 和 MCP Registry 两种发现源。
在没有网络时优雅降级，返回空结果而非报错。
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

from ..cell import Cell
from ..registry import CellRegistry

logger = logging.getLogger("ai_embryo.cells.discovery")


@CellRegistry.register()
class DiscoveryCell(Cell):
    """工具发现细胞

    配置项：
        source: 发现源类型 "clawhub" | "mcp" | "all"（默认 "all"）
        search_strategy: 搜索策略 "task_match" | "keyword" | "semantic"（默认 "task_match"）
        max_tools: 最大返回工具数量（默认 10）
        preference_domains: 偏好领域列表，如 ["search", "data", "analysis"]

    process() 输入：
        task: 用户要做的事（字符串）
        discovery_config: 可选的发现配置覆盖

    process() 输出：
        available_tools: 所有发现的工具列表
        recommended_tools: 推荐工具列表（排序后）
        response: 描述性响应字符串
    """

    DEFAULT_CLAWHUB_BASE = "https://clawhub.example.com/api"
    DEFAULT_MCP_REGISTRY = "https://model-context-protocol.dev/servers"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.source = self.config.get("source", "all")
        self.search_strategy = self.config.get("search_strategy", "task_match")
        self.max_tools = self.config.get("max_tools", 10)
        self.preference_domains = self.config.get("preference_domains", [])

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        """发现可用工具

        Args:
            input: 包含 task 和可选的 discovery_config
                   {
                       "task": "用户要做的事",
                       "discovery_config": {...}  # 可选配置覆盖
                   }

        Returns:
            {
                "available_tools": [...],
                "recommended_tools": [...],
                "response": "发现了N个相关工具"
            }
        """
        task = input.get("task", "")
        override_config = input.get("discovery_config", {})

        source = override_config.get("source", self.source)
        max_tools = override_config.get("max_tools", self.max_tools)
        preference_domains = override_config.get(
            "preference_domains", self.preference_domains
        )

        available_tools = []

        if source in ("clawhub", "all"):
            clawhub_tools = self._discover_from_clawhub(task, preference_domains)
            available_tools.extend(clawhub_tools)

        if source in ("mcp", "all"):
            mcp_tools = self._discover_from_mcp_registry(task, preference_domains)
            available_tools.extend(mcp_tools)

        # 去重（按 name）
        seen = set()
        unique_tools = []
        for tool in available_tools:
            name = tool.get("name", "")
            if name and name not in seen:
                seen.add(name)
                unique_tools.append(tool)

        # 限制数量
        unique_tools = unique_tools[:max_tools]

        # 推荐工具 = 全部（后续可按 relevance score 排序）
        recommended_tools = list(unique_tools)

        n = len(unique_tools)
        response = f"发现了{n}个相关工具" if n > 0 else "未发现相关工具"

        return {
            "available_tools": unique_tools,
            "recommended_tools": recommended_tools,
            "response": response,
            "source": source,
            "task": task,
        }

    def _discover_from_clawhub(
        self, task: str, preference_domains: list[str]
    ) -> list[dict[str, Any]]:
        """从 ClawHub 技能市场发现工具

        执行 clawhub search <query> 命令获取技能列表。
        优雅降级：命令失败或无输出时返回空列表。
        """
        try:
            cmd = ["clawhub", "search", task]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.warning(f"ClawHub search failed: {result.stderr}")
                return []

            tools = self._parse_clawhub_output(result.stdout, preference_domains)
            return tools

        except FileNotFoundError:
            logger.warning("clawhub command not found, skipping ClawHub discovery")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("ClawHub search timed out")
            return []
        except Exception as e:
            logger.warning(f"ClawHub discovery error: {e}")
            return []

    def _parse_clawhub_output(
        self, output: str, preference_domains: list[str]
    ) -> list[dict[str, Any]]:
        """解析 clawhub search 的输出

        期望格式（JSON Lines 或简单文本）：
        {"name": "tool_name", "description": "...", "domain": "..."}
        或
        tool_name - description
        """
        import json

        tools = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试 JSON 解析
            if line.startswith("{"):
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and "name" in obj:
                        tool = {
                            "name": obj.get("name", ""),
                            "description": obj.get("description", ""),
                            "domain": obj.get("domain", ""),
                            "source": "clawhub",
                        }
                        if self._matches_domains(tool, preference_domains):
                            tools.append(tool)
                except json.JSONDecodeError:
                    pass
            else:
                # 尝试简单格式：name - description
                parts = line.split(" - ", 1)
                if len(parts) >= 1:
                    name = parts[0].strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                    tool = {
                        "name": name,
                        "description": desc,
                        "domain": "",
                        "source": "clawhub",
                    }
                    if self._matches_domains(tool, preference_domains):
                        tools.append(tool)

        return tools

    def _discover_from_mcp_registry(
        self, task: str, preference_domains: list[str]
    ) -> list[dict[str, Any]]:
        """从 MCP Registry 发现 MCP 服务器

        通过 HTTP 请求获取 MCP 服务列表。
        优雅降级：网络错误时返回空列表。
        """
        try:
            import urllib.request
            import urllib.error

            url = self.config.get("mcp_registry_url", self.DEFAULT_MCP_REGISTRY)
            req = urllib.request.Request(url, headers={"Accept": "application/json"})

            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode("utf-8")

            servers = self._parse_mcp_registry_response(data, task, preference_domains)
            return servers

        except urllib.error.URLError as e:
            logger.warning(f"MCP Registry network error: {e}")
            return []
        except Exception as e:
            logger.warning(f"MCP Registry discovery error: {e}")
            return []

    def _parse_mcp_registry_response(
        self, data: str, task: str, preference_domains: list[str]
    ) -> list[dict[str, Any]]:
        """解析 MCP Registry HTTP 响应

        期望格式：
        {"servers": [{"name": "...", "description": "...", "command": "..."}]}
        """
        import json

        try:
            obj = json.loads(data)
            servers = obj.get("servers", []) if isinstance(obj, dict) else obj
            if not isinstance(servers, list):
                servers = []
        except json.JSONDecodeError:
            servers = []

        tools = []
        task_lower = task.lower()

        for server in servers:
            if not isinstance(server, dict):
                continue

            name = server.get("name", "")
            desc = server.get("description", "")

            # 简单的任务相关性过滤
            if task and name:
                name_lower = name.lower()
                if task_lower in name_lower or task_lower in desc.lower():
                    tool = {
                        "name": name,
                        "description": desc,
                        "command": server.get("command", ""),
                        "source": "mcp",
                    }
                    if self._matches_domains(tool, preference_domains):
                        tools.append(tool)
            else:
                tool = {
                    "name": name,
                    "description": desc,
                    "command": server.get("command", ""),
                    "source": "mcp",
                }
                if self._matches_domains(tool, preference_domains):
                    tools.append(tool)

        return tools

    def _matches_domains(self, tool: dict[str, Any], domains: list[str]) -> bool:
        """检查工具是否匹配偏好领域"""
        if not domains:
            return True

        tool_domain = tool.get("domain", "").lower()
        tool_name = tool.get("name", "").lower()
        tool_desc = tool.get("description", "").lower()

        for domain in domains:
            domain_lower = domain.lower()
            if (
                domain_lower in tool_domain
                or domain_lower in tool_name
                or domain_lower in tool_desc
            ):
                return True

        return False
