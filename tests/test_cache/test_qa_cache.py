"""T4.3 RED: 问答结果缓存测试。"""
from app.cache.qa_cache import QACache


def test_qa_cache_miss_then_hit(redis_client):
    cache = QACache(redis_client, ttl=60)
    assert cache.get("如何报销") is None
    cache.set("如何报销", {"answer": "在OA系统提交", "sources": []})
    result = cache.get("如何报销")
    assert result is not None
    assert result["answer"] == "在OA系统提交"


def test_qa_cache_different_query_separate(redis_client):
    cache = QACache(redis_client)
    cache.set("Q1", {"answer": "A1", "sources": []})
    assert cache.get("Q2") is None
    assert cache.get("Q1") is not None


def test_qa_cache_kb_isolation(redis_client):
    cache = QACache(redis_client)
    cache.set("Q", {"answer": "A1", "sources": []}, kb="kb1")
    cache.set("Q", {"answer": "A2", "sources": []}, kb="kb2")
    assert cache.get("Q", kb="kb1")["answer"] == "A1"
    assert cache.get("Q", kb="kb2")["answer"] == "A2"


def test_qa_cache_preserves_sources(redis_client):
    cache = QACache(redis_client)
    sources = [{"index": 1, "source": "a.md", "content": "片段"}]
    cache.set("Q", {"answer": "A", "sources": sources})
    result = cache.get("Q")
    assert result["sources"] == sources
