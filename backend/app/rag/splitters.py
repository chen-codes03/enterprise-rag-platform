"""文本分块。

基于 LangChain RecursiveCharacterTextSplitter，chunk_size/overlap 可配，
默认值取自 Settings，便于通过调参优化召回效果（G3）。
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings


def make_splitter(
    chunk_size: int | None = None, chunk_overlap: int | None = None
) -> RecursiveCharacterTextSplitter:
    """构造分块器，未指定参数时取 Settings 默认值。"""
    settings = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size if chunk_size is not None else settings.chunk_size,
        chunk_overlap=chunk_overlap if chunk_overlap is not None else settings.chunk_overlap,
    )


def split_documents(
    docs: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """将文档分块，保留原始 metadata。"""
    return make_splitter(chunk_size, chunk_overlap).split_documents(docs)
