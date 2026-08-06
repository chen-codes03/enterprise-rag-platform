"""文档入库管道。

编排：文档解析（loaders）→ 文本分块（splitters）→ 向量库存储（vectorstore）。
"""
from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.rag.loaders import load_document
from app.rag.splitters import split_documents
from app.rag.vectorstore import get_vectorstore


def ingest_documents(
    documents: list[Document],
    store: Chroma | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """将文档分块后写入向量库，返回入库块数。"""
    chunks = split_documents(documents, chunk_size, chunk_overlap)
    store = store or get_vectorstore()
    store.add_documents(chunks)
    return len(chunks)


def ingest_file(
    path: str | Path,
    store: Chroma | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """解析单个文件并入库，返回入库块数。"""
    documents = load_document(path)
    return ingest_documents(documents, store, chunk_size, chunk_overlap)
