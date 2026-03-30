"""
ConfigManager — 配置管理器

从 config.yaml 加载配置，支持环境变量覆盖和运行时修改。
"""

from __future__ import annotations

import os
import copy
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG = {
    "server": {"host": "0.0.0.0", "port": 8010},
    "llm": {
        "provider": "openai",
        "api_key": "",
        "base_url": "",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
    },
    "evolution": {
        "default_population_size": 8,
        "default_generations": 10,
        "selection_ratio": 0.5,
        "elitism": 1,
    },
}


class ConfigManager:
    """全局配置管理器（单例模式）"""

    _instance: ConfigManager | None = None
    _config: dict[str, Any] = {}
    _config_path: Path | None = None

    def __new__(cls) -> ConfigManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = copy.deepcopy(_DEFAULT_CONFIG)
        return cls._instance

    def load(self, path: str | Path | None = None) -> None:
        """从 YAML 文件加载配置"""
        if path is None:
            path = Path(__file__).parent.parent / "config.yaml"
        path = Path(path)
        self._config_path = path

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}
            self._deep_merge(self._config, file_config)

        # 环境变量覆盖
        env_key = os.environ.get("AI_EMBRYO_API_KEY", "")
        if env_key:
            self._config["llm"]["api_key"] = env_key

        env_model = os.environ.get("AI_EMBRYO_MODEL", "")
        if env_model:
            self._config["llm"]["model"] = env_model

        env_base = os.environ.get("AI_EMBRYO_BASE_URL", "")
        if env_base:
            self._config["llm"]["base_url"] = env_base

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分路径如 'llm.api_key'"""
        parts = key.split(".")
        obj = self._config
        for p in parts:
            if isinstance(obj, dict) and p in obj:
                obj = obj[p]
            else:
                return default
        return obj

    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点分路径"""
        parts = key.split(".")
        obj = self._config
        for p in parts[:-1]:
            obj = obj.setdefault(p, {})
        obj[parts[-1]] = value

    def get_all(self) -> dict[str, Any]:
        """返回完整配置（深拷贝）"""
        return copy.deepcopy(self._config)

    def save(self) -> None:
        """保存当前配置回 YAML 文件"""
        if self._config_path is None:
            return
        with open(self._config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True, indent=2)

    def has_api_key(self) -> bool:
        """检查是否配置了 API key"""
        return bool(self._config.get("llm", {}).get("api_key", ""))

    def get_masked_config(self) -> dict[str, Any]:
        """返回配置，API key 只显示最后4位"""
        cfg = copy.deepcopy(self._config)
        key = cfg.get("llm", {}).get("api_key", "")
        if key and len(key) > 4:
            cfg["llm"]["api_key"] = "***" + key[-4:]
        elif key:
            cfg["llm"]["api_key"] = "***"
        return cfg

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        """深度合并字典"""
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                ConfigManager._deep_merge(base[k], v)
            else:
                base[k] = v

    @classmethod
    def reset(cls) -> None:
        """重置单例（主要用于测试）"""
        cls._instance = None
