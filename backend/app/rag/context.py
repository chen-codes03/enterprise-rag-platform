"""上下文拼接与溯源构建。

将检索到的文档拼成带编号的上下文，并构建结构化来源信息用于溯源。
"""
from __future__ import annotations

from langchain_core.documents import Document


def build_context(docs: list[Document]) -> str:
    """拼接文档为带编号的上下文字符串。"""
    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知")
        section = doc.metadata.get("section", "")
        header = f"[{i}] 来源: {source}" + (f"（{section}）" if section else "")
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n".join(parts)


def build_sources(docs: list[Document]) -> list[dict]:
    """构建结构化来源列表，用于回答溯源。"""
    sources: list[dict] = []
    for i, doc in enumerate(docs, 1):
        sources.append(
            {
                "index": i,
                "source": doc.metadata.get("source", "未知"),
                "section": doc.metadata.get("section", ""),
                "content": doc.page_content,
            }
        )
    return sources
