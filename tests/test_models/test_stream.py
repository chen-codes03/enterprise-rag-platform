"""T1.9: 流式输出测试。验证 stream 产出多个片段并以 done=True 结束。"""
import pytest

from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.models.base import Message, StreamChunk
from app.models.deepseek import DeepSeekProvider


def _fake_llm(reply: str):
    return FakeMessagesListChatModel(responses=[AIMessage(content=reply)])


@pytest.mark.asyncio
async def test_stream_yields_chunks_and_done():
    provider = DeepSeekProvider(llm=_fake_llm("流式回复内容"))
    chunks: list[StreamChunk] = []
    async for chunk in provider.stream([Message(role="human", content="讲讲")]):
        chunks.append(chunk)

    assert len(chunks) >= 1
    # 最后一个片段标记结束
    assert chunks[-1].done is True
    # 拼接非结束片段内容应包含完整回复
    full = "".join(c.content for c in chunks if not c.done)
    assert "流式回复内容" in full


@pytest.mark.asyncio
async def test_stream_chunks_are_stream_chunk_type():
    provider = DeepSeekProvider(llm=_fake_llm("类型检查"))
    async for chunk in provider.stream([Message(role="human", content="hi")]):
        assert isinstance(chunk, StreamChunk)
        break  # 只需验证第一个片段类型
