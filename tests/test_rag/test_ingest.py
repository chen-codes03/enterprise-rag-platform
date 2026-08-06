"""T2.13 RED: ingest 管道测试。端到端：文档 → 块 → 向量 → 存储。"""
from langchain_core.documents import Document


def _store(tmp_chroma_dir, collection):
    from app.rag.embeddings import DeterministicEmbeddings
    from app.rag.vectorstore import get_vectorstore

    return get_vectorstore(
        embeddings=DeterministicEmbeddings(dim=16),
        persist_dir=str(tmp_chroma_dir),
        collection=collection,
    )


def test_ingest_file_end_to_end(tmp_path, tmp_chroma_dir):
    from app.rag.ingest import ingest_file

    md = tmp_path / "kb.md"
    md.write_text("# 知识库\n\n企业报销流程说明。" * 20, encoding="utf-8")
    store = _store(tmp_chroma_dir, "ingest_e2e")

    n = ingest_file(md, store=store, chunk_size=100, chunk_overlap=20)
    assert n > 0

    results = store.similarity_search("报销", k=2)
    assert len(results) >= 1
    assert all(r.metadata.get("source") for r in results)


def test_ingest_documents_returns_chunk_count(tmp_chroma_dir):
    from app.rag.ingest import ingest_documents

    store = _store(tmp_chroma_dir, "ingest_docs")
    docs = [Document(page_content="A" * 600, metadata={"source": "s"})]
    n = ingest_documents(docs, store=store, chunk_size=100, chunk_overlap=20)
    assert n > 1


def test_ingest_preserves_source_metadata(tmp_path, tmp_chroma_dir):
    from app.rag.ingest import ingest_file

    md = tmp_path / "meta.md"
    md.write_text("# 制度\n\n考勤制度详细说明内容。" * 10, encoding="utf-8")
    store = _store(tmp_chroma_dir, "ingest_meta")
    ingest_file(md, store=store, chunk_size=80, chunk_overlap=10)

    results = store.similarity_search("考勤", k=3)
    for r in results:
        assert r.metadata["source"] == str(md)
