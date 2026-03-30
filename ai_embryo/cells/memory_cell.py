"""
MemoryCell — 记忆存取细胞

职责：存储和检索记忆。支持 ChromaDB 向量存储和简单字典存储。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from ..cell import Cell
from ..registry import CellRegistry
from ..exceptions import CellError

logger = logging.getLogger("ai_embryo.cells.memory")

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


@CellRegistry.register()
class MemoryCell(Cell):
    """记忆细胞
    
    配置项：
        backend: 存储后端 ("chromadb" | "dict") 默认 "dict"
        collection: ChromaDB 集合名称
        persist_directory: ChromaDB 持久化目录
        max_results: 检索返回的最大数量 (默认 5)
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        
        self.backend = self.config.get("backend", "dict")
        self.max_results = self.config.get("max_results", 5)
        
        # 初始化存储
        if self.backend == "chromadb":
            if not HAS_CHROMADB:
                logger.warning("chromadb 未安装，回退到 dict 模式")
                self.backend = "dict"
            else:
                persist_dir = self.config.get("persist_directory", "./memory_db")
                self._chroma_client = chromadb.PersistentClient(path=persist_dir)
                collection_name = self.config.get("collection", "ai_embryo_memory")
                self._collection = self._chroma_client.get_or_create_collection(
                    name=collection_name
                )
        
        if self.backend == "dict":
            self._store: list[dict[str, Any]] = []

    def process(self, input: dict[str, Any]) -> dict[str, Any]:
        """处理记忆操作
        
        Args:
            input: 包含以下键之一：
                - action: "store" | "retrieve" | "search" (默认 "search")
                - content: 要存储的内容 (store 时必须)
                - query: 搜索查询 (retrieve/search 时)
                - input: 如果没有 query，用 input 作为查询
                - metadata: 存储时的附加元数据
                
        Returns:
            - memories: 检索到的记忆列表
            - stored: 是否成功存储
            - response: 摘要文本
        """
        action = input.get("action", "search")
        
        if action == "store":
            return self._store_memory(input)
        else:
            return self._search_memory(input)

    def _store_memory(self, input: dict[str, Any]) -> dict[str, Any]:
        """存储记忆"""
        content = input.get("content", input.get("input", ""))
        if not content:
            return {"stored": False, "response": "没有要存储的内容"}

        metadata = input.get("metadata", {})
        metadata["timestamp"] = time.time()

        if self.backend == "chromadb":
            doc_id = f"mem_{int(time.time() * 1000)}"
            self._collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id],
            )
        else:
            self._store.append({
                "content": content,
                "metadata": metadata,
            })

        return {
            "stored": True,
            "response": f"已存储记忆: {content[:50]}...",
        }

    def _search_memory(self, input: dict[str, Any]) -> dict[str, Any]:
        """搜索记忆"""
        query = input.get("query", input.get("input", ""))
        if not query:
            return {"memories": [], "response": "没有搜索查询"}

        if self.backend == "chromadb":
            results = self._collection.query(
                query_texts=[query],
                n_results=self.max_results,
            )
            
            memories = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    mem = {"content": doc}
                    if results["metadatas"] and results["metadatas"][0]:
                        mem["metadata"] = results["metadatas"][0][i]
                    if results["distances"] and results["distances"][0]:
                        mem["distance"] = results["distances"][0][i]
                    memories.append(mem)
        else:
            # 简单的关键词匹配
            memories = []
            query_lower = query.lower()
            for item in self._store:
                if query_lower in item["content"].lower():
                    memories.append(item)
            memories = memories[:self.max_results]

        # 构建摘要
        if memories:
            summary = f"找到 {len(memories)} 条相关记忆"
        else:
            summary = "没有找到相关记忆"

        return {
            "memories": memories,
            "response": summary,
        }
