"""T1.3 RED: DeepSeek provider 测试。

通过注入 FakeMessagesListChatModel 验证同步调用返回 ChatResult，
不触达真实 API。
"""
import pytest


def _fake_llm(reply: str):
    """构造一个返回固定回复的假 LangChain chat model。"""
    from langchain_core.language_models.fake_chat_models import (
        FakeMessagesListChatModel,
    )
    from langchain_core.messages import AIMessage

    return FakeMessagesListChatModel(responses=[AIMessage(content=reply)])


def test_deepseek_chat_returns_chat_result():
    from app.models.base import ChatResult, Message
    from app.models.deepseek import DeepSeekProvider

    provider = DeepSeekProvider(llm=_fake_llm("DeepSeek 回答"))
    result = provider.chat([Message(role="human", content="你好")])

    assert isinstance(result, ChatResult)
    assert result.content == "DeepSeek 回答"


def test_deepseek_chat_multi_messages():
    from app.models.base import Message
    from app.models.deepseek import DeepSeekProvider

    provider = DeepSeekProvider(llm=_fake_llm("收到"))
    messages = [
        Message(role="system", content="你是助手"),
        Message(role="human", content="提问"),
    ]
    result = provider.chat(messages)
    assert result.content == "收到"


def test_deepseek_is_model_provider():
    from app.models.base import ModelProvider
    from app.models.deepseek import DeepSeekProvider

    assert issubclass(DeepSeekProvider, ModelProvider)


def test_deepseek_builds_chat_openai_from_settings(monkeypatch):
    """未注入 llm 时，应基于 Settings 构建 ChatOpenAI（验证构造不报错）。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dk-test")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    from app.models.deepseek import DeepSeekProvider

    provider = DeepSeekProvider.from_settings()
    # 内部 llm 应为 ChatOpenAI，模型名正确
    assert provider.llm.model_name == "deepseek-chat"
