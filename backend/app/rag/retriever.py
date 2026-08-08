"""语义检索器。

封装 Chroma 相似度检索，支持 top-k 与带分数检索（用于排序与调优）。
"""
from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import get_settings


def retrieve(store: Chroma, query: str, k: int | None = None) -> list[Document]:
    """检索 top-k 相关文档。"""
    k = k or get_settings().retrieve_top_k
    return store.similarity_search(query, k=k)


def retrieve_with_scores(
    store: Chroma, query: str, k: int | None = None
) -> list[tuple[Document, float]]:
    """检索 top-k 并返回 (文档, 距离分数)，按相似度从高到低排序。"""
    k = k or get_settings().retrieve_top_k
    return store.similarity_search_with_score(query, k=k)
