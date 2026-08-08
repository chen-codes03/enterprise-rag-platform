"""模型 provider 工厂。

按 Settings.model_provider 配置返回对应的 provider 实例，
实现"改配置即可切换模型"，降低模型切换成本。
"""
from __future__ import annotations

import warnings

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

# 各 provider 对应的 api_key 字段名，用于 fallback 检测
_PROVIDER_API_KEY_FIELD: dict[str, str] = {
    "deepseek": "deepseek_api_key",
    "qwen": "qwen_api_key",
}


def get_model_provider(settings: Settings | None = None) -> ModelProvider:
    """根据配置返回模型 provider 实例。

    若配置了真实大模型（deepseek/qwen）但未填写 API key，
    自动降级到 fake 演示模式，避免启动后调用失败。
    """
    settings = settings or get_settings()
    provider_name = settings.model_provider

    # Fallback：配置了真实大模型但缺 API key → 降级到 fake
    api_key_field = _PROVIDER_API_KEY_FIELD.get(provider_name)
    if api_key_field and not getattr(settings, api_key_field, ""):
        warnings.warn(
            f"MODEL_PROVIDER={provider_name} 但未配置 API key，"
            f"自动降级到 fake 演示模式。请在 .env 中配置 "
            f"{api_key_field.upper()} 以启用真实大模型。",
            RuntimeWarning,
            stacklevel=2,
        )
        provider_name = "fake"

    cls = _PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(
            f"未知的模型 provider: {provider_name}，可选: {list(_PROVIDERS)}"
        )
    return cls.from_settings(settings)
