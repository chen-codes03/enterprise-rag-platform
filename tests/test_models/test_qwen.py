"""T1.5 RED: 通义千问 provider 测试。"""
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage


def _fake_llm(reply: str):
    return FakeMessagesListChatModel(responses=[AIMessage(content=reply)])


def test_qwen_chat_returns_chat_result():
    from app.models.base import ChatResult, Message
    from app.models.qwen import QwenProvider

    provider = QwenProvider(llm=_fake_llm("Qwen 回答"))
    result = provider.chat([Message(role="human", content="你好")])

    assert isinstance(result, ChatResult)
    assert result.content == "Qwen 回答"


def test_qwen_is_model_provider():
    from app.models.base import ModelProvider
    from app.models.qwen import QwenProvider

    assert issubclass(QwenProvider, ModelProvider)


def test_qwen_builds_chat_openai_from_settings(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "qwen-test")
    monkeypatch.setenv("QWEN_MODEL", "qwen-plus")
    from app.models.qwen import QwenProvider

    provider = QwenProvider.from_settings()
    assert provider.llm.model_name == "qwen-plus"
