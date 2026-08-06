"""T3.7 RED: RAG 问答链路测试。"""
import pytest
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.models.deepseek import DeepSeekProvider
from app.rag.chain import RAGAnswer, RAGChain


def _provider(reply: str) -> DeepSeekProvider:
    llm = FakeMessagesListChatModel(responses=[AIMessage(content=reply)])
    return DeepSeekProvider(llm=llm)


def test_rag_chain_ask_returns_answer_and_sources(kb_store):
    chain = RAGChain(store=kb_store, model_provider=_provider("报销需在OA系统提交报销单并附发票 [1]。"))
    result = chain.ask("如何报销？")

    assert isinstance(result, RAGAnswer)
    assert "OA系统" in result.answer
    assert len(result.sources) >= 1
    assert all("source" in s for s in result.sources)


def test_rag_chain_sources_have_metadata(kb_store):
    chain = RAGChain(store=kb_store, model_provider=_provider("回答"))
    result = chain.ask("请假流程")
    for s in result.sources:
        assert "index" in s
        assert "source" in s
        assert "content" in s
        assert s["source"]


@pytest.mark.asyncio
async def test_rag_chain_async_ask(kb_store):
    chain = RAGChain(store=kb_store, model_provider=_provider("异步回答内容"))
    result = await chain.async_ask("入职流程")

    assert result.answer == "异步回答内容"
    assert len(result.sources) >= 1


@pytest.mark.asyncio
async def test_rag_chain_astream_yields_answer(kb_store):
    chain = RAGChain(store=kb_store, model_provider=_provider("流式回答内容"))
    chunks = []
    async for chunk in chain.astream("部署流程"):
        chunks.append(chunk)
    full = "".join(chunks)
    assert "流式回答内容" in full


@pytest.mark.asyncio
async def test_rag_chain_astream_accepts_precomputed_docs(kb_store):
    """astream 接受预检索的 docs，避免重复检索。"""
    chain = RAGChain(store=kb_store, model_provider=_provider("预检索回答"))
    docs = chain.retrieve("入职")
    chunks = []
    async for chunk in chain.astream("入职流程", docs=docs):
        chunks.append(chunk)
    assert "".join(chunks) == "预检索回答"


def test_rag_chain_topk_controls_sources_count(kb_store):
    chain = RAGChain(store=kb_store, model_provider=_provider("回答"), top_k=2)
    result = chain.ask("流程")
    assert len(result.sources) <= 2
