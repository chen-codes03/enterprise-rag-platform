"""T1.1 RED: 模型层抽象基类测试。

验证 ModelProvider 为 ABC，定义 chat/async_chat/stream 抽象方法，
子类未实现时实例化抛 TypeError。
"""
import inspect

import pytest


def test_model_provider_is_abstract():
    from app.models.base import ModelProvider

    assert inspect.isabstract(ModelProvider)


def test_model_provider_abstract_methods():
    from app.models.base import ModelProvider

    abstract = ModelProvider.__abstractmethods__
    assert "chat" in abstract
    assert "async_chat" in abstract
    assert "stream" in abstract


def test_incomplete_subclass_raises_typeerror():
    from app.models.base import ModelProvider

    class Incomplete(ModelProvider):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_message_dataclass_fields():
    from app.models.base import Message

    m = Message(role="human", content="你好")
    assert m.role == "human"
    assert m.content == "你好"


def test_chat_result_dataclass():
    from app.models.base import ChatResult

    r = ChatResult(content="回答")
    assert r.content == "回答"


def test_stream_chunk_dataclass():
    from app.models.base import StreamChunk

    c = StreamChunk(content="片", done=False)
    assert c.content == "片"
    assert c.done is False


def test_to_lc_messages_empty_raises():
    from app.models.base import _LangChainProvider

    with pytest.raises(ValueError, match="不能为空"):
        _LangChainProvider._to_lc_messages([])


def test_to_lc_messages_unknown_role_raises():
    from app.models.base import Message, _LangChainProvider

    with pytest.raises(ValueError, match="未知的消息角色"):
        _LangChainProvider._to_lc_messages([Message(role="robot", content="x")])
