"""API 依赖：鉴权与 RAG 组件注入。"""
from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import get_settings


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    """API Key 鉴权。缺失或无效返回 401。"""
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


def get_store():
    """向量库依赖（生产用，测试中覆盖）。"""
    from app.rag.vectorstore import get_vectorstore

    return get_vectorstore()


def get_rag_chain():
    """RAG 链路依赖（生产用，测试中覆盖）。

    生产环境从 Settings 构建向量库、模型 provider、QA 缓存并组装 RAGChain。
    """
    from app.cache.qa_cache import QACache
    from app.cache.redis_client import get_redis_client
    from app.models.factory import get_model_provider
    from app.rag.chain import RAGChain
    from app.rag.vectorstore import get_vectorstore

    settings = get_settings()
    store = get_vectorstore(settings=settings)
    provider = get_model_provider(settings)
    qa_cache = QACache(get_redis_client())
    return RAGChain(
        store=store,
        model_provider=provider,
        qa_cache=qa_cache,
        kb=settings.chroma_collection,
    )
