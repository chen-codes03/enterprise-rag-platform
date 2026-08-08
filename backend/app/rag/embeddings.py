"""Embedding 向量化层。

封装 LangChain Embeddings 接口，支持三种 provider：
- doubao：火山引擎豆包多模态 Embedding（推荐，语义检索效果好）
- openai：标准 OpenAI 兼容 Embedding（DeepSeek / 通义千问等）
- fake：确定性假 Embedding（测试与离线场景）
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
import warnings

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.config import Settings, get_settings


class DoubaoEmbeddings(Embeddings):
    """火山引擎豆包多模态 Embedding 适配器。

    适配 doubao-embedding-vision-251215 的特殊 API 格式：
    - 请求：POST /embeddings/multimodal，input 为 [{type, text}] 数组
    - 响应：data.embedding（单条，非数组）
    """

    def __init__(self, api_key: str, model: str, base_url: str, dimension: int = 2048) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.dimension = dimension

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.base_url}/embeddings/multimodal"
        input_items = [{"type": "text", "text": t} for t in texts]
        payload = json.dumps({"model": self.model, "input": input_items}).encode()

        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        })
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result["data"]["embedding"]

    def embed_query(self, text: str) -> list[float]:
        vec = self._call_api([text])
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._call_api([t]) for t in texts]


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
    """根据配置返回 Embedding 实例。"""
    settings = settings or get_settings()
    provider = settings.embedding_provider

    # Doubao 豆包 Embedding
    if provider == "doubao":
        if not settings.embedding_api_key:
            warnings.warn(
                "EMBEDDING_PROVIDER=doubao 但未配置 EMBEDDING_API_KEY，"
                "自动降级到 fake 确定性哈希向量。",
                RuntimeWarning,
                stacklevel=2,
            )
            return DeterministicEmbeddings(dim=settings.embedding_dimension)
        return DoubaoEmbeddings(
            api_key=settings.embedding_api_key,
            model=settings.embedding_model,
            base_url=settings.embedding_base_url,
            dimension=settings.embedding_dimension,
        )

    # OpenAI 兼容 Embedding
    if provider == "openai":
        if not settings.embedding_api_key:
            warnings.warn(
                "EMBEDDING_PROVIDER=openai 但未配置 EMBEDDING_API_KEY，"
                "自动降级到 fake 确定性哈希向量。",
                RuntimeWarning,
                stacklevel=2,
            )
            return DeterministicEmbeddings(dim=settings.embedding_dimension)
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )

    if provider == "fake":
        return DeterministicEmbeddings(dim=settings.embedding_dimension)

    raise ValueError(f"未知的 embedding provider: {provider}，可选: fake | openai | doubao")
