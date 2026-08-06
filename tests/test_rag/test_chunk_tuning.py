"""T3.9: chunk 参数与 top_k 调优测试。验证可调参数影响召回粒度与数量。"""
from langchain_core.documents import Document


def test_chunk_size_affects_chunk_count():
    from app.rag.splitters import split_documents

    text = "企业知识库内容片段。" * 80
    docs = [Document(page_content=text, metadata={"source": "s"})]
    small = split_documents(docs, chunk_size=50, chunk_overlap=10)
    large = split_documents(docs, chunk_size=300, chunk_overlap=30)
    assert len(small) > len(large)


def test_top_k_controls_retrieval_count(kb_store):
    from app.rag.retriever import retrieve

    r2 = retrieve(kb_store, "流程", k=2)
    r4 = retrieve(kb_store, "流程", k=4)
    assert len(r2) <= 2
    assert len(r4) >= len(r2)


def test_small_chunk_yields_shorter_retrieved_content(tmp_chroma_dir):
    """小 chunk 入库后检索到的片段更短，体现粒度可调。"""
    from app.rag.embeddings import DeterministicEmbeddings
    from app.rag.ingest import ingest_documents
    from app.rag.retriever import retrieve
    from app.rag.vectorstore import get_vectorstore

    long_text = "报销流程说明内容详细描述步骤。" * 30
    docs = [Document(page_content=long_text, metadata={"source": "s"})]
    store = get_vectorstore(
        embeddings=DeterministicEmbeddings(dim=16),
        persist_dir=str(tmp_chroma_dir / "small"),
        collection="small_chunks",
    )
    ingest_documents(docs, store=store, chunk_size=40, chunk_overlap=5)

    results = retrieve(store, "报销", k=1)
    assert len(results) == 1
    assert len(results[0].page_content) <= 40
