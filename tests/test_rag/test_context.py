"""T3.5 RED: 上下文拼接测试。"""
from langchain_core.documents import Document

from app.rag.context import build_context, build_sources


def test_build_context_numbers_documents():
    docs = [
        Document(page_content="内容A", metadata={"source": "a.md", "section": "x"}),
        Document(page_content="内容B", metadata={"source": "b.md", "section": "y"}),
    ]
    ctx = build_context(docs)
    assert "[1]" in ctx and "[2]" in ctx
    assert "内容A" in ctx and "内容B" in ctx
    assert "a.md" in ctx and "b.md" in ctx


def test_build_context_separator_between_docs():
    docs = [
        Document(page_content="第一段", metadata={"source": "a.md"}),
        Document(page_content="第二段", metadata={"source": "b.md"}),
    ]
    ctx = build_context(docs)
    assert "第一段" in ctx and "第二段" in ctx
    # 两段之间应有分隔
    assert ctx.index("第一段") < ctx.index("第二段")


def test_build_sources_structure():
    docs = [Document(page_content="片段内容", metadata={"source": "a.md", "section": "x"})]
    sources = build_sources(docs)
    assert len(sources) == 1
    s = sources[0]
    assert s["index"] == 1
    assert s["source"] == "a.md"
    assert s["section"] == "x"
    assert s["content"] == "片段内容"


def test_build_sources_indices_sequential():
    docs = [
        Document(page_content="a", metadata={"source": "1"}),
        Document(page_content="b", metadata={"source": "2"}),
        Document(page_content="c", metadata={"source": "3"}),
    ]
    sources = build_sources(docs)
    assert [s["index"] for s in sources] == [1, 2, 3]
