"""T1.7: 异步调用测试。验证 async_chat 可 await 且返回 ChatResult。"""
import pytest

from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.models.base import Message
from app.models.deepseek import DeepSeekProvider


def _fake_llm(reply: str):
    return FakeMessagesListChatModel(responses=[AIMessage(content=reply)])


@pytest.mark.asyncio
async def test_async_chat_returns_chat_result():
    provider = DeepSeekProvider(llm=_fake_llm("异步回答"))
    result = await provider.async_chat([Message(role="human", content="你好")])

    from app.models.base import ChatResult

    assert isinstance(result, ChatResult)
    assert result.content == "异步回答"


@pytest.mark.asyncio
async def test_async_chat_distinct_from_sync():
    """同步与异步应返回相同内容但走不同路径。"""
    provider = DeepSeekProvider(llm=_fake_llm("一致回答"))
    sync_res = provider.chat([Message(role="human", content="hi")])
    async_res = await provider.async_chat([Message(role="human", content="hi")])
    assert sync_res.content == async_res.content == "一致回答"
