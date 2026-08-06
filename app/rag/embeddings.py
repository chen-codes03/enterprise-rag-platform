"""Embedding 向量化层。

封装 LangChain Embeddings 接口，默认使用 OpenAI 兼容 Embedding；
提供 DeterministicEmbeddings 用于测试与离线场景（基于文本哈希，确定性）。
"""
from __future__ import annotations

import hashlib
import warnings

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.config import Settings, get_settings


class DeterministicEmbeddings(Embeddings):
    """确定性假 Embedding，基于 SHA-256 文本哈希生成定长向量。

    用于测试与离线场景：相同文本始终得到相同向量，不同文本大概率不同。
    """

    def __init__(self, dim: int = 8) -> None:
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [(h[i % len(h)] / 255.0) - 0.5 for i in range(self.dim)]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


def get_embeddings(settings: Settings | None = None) -> Embeddings:
    """根据配置返回 Embedding 实例。

    若配置了 openai 但未填写 API key，自动降级到 fake 演示模式。
    """
    settings = settings or get_settings()
    provider = settings.embedding_provider

    # Fallback：配置了 openai embedding 但缺 API key → 降级到 fake
    if provider == "openai" and not settings.embedding_api_key:
        warnings.warn(
            "EMBEDDING_PROVIDER=openai 但未配置 EMBEDDING_API_KEY，"
            "自动降级到 fake 确定性哈希向量。请在 .env 中设置 API key 以启用真实 Embedding。",
            RuntimeWarning,
            stacklevel=2,
        )
        return DeterministicEmbeddings(dim=settings.embedding_dimension)

    if provider == "fake":
        return DeterministicEmbeddings(dim=settings.embedding_dimension)
    if provider == "openai":
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )
    raise ValueError(f"未知的 embedding provider: {provider}，可选: fake | openai")
