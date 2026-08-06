"""T2.11 RED: 向量库测试。验证 Chroma 持久化存储与相似度检索。"""
from langchain_core.documents import Document


def _store(tmp_chroma_dir, dim=16, collection="test"):
    from app.rag.embeddings import DeterministicEmbeddings
    from app.rag.vectorstore import get_vectorstore

    return get_vectorstore(
        embeddings=DeterministicEmbeddings(dim=dim),
        persist_dir=str(tmp_chroma_dir),
        collection=collection,
    )


def test_vectorstore_add_documents_returns_ids(tmp_chroma_dir):
    store = _store(tmp_chroma_dir)
    ids = store.add_documents(
        [
            Document(page_content="企业知识库使用说明", metadata={"source": "a.md"}),
            Document(page_content="请假流程与考勤制度", metadata={"source": "b.md"}),
            Document(page_content="服务器部署文档", metadata={"source": "c.md"}),
        ]
    )
    assert len(ids) == 3


def test_vectorstore_similarity_search_topk(tmp_chroma_dir):
    store = _store(tmp_chroma_dir)
    store.add_documents(
        [
            Document(page_content="企业知识库使用说明", metadata={"source": "a.md"}),
            Document(page_content="请假流程与考勤制度", metadata={"source": "b.md"}),
            Document(page_content="服务器部署文档", metadata={"source": "c.md"}),
        ]
    )
    results = store.similarity_search("知识库", k=2)
    assert len(results) <= 2
    assert all(r.metadata.get("source") for r in results)


def test_vectorstore_persists_across_instances(tmp_chroma_dir):
    store = _store(tmp_chroma_dir, collection="persist_test")
    store.add_documents([Document(page_content="持久化测试内容", metadata={"source": "x"})])

    # 重新打开同一持久化目录与 collection
    store2 = _store(tmp_chroma_dir, collection="persist_test")
    results = store2.similarity_search("持久化", k=1)
    assert len(results) == 1
    assert "持久化测试内容" in results[0].page_content


def test_add_documents_wrapper(tmp_chroma_dir):
    from app.rag.vectorstore import add_documents

    store = _store(tmp_chroma_dir, collection="wrapper")
    ids = add_documents(
        store, [Document(page_content="包装函数测试", metadata={"source": "w"})]
    )
    assert len(ids) == 1


def test_similarity_search_wrapper_uses_topk(tmp_chroma_dir, monkeypatch):
    from app.rag.vectorstore import add_documents, similarity_search

    monkeypatch.setenv("RETRIEVE_TOP_K", "1")
    store = _store(tmp_chroma_dir, collection="wrapper2")
    add_documents(
        store,
        [
            Document(page_content="甲", metadata={"source": "1"}),
            Document(page_content="乙", metadata={"source": "2"}),
            Document(page_content="丙", metadata={"source": "3"}),
        ],
    )
    results = similarity_search(store, "甲")
    assert len(results) == 1
