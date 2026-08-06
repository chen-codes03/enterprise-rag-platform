"""Chroma 向量库封装。

提供统一的 get_vectorstore 入口，基于 langchain-chroma，
支持持久化存储与相似度检索。Embedding 与持久化目录均可注入，便于测试。
"""
from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.config import Settings, get_settings
from app.rag.embeddings import get_embeddings


def get_vectorstore(
    embeddings: Embeddings | None = None,
    persist_dir: str | None = None,
    collection: str | None = None,
    settings: Settings | None = None,
) -> Chroma:
    """构造 Chroma 向量库。未指定参数时取 Settings 默认值。"""
    settings = settings or get_settings()
    embeddings = embeddings or get_embeddings(settings)
    return Chroma(
        collection_name=collection or settings.chroma_collection,
        embedding_function=embeddings,
        persist_directory=persist_dir or settings.chroma_persist_dir,
    )


def add_documents(store: Chroma, documents) -> list[str]:
    """向向量库添加文档并返回 id 列表。"""
    return store.add_documents(documents)


def similarity_search(store: Chroma, query: str, k: int | None = None):
    """语义检索 top-k。"""
    settings = get_settings()
    return store.similarity_search(query, k=k or settings.retrieve_top_k)
