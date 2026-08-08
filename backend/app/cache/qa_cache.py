"""问答结果缓存。"""
from __future__ import annotations

import hashlib
import json
import time

import redis

from app.config import get_settings

_DEFAULT_KB = "default"


class QACache:
    """问答结果缓存。Redis 不可用时自动降级为内存缓存。"""

    def __init__(
        self,
        client: redis.Redis | None,
        ttl: int | None = None,
        prefix: str = "qa",
    ) -> None:
        self.client = client
        self.ttl = ttl or get_settings().qa_cache_ttl
        self.prefix = prefix
        # 内存缓存降级
        self._mem_cache: dict[str, tuple[str, float]] = {}

    def _key(self, query: str, kb: str | None = None) -> str:
        kb = kb or _DEFAULT_KB
        h = hashlib.sha256(f"{kb}:{query}".encode("utf-8")).hexdigest()
        return f"{self.prefix}:{kb}:{h}"

    def get(self, query: str, kb: str | None = None) -> dict | None:
        key = self._key(query, kb)
        if self.client is None:
            # 内存降级
            val = self._mem_cache.get(key)
            if val and time.time() < val[1]:
                return json.loads(val[0])
            self._mem_cache.pop(key, None)
            return None
        val = self.client.get(key)
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
        key = self._key(query, kb)
        val = json.dumps(answer, ensure_ascii=False)
        ttl_val = ttl or self.ttl
        if self.client is None:
            # 内存降级
            self._mem_cache[key] = (val, time.time() + ttl_val)
            return
        self.client.setex(key, ttl_val, val)

    def invalidate_kb(self, kb: str | None = None) -> int:
        kb = kb or _DEFAULT_KB
        if self.client is None:
            return self._delete_mem_by_pattern(f"{self.prefix}:{kb}:*")
        return self._delete_by_pattern(f"{self.prefix}:{kb}:*")

    def invalidate_all(self) -> int:
        if self.client is None:
            return self._delete_mem_by_pattern(f"{self.prefix}:*")
        return self._delete_by_pattern(f"{self.prefix}:*")

    def _delete_by_pattern(self, pattern: str) -> int:
        deleted = 0
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)
            deleted += 1
        return deleted

    def _delete_mem_by_pattern(self, pattern: str) -> int:
        import fnmatch
        deleted = 0
        for key in list(self._mem_cache.keys()):
            if fnmatch.fnmatch(key, pattern):
                self._mem_cache.pop(key, None)
                deleted += 1
        return deleted
