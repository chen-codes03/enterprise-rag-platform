"""T2.9 RED: Embedding 层测试。"""
import pytest


def test_deterministic_embeddings_consistent():
    from app.rag.embeddings import DeterministicEmbeddings

    e = DeterministicEmbeddings(dim=8)
    v1 = e.embed_query("你好")
    v2 = e.embed_query("你好")
    assert v1 == v2
    assert len(v1) == 8


def test_deterministic_embeddings_different_text_differs():
    from app.rag.embeddings import DeterministicEmbeddings

    e = DeterministicEmbeddings(dim=8)
    assert e.embed_query("你好") != e.embed_query("世界")


def test_embed_documents_returns_correct_count():
    from app.rag.embeddings import DeterministicEmbeddings

    e = DeterministicEmbeddings(dim=4)
    vectors = e.embed_documents(["a", "b", "c"])
    assert len(vectors) == 3
    assert all(len(v) == 4 for v in vectors)


def test_get_embeddings_fake_provider(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "fake")
    monkeypatch.setenv("EMBEDDING_DIMENSION", "8")
    from app.rag.embeddings import DeterministicEmbeddings, get_embeddings

    e = get_embeddings()
    assert isinstance(e, DeterministicEmbeddings)
    assert len(e.embed_query("x")) == 8


def test_get_embeddings_openai_provider(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    from langchain_openai import OpenAIEmbeddings

    from app.rag.embeddings import get_embeddings

    e = get_embeddings()
    assert isinstance(e, OpenAIEmbeddings)


def test_get_embeddings_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "unknown-emb")
    from app.rag.embeddings import get_embeddings

    with pytest.raises(ValueError):
        get_embeddings()
