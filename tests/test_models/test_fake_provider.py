"""Fake provider 测试：验证离线演示模式可用。"""
import pytest

from app.models.factory import get_model_provider
from app.models.fake import FakeProvider
from app.models.base import Message


def test_fake_provider_chat_returns_reply():
    provider = FakeProvider()
    result = provider.chat([Message(role="human", content="你好")])
    assert result.content == FakeProvider.DEFAULT_REPLY


@pytest.mark.asyncio
async def test_fake_provider_async_chat():
    provider = FakeProvider()
    result = await provider.async_chat([Message(role="human", content="你好")])
    assert result.content == FakeProvider.DEFAULT_REPLY


@pytest.mark.asyncio
async def test_fake_provider_stream():
    provider = FakeProvider()
    chunks = []
    async for chunk in provider.stream([Message(role="human", content="你好")]):
        chunks.append(chunk)
    # 至少收到内容 chunk + 结束 chunk
    assert len(chunks) >= 2
    assert chunks[-1].done is True


def test_factory_returns_fake_provider(isolated_env, monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    from app.config import get_settings

    get_settings.cache_clear()
    provider = get_model_provider()
    assert isinstance(provider, FakeProvider)


def test_fake_provider_from_settings():
    provider = FakeProvider.from_settings()
    assert isinstance(provider, FakeProvider)
