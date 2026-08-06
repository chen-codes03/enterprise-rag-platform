"""T4.5 RED: Embedding 缓存测试。验证命中缓存时不再调用底层 embed。"""
from langchain_core.embeddings import Embeddings

from app.cache.embedding_cache import CachedEmbeddings, EmbeddingCache


class CountingEmbeddings(Embeddings):
    """计数 embed 调用次数的假 Embedding。"""

    def __init__(self) -> None:
        self.calls = 0

    def embed_documents(self, texts):
        self.calls += 1
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    def embed_query(self, text):
        self.calls += 1
        return [0.1, 0.2, 0.3, 0.4]


def test_embed_query_cache_hit_avoids_base_call(redis_client):
    base = CountingEmbeddings()
    cached = CachedEmbeddings(base, EmbeddingCache(redis_client))

    v1 = cached.embed_query("hello")
    v2 = cached.embed_query("hello")

    assert base.calls == 1  # 第二次命中缓存
    assert v1 == v2


def test_embed_query_different_text_calls_base(redis_client):
    base = CountingEmbeddings()
    cached = CachedEmbeddings(base, EmbeddingCache(redis_client))

    cached.embed_query("hello")
    cached.embed_query("world")

    assert base.calls == 2


def test_embed_documents_partial_cache_hit(redis_client):
    base = CountingEmbeddings()
    emb_cache = EmbeddingCache(redis_client)
    # 预先缓存第一条
    emb_cache.set("a", [0.5, 0.5, 0.5, 0.5])
    cached = CachedEmbeddings(base, emb_cache)

    vectors = cached.embed_documents(["a", "b"])
    assert vectors[0] == [0.5, 0.5, 0.5, 0.5]  # 命中缓存
    assert vectors[1] == [0.1, 0.2, 0.3, 0.4]  # 回源
    assert base.calls == 1  # 只回源一条
