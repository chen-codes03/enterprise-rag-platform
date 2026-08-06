"""修复 A: get_rag_chain 组件单例化测试。

验证 store / provider / qa_cache 被缓存复用，避免每次请求重复初始化
（尤其 Chroma 客户端的持久化重载开销）。
"""
import app.api.deps as deps


def test_get_store_is_cached(monkeypatch):
    """get_store 多次调用应返回同一 Chroma 实例。"""
    deps._get_store_cached.cache_clear()
    calls = []

    class _FakeStore:
        pass

    class _FakeEmbeddings:
        def embed_query(self, t):
            return [0.0]

        def embed_documents(self, ts):
            return [[0.0] for _ in ts]

    def fake_get_vectorstore(**kwargs):
        calls.append(1)
        return _FakeStore()

    monkeypatch.setattr("app.rag.vectorstore.get_vectorstore", fake_get_vectorstore)
    monkeypatch.setattr("app.rag.embeddings.get_embeddings", lambda *a, **k: _FakeEmbeddings())
    monkeypatch.setattr(
        "app.cache.redis_client.get_redis_client", lambda *a, **k: object()
    )
    try:
        s1 = deps._get_store_cached()
        s2 = deps._get_store_cached()
        assert s1 is s2
        assert len(calls) == 1
    finally:
        deps._get_store_cached.cache_clear()


def test_get_qa_cache_is_cached(monkeypatch):
    """qa_cache 多次调用应返回同一 QACache 实例。"""
    deps._get_qa_cache_cached.cache_clear()
    calls = []

    class _FakeQACache:
        pass

    def fake_get_redis_client(**kwargs):
        calls.append(1)
        return _FakeQACache()

    monkeypatch.setattr(
        "app.cache.redis_client.get_redis_client", fake_get_redis_client
    )
    try:
        c1 = deps._get_qa_cache_cached()
        c2 = deps._get_qa_cache_cached()
        assert c1 is c2
        assert len(calls) == 1
    finally:
        deps._get_qa_cache_cached.cache_clear()


def test_get_model_provider_is_cached(monkeypatch):
    """model provider 多次调用应返回同一实例。"""
    deps._get_provider_cached.cache_clear()
    calls = []

    class _FakeProvider:
        pass

    def fake_factory(*args, **kwargs):
        calls.append(1)
        return _FakeProvider()

    monkeypatch.setattr("app.models.factory.get_model_provider", fake_factory)
    try:
        p1 = deps._get_provider_cached()
        p2 = deps._get_provider_cached()
        assert p1 is p2
        assert len(calls) == 1
    finally:
        deps._get_provider_cached.cache_clear()
