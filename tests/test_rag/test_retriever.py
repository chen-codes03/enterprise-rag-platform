"""T3.1 RED: 语义检索器测试。"""
from app.rag.retriever import retrieve, retrieve_with_scores


def test_retrieve_returns_at_most_k(kb_store):
    results = retrieve(kb_store, "报销", k=2)
    assert len(results) <= 2


def test_retrieve_default_topk_from_settings(kb_store, monkeypatch):
    monkeypatch.setenv("RETRIEVE_TOP_K", "3")
    # kb_store 已缓存旧 settings，清除后使新 env 生效
    from app.config import get_settings

    get_settings.cache_clear()
    results = retrieve(kb_store, "入职")
    assert len(results) <= 3


def test_retrieve_with_scores_ordered(kb_store):
    """Chroma 返回结果应按距离升序（相似度从高到低）。"""
    results = retrieve_with_scores(kb_store, "请假", k=3)
    assert len(results) >= 1
    scores = [s for _, s in results]
    assert scores == sorted(scores)


def test_retrieve_returns_documents(kb_store):
    from langchain_core.documents import Document

    results = retrieve(kb_store, "部署", k=2)
    assert all(isinstance(r, Document) for r in results)
