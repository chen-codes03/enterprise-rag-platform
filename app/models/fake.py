"""Fake 模型 provider。

用于离线演示与集成测试：不调用真实大模型 API，基于 LangChain
GenericFakeChatModel 返回固定/回显式回答，配合 fake embedding 可在
无网络、无 API key 环境下完整跑通 RAG 链路与 API 接口。
"""
from __future__ import annotations

from itertools import cycle

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from app.config import Settings, get_settings
from app.models.base import _LangChainProvider


class FakeProvider(_LangChainProvider):
    """假模型 provider，返回固定回答，用于离线演示。"""

    DEFAULT_REPLY = (
        "（演示模式）根据企业知识库检索到的上下文，这是一个示例回答。"
        "如需接入真实大模型，请配置 DeepSeek 或通义千问 API key。"
    )

    def __init__(self, llm=None, settings: Settings | None = None) -> None:
        if llm is None:
            llm = self.build_llm(settings or get_settings())
        super().__init__(llm)

    @staticmethod
    def build_llm(settings: Settings) -> GenericFakeChatModel:
        # 用 cycle 无限循环，避免单例 provider 下多次调用耗尽迭代器
        return GenericFakeChatModel(messages=cycle([FakeProvider.DEFAULT_REPLY]))

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "FakeProvider":
        return cls(settings=settings)
