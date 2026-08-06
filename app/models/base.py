"""统一模型调用层抽象基类。

定义与具体模型解耦的消息与返回类型，以及 ModelProvider 抽象接口。
_LangChainProvider 提供基于 LangChain BaseChatModel 的共享实现，
具体 provider（DeepSeek/Qwen）只需提供配置差异，降低模型切换成本。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

_ROLE_TO_LC = {"system": SystemMessage, "human": HumanMessage, "ai": AIMessage}


@dataclass(frozen=True)
class Message:
    """统一的输入消息。role: system | human | ai。"""

    role: str
    content: str


@dataclass(frozen=True)
class ChatResult:
    """同步/异步调用的统一返回。"""

    content: str


@dataclass(frozen=True)
class StreamChunk:
    """流式输出的单个片段。done=True 表示流结束。"""

    content: str
    done: bool = False


class ModelProvider(ABC):
    """模型调用层抽象。子类需实现 chat / async_chat / stream。"""

    @abstractmethod
    def chat(self, messages: list[Message]) -> ChatResult:
        """同步对话。"""

    @abstractmethod
    async def async_chat(self, messages: list[Message]) -> ChatResult:
        """异步对话。"""

    @abstractmethod
    def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
        """流式输出（async generator）。"""


class _LangChainProvider(ModelProvider):
    """基于 LangChain BaseChatModel 的共享实现。

    具体子类通过 __init__ 注入或 from_settings 构建 llm 即可，
    无需重复实现 chat / async_chat / stream。
    """

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm

    @staticmethod
    def _to_lc_messages(messages: list[Message]) -> list[BaseMessage]:
        if not messages:
            raise ValueError("messages 不能为空")
        result: list[BaseMessage] = []
        for m in messages:
            cls = _ROLE_TO_LC.get(m.role)
            if cls is None:
                raise ValueError(f"未知的消息角色: {m.role}")
            result.append(cls(content=m.content))
        return result

    def chat(self, messages: list[Message]) -> ChatResult:
        resp = self.llm.invoke(self._to_lc_messages(messages))
        return ChatResult(content=resp.content)

    async def async_chat(self, messages: list[Message]) -> ChatResult:
        resp = await self.llm.ainvoke(self._to_lc_messages(messages))
        return ChatResult(content=resp.content)

    async def stream(self, messages: list[Message]) -> AsyncIterator[StreamChunk]:
        lc_messages = self._to_lc_messages(messages)
        async for chunk in self.llm.astream(lc_messages):
            yield StreamChunk(content=chunk.content, done=False)
        yield StreamChunk(content="", done=True)
