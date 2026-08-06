"""模型 provider 工厂。

按 Settings.model_provider 配置返回对应的 provider 实例，
实现"改配置即可切换模型"，降低模型切换成本。
"""
from __future__ import annotations

from app.config import Settings, get_settings
from app.models.base import ModelProvider
from app.models.deepseek import DeepSeekProvider
from app.models.fake import FakeProvider
from app.models.qwen import QwenProvider

# provider 注册表，便于扩展新模型
_PROVIDERS: dict[str, type] = {
    "deepseek": DeepSeekProvider,
    "qwen": QwenProvider,
    "fake": FakeProvider,
}


def get_model_provider(settings: Settings | None = None) -> ModelProvider:
    """根据配置返回模型 provider 实例。"""
    settings = settings or get_settings()
    provider_name = settings.model_provider
    cls = _PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(
            f"未知的模型 provider: {provider_name}，可选: {list(_PROVIDERS)}"
        )
    return cls.from_settings(settings)
