"""通义千问（Qwen）模型 provider。

DashScope 提供 OpenAI 兼容接口，基于 LangChain ChatOpenAI 封装。
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.models.base import _LangChainProvider


class QwenProvider(_LangChainProvider):
    """通义千问大模型调用 provider。"""

    def __init__(self, llm=None, settings: Settings | None = None) -> None:
        if llm is None:
            llm = self.build_llm(settings or get_settings())
        super().__init__(llm)

    @staticmethod
    def build_llm(settings: Settings) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.qwen_model,
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url,
        )

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "QwenProvider":
        return cls(settings=settings)
