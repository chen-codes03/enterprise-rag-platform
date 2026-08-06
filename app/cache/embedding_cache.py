"""Embedding 向量缓存。

缓存文本到向量的计算结果，避免重复调用 Embedding API，降低成本（G4）。
通过 CachedEmbeddings 装饰 LangChain Embeddings 接口，对上层透明。
"""
from __future__ import annotations

import hashlib
import json

import redis
from langchain_core.embeddings import Embeddings

from app.config import get_settings


class EmbeddingCache:
    """Embedding 向量缓存。"""

    def __init__(
        self,
        client: redis.Redis,
        ttl: int | None = None,
        prefix: str = "emb",
    ) -> None:
        self.client = client
        self.ttl = ttl or get_settings().embedding_cache_ttl
        self.prefix = prefix

    def _key(self, text: str) -> str:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self.prefix}:{h}"

    def get(self, text: str) -> list[float] | None:
        val = self.client.get(self._key(text))
        if val is None:
            return None
        return json.loads(val)

    def set(self, text: str, vector: list[float], ttl: int | None = None) -> None:
        self.client.setex(self._key(text), ttl or self.ttl, json.dumps(vector))

    def invalidate_all(self) -> int:
        deleted = 0
        for key in self.client.scan_iter(f"{self.prefix}:*"):
            self.client.delete(key)
            deleted += 1
        return deleted


class CachedEmbeddings(Embeddings):
    """装饰 Embeddings：命中缓存则直接返回，否则回源并回填缓存。"""

    def __init__(self, base: Embeddings, cache: EmbeddingCache) -> None:
        self.base = base
        self.cache = cache

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        to_compute: list[str] = []
        indices: list[int] = []
        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                results[i] = cached
            else:
                to_compute.append(text)
                indices.append(i)
        if to_compute:
            computed = self.base.embed_documents(to_compute)
            for idx, text, vec in zip(indices, to_compute, computed):
                results[idx] = vec
                self.cache.set(text, vec)
        return results  # type: ignore[return-value]

    def embed_query(self, text: str) -> list[float]:
        cached = self.cache.get(text)
        if cached is not None:
            return cached
        vec = self.base.embed_query(text)
        self.cache.set(text, vec)
        return vec
