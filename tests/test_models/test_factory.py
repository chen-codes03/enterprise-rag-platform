"""T1.11 RED: 模型工厂测试。验证按 Settings.provider 返回对应 provider，
未知 provider 抛 ValueError。
"""
import pytest


def test_factory_returns_deepseek(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dk-test")
    from app.models.deepseek import DeepSeekProvider
    from app.models.factory import get_model_provider

    provider = get_model_provider()
    assert isinstance(provider, DeepSeekProvider)


def test_factory_returns_qwen(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "qwen")
    monkeypatch.setenv("QWEN_API_KEY", "qwen-test")
    from app.models.factory import get_model_provider
    from app.models.qwen import QwenProvider

    provider = get_model_provider()
    assert isinstance(provider, QwenProvider)


def test_factory_unknown_raises_valueerror(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "unknown-llm")
    from app.models.factory import get_model_provider

    with pytest.raises(ValueError):
        get_model_provider()


def test_factory_returns_model_provider(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dk-test")
    from app.models.base import ModelProvider
    from app.models.factory import get_model_provider

    provider = get_model_provider()
    assert isinstance(provider, ModelProvider)
