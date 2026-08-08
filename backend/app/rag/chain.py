"""RAG 问答链路。

编排：语义检索 → 上下文拼接 → LLM 生成 → 溯源。
生成步骤使用 LangChain LCEL：prompt | llm | StrOutputParser()，
llm 由统一模型层 ModelProvider 提供，切换 provider 即切换底层模型。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from app.cache.qa_cache import QACache
from app.config import get_settings
from app.models.base import ModelProvider
from app.rag.context import build_context, build_sources
from app.rag.prompts import get_rag_prompt
from app.rag.reranker import rerank
from app.rag.retriever import retrieve


@dataclass
class RAGAnswer:
    """RAG 问答结果：答案 + 溯源来源。"""

    answer: str
    sources: list[dict] = field(default_factory=list)


class RAGChain:
    """RAG 问答链路。检索 + 上下文拼接 + LCEL 生成。"""

    def __init__(
        self,
        store: Chroma,
        model_provider: ModelProvider,
        top_k: int | None = None,
        qa_cache: QACache | None = None,
        kb: str = "default",
    ) -> None:
        self.store = store
        self.model_provider = model_provider
        self.top_k = top_k or get_settings().retrieve_top_k
        self.qa_cache = qa_cache  # 可插拔缓存，None 表示不缓存
        self.kb = kb
        # LCEL 生成链：prompt | llm | 解析为字符串
        self._answer_chain = (
            get_rag_prompt() | model_provider.llm | StrOutputParser()
        )

    def retrieve(self, query: str) -> list[Document]:
        """语义检索（公开，便于上层获取来源）。

        启用重排序时：向量检索召回 top_n 候选 → LLM 打分 → 取 top_k。
        未启用时：直接向量检索 top_k。
        """
        settings = get_settings()
        if not settings.rerank_enabled:
            return retrieve(self.store, query, k=self.top_k)

        # 向量检索召回更多候选用于重排序
        candidates = retrieve(self.store, query, k=settings.rerank_top_n)
        if len(candidates) <= self.top_k:
            return candidates

        # LLM 打分重排序
        return rerank(query, candidates, self.model_provider, top_k=self.top_k)

    def ask(self, query: str) -> RAGAnswer:
        """同步问答。命中缓存则直接返回，否则计算并回填缓存。"""
        if self.qa_cache is not None:
            cached = self.qa_cache.get(query, kb=self.kb)
            if cached is not None:
                return RAGAnswer(
                    answer=cached["answer"], sources=cached["sources"]
                )
        docs = self.retrieve(query)
        context = build_context(docs)
        answer = self._answer_chain.invoke(
            {"context": context, "question": query}
        )
        result = RAGAnswer(answer=answer, sources=build_sources(docs))
        if self.qa_cache is not None:
            self.qa_cache.set(
                query,
                {"answer": result.answer, "sources": result.sources},
                kb=self.kb,
            )
        return result

    async def async_ask(self, query: str) -> RAGAnswer:
        """异步问答。命中缓存则直接返回，否则计算并回填缓存。"""
        if self.qa_cache is not None:
            cached = self.qa_cache.get(query, kb=self.kb)
            if cached is not None:
                return RAGAnswer(
                    answer=cached["answer"], sources=cached["sources"]
                )
        docs = self.retrieve(query)
        context = build_context(docs)
        answer = await self._answer_chain.ainvoke(
            {"context": context, "question": query}
        )
        result = RAGAnswer(answer=answer, sources=build_sources(docs))
        if self.qa_cache is not None:
            self.qa_cache.set(
                query,
                {"answer": result.answer, "sources": result.sources},
                kb=self.kb,
            )
        return result

    async def astream(
        self, query: str, docs: list[Document] | None = None
    ) -> AsyncIterator[str]:
        """流式输出回答（逐 token）。可传入预检索 docs 避免重复检索。

        注：流式路径不经过 QA 缓存，适用于实时交互场景。
        """
        if docs is None:
            docs = self.retrieve(query)
        context = build_context(docs)
        async for chunk in self._answer_chain.astream(
            {"context": context, "question": query}
        ):
            yield chunk
