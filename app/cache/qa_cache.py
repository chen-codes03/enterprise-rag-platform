"""问答结果缓存。

缓存 RAG 问答结果（answer + sources），key 由 query + 知识库标识哈希得到。
支持 TTL 失效与知识库更新主动失效，降低大模型调用成本、提升响应速度（G4）。
"""
from __future__ import annotations

import hashlib
import json

import redis

from app.config import get_settings

_DEFAULT_KB = "default"


class QACache:
    """问答结果缓存。"""

    def __init__(
        self,
        client: redis.Redis,
        ttl: int | None = None,
        prefix: str = "qa",
    ) -> None:
        self.client = client
        self.ttl = ttl or get_settings().qa_cache_ttl
        self.prefix = prefix

    def _key(self, query: str, kb: str | None = None) -> str:
        kb = kb or _DEFAULT_KB
        h = hashlib.sha256(f"{kb}:{query}".encode("utf-8")).hexdigest()
        return f"{self.prefix}:{kb}:{h}"

    def get(self, query: str, kb: str | None = None) -> dict | None:
        val = self.client.get(self._key(query, kb))
        if val is None:
            return None
        return json.loads(val)

    def set(
        self,
        query: str,
        answer: dict,
        kb: str | None = None,
        ttl: int | None = None,
    ) -> None:
        self.client.setex(
            self._key(query, kb),
            ttl or self.ttl,
            json.dumps(answer, ensure_ascii=False),
        )

    def invalidate_kb(self, kb: str | None = None) -> int:
        """失效指定知识库的所有问答缓存，返回删除条数。"""
        kb = kb or _DEFAULT_KB
        return self._delete_by_pattern(f"{self.prefix}:{kb}:*")

    def invalidate_all(self) -> int:
        """失效全部问答缓存。"""
        return self._delete_by_pattern(f"{self.prefix}:*")

    def _delete_by_pattern(self, pattern: str) -> int:
        deleted = 0
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)
            deleted += 1
        return deleted
