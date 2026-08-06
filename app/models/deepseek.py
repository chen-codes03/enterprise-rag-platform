"""DeepSeek 模型 provider。

DeepSeek 提供 OpenAI 兼容接口，基于 LangChain ChatOpenAI 封装。
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.models.base import _LangChainProvider


class DeepSeekProvider(_LangChainProvider):
    """DeepSeek 大模型调用 provider。"""

    def __init__(self, llm=None, settings: Settings | None = None) -> None:
        if llm is None:
            llm = self.build_llm(settings or get_settings())
        super().__init__(llm)

    @staticmethod
    def build_llm(settings: Settings) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "DeepSeekProvider":
        return cls(settings=settings)
