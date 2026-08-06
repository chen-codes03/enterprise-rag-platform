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
    source_name: str | None = None,
) -> int:
    """解析单个文件并入库，返回入库块数。

    source_name：可选的原始文件名，用于覆盖 metadata.source，
    避免上传场景下溯源来源显示为临时文件路径。未提供时沿用 path。
    """
    documents = load_document(path)
    if source_name:
        for doc in documents:
            doc.metadata["source"] = source_name
    return ingest_documents(documents, store, chunk_size, chunk_overlap)
