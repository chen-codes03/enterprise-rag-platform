"""T4.7 RED: 缓存失效策略测试。TTL + 知识库更新主动失效。"""
import time

from app.cache.qa_cache import QACache


def test_qa_cache_ttl_configured(redis_client):
    cache = QACache(redis_client, ttl=120)
    cache.set("Q", {"answer": "A", "sources": []})
    keys = list(redis_client.scan_iter("qa:*"))
    assert len(keys) == 1
    assert redis_client.ttl(keys[0]) > 0


def test_qa_cache_ttl_expiry(redis_client):
    """TTL 到期后应 miss。"""
    cache = QACache(redis_client, ttl=1)
    cache.set("Q", {"answer": "A", "sources": []})
    assert cache.get("Q") is not None
    time.sleep(1.2)
    assert cache.get("Q") is None


def test_qa_cache_invalidate_kb(redis_client):
    cache = QACache(redis_client)
    cache.set("Q1", {"answer": "A", "sources": []}, kb="kb1")
    cache.set("Q2", {"answer": "B", "sources": []}, kb="kb2")

    deleted = cache.invalidate_kb("kb1")
    assert deleted >= 1
    assert cache.get("Q1", kb="kb1") is None
    assert cache.get("Q2", kb="kb2") is not None  # kb2 未受影响


def test_qa_cache_invalidate_all(redis_client):
    cache = QACache(redis_client)
    cache.set("Q1", {"answer": "A", "sources": []}, kb="kb1")
    cache.set("Q2", {"answer": "B", "sources": []}, kb="kb2")

    deleted = cache.invalidate_all()
    assert deleted >= 2
    assert cache.get("Q1", kb="kb1") is None
    assert cache.get("Q2", kb="kb2") is None


def test_embedding_cache_invalidate_all(redis_client):
    from app.cache.embedding_cache import EmbeddingCache

    emb_cache = EmbeddingCache(redis_client)
    emb_cache.set("hello", [0.1, 0.2])
    assert emb_cache.get("hello") is not None

    deleted = emb_cache.invalidate_all()
    assert deleted >= 1
    assert emb_cache.get("hello") is None
