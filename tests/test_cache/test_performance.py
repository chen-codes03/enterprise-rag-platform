"""T4.9: 缓存性能对比测试。验证缓存命中显著降低响应延迟（G4）。

用慢速 FakeLLM（每次调用 sleep）模拟真实大模型延迟，
对比有/无缓存下重复请求的总耗时。
"""
import time

from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.cache.qa_cache import QACache
from app.models.deepseek import DeepSeekProvider
from app.rag.chain import RAGChain


class SlowFakeLLM(FakeMessagesListChatModel):
    """每次生成 sleep 的假 LLM，模拟真实大模型延迟。"""

    delay: float = 0.05

    def __init__(self, responses, delay: float = 0.05) -> None:
        super().__init__(responses=responses, delay=delay)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        time.sleep(self.delay)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def _make_chain(kb_store, redis_client, cached: bool) -> RAGChain:
    provider = DeepSeekProvider(
        llm=SlowFakeLLM(responses=[AIMessage(content="答案内容")], delay=0.05)
    )
    qa_cache = QACache(redis_client) if cached else None
    return RAGChain(
        store=kb_store, model_provider=provider, top_k=3, qa_cache=qa_cache
    )


def test_cache_hit_returns_same_answer(kb_store, redis_client):
    chain = _make_chain(kb_store, redis_client, cached=True)
    r1 = chain.ask("报销流程")
    r2 = chain.ask("报销流程")
    assert r1.answer == r2.answer == "答案内容"
    assert r1.sources == r2.sources


def test_cache_improves_latency(kb_store, redis_client):
    query = "报销流程"
    n_repeat = 5

    uncached_chain = _make_chain(kb_store, redis_client, cached=False)
    cached_chain = _make_chain(kb_store, redis_client, cached=True)
    # 预热缓存
    cached_chain.ask(query)

    t0 = time.monotonic()
    for _ in range(n_repeat):
        uncached_chain.ask(query)
    uncached_time = time.monotonic() - t0

    t1 = time.monotonic()
    for _ in range(n_repeat):
        cached_chain.ask(query)
    cached_time = time.monotonic() - t1

    # 缓存命中应显著快于无缓存
    assert cached_time < uncached_time
    assert cached_time < uncached_time / 2


def test_cache_miss_still_works(kb_store, redis_client):
    """无缓存（qa_cache=None）时链路正常工作。"""
    chain = _make_chain(kb_store, redis_client, cached=False)
    result = chain.ask("入职流程")
    assert result.answer == "答案内容"
    assert len(result.sources) >= 1


def test_async_cache_hit_returns_cached(kb_store, redis_client):
    """async_ask 命中缓存应直接返回，不再调用 LLM。"""
    import asyncio

    chain = _make_chain(kb_store, redis_client, cached=True)
    r1 = chain.ask("报销流程")  # 同步写入缓存

    async def _a():
        return await chain.async_ask("报销流程")

    r2 = asyncio.run(_a())
    assert r2.answer == r1.answer == "答案内容"
    assert r2.sources == r1.sources
