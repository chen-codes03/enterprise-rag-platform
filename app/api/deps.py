"""API 依赖：鉴权与 RAG 组件注入。

store / model provider / qa_cache 通过 lru_cache 单例化，避免每次请求
重复初始化（尤其 Chroma 客户端的持久化重载开销）。RAGChain 仍按请求
构建（轻量组装 + 每请求独立 kb，保证并发安全）。
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Header, HTTPException

from app.config import get_settings


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> str:
    """API Key 鉴权。缺失或无效返回 401。"""
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


@lru_cache
def _get_store_cached():
    """单例向量库（生产用，测试中通过 dependency_overrides 覆盖 get_store）。

    生产链路接入 Embedding 缓存（CachedEmbeddings），并按 model_id 隔离
    不同 embedding 模型的缓存，避免切换模型后命中错误维度的旧向量。
    """
    from app.cache.embedding_cache import CachedEmbeddings, EmbeddingCache
    from app.cache.redis_client import get_redis_client
    from app.rag.embeddings import get_embeddings
    from app.rag.vectorstore import get_vectorstore

    settings = get_settings()
    base_embeddings = get_embeddings(settings)
    model_id = f"{settings.embedding_model}:{settings.embedding_dimension}"
    cached_embeddings = CachedEmbeddings(
        base_embeddings, EmbeddingCache(get_redis_client(), model_id=model_id)
    )
    return get_vectorstore(embeddings=cached_embeddings, settings=settings)


def get_store():
    """向量库依赖（单例，测试中覆盖）。"""
    return _get_store_cached()


@lru_cache
def _get_provider_cached():
    """单例模型 provider。"""
    from app.models.factory import get_model_provider

    return get_model_provider(get_settings())


@lru_cache
def _get_qa_cache_cached():
    """单例 QA 缓存。"""
    from app.cache.qa_cache import QACache
    from app.cache.redis_client import get_redis_client

    return QACache(get_redis_client())


def get_qa_cache():
    """问答缓存依赖（单例，测试中覆盖）。"""
    return _get_qa_cache_cached()


def get_redis_dep():
    """Redis 客户端依赖（健康检查等场景用，测试中覆盖）。"""
    from app.cache.redis_client import get_redis_client

    return get_redis_client()


def clear_component_cache() -> None:
    """清理组件单例缓存（测试间隔离用）。"""
    _get_store_cached.cache_clear()
    _get_provider_cached.cache_clear()
    _get_qa_cache_cached.cache_clear()


def get_rag_chain():
    """RAG 链路依赖（生产用，测试中覆盖）。

    复用单例 store / provider / qa_cache，每请求构建独立的 RAGChain
    （kb 按请求设置，避免共享可变状态引发的并发问题）。
    """
    from app.rag.chain import RAGChain

    settings = get_settings()
    return RAGChain(
        store=get_store(),
        model_provider=_get_provider_cached(),
        qa_cache=get_qa_cache(),
        kb=settings.chroma_collection,
    )
