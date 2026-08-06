"""T2.7 RED: 文本分块测试。验证 chunk_size/overlap 参数生效、
块大小受控、重叠正确、元数据保留。
"""
from langchain_core.documents import Document


def test_split_creates_multiple_chunks():
    from app.rag.splitters import split_documents

    docs = [Document(page_content="A" * 750, metadata={"source": "s"})]
    chunks = split_documents(docs, chunk_size=100, chunk_overlap=20)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.page_content) <= 100


def test_split_overlap_between_consecutive_chunks():
    """连续块应共享 overlap 长度的文本。"""
    from app.rag.splitters import split_documents

    text = "abcdefghij" * 30  # 300 字符，无分隔符 → 按字符切
    docs = [Document(page_content=text, metadata={"source": "s"})]
    chunks = split_documents(docs, chunk_size=50, chunk_overlap=10)

    assert len(chunks) >= 2
    # chunk[i] 末尾 10 字符 == chunk[i+1] 开头 10 字符
    assert chunks[0].page_content[-10:] == chunks[1].page_content[:10]


def test_split_preserves_metadata():
    from app.rag.splitters import split_documents

    docs = [Document(page_content="内容 " * 200, metadata={"source": "doc.md", "format": "markdown"})]
    chunks = split_documents(docs, chunk_size=100, chunk_overlap=20)

    assert len(chunks) > 1
    for c in chunks:
        assert c.metadata["source"] == "doc.md"
        assert c.metadata["format"] == "markdown"


def test_split_default_params_from_settings(monkeypatch):
    """默认参数应取自 Settings。"""
    monkeypatch.setenv("CHUNK_SIZE", "300")
    monkeypatch.setenv("CHUNK_OVERLAP", "30")
    from app.rag.splitters import split_documents

    docs = [Document(page_content="X" * 600, metadata={"source": "s"})]
    chunks = split_documents(docs)  # 使用默认（Settings）参数
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.page_content) <= 300
