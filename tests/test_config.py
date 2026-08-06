"""T0.3 RED: 配置管理模块测试。

验证 Settings 能从环境变量读取应用配置、模型配置、RAG 参数、缓存参数，
并提供合理默认值。
"""
import pytest


def test_settings_reads_api_key(monkeypatch):
    """Settings 应从环境变量读取 API_KEY。"""
    monkeypatch.setenv("API_KEY", "sk-test-123")
    from app.config import Settings

    s = Settings()
    assert s.api_key == "sk-test-123"


def test_settings_model_provider_default(monkeypatch):
    """MODEL_PROVIDER 默认应为 deepseek。"""
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    from app.config import Settings

    s = Settings()
    assert s.model_provider == "deepseek"


def test_settings_model_provider_switch(monkeypatch):
    """可通过环境变量切换 MODEL_PROVIDER。"""
    monkeypatch.setenv("MODEL_PROVIDER", "qwen")
    from app.config import Settings

    s = Settings()
    assert s.model_provider == "qwen"


def test_settings_deepseek_config(monkeypatch):
    """应读取 DeepSeek 相关配置。"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dk-xxx")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    from app.config import Settings

    s = Settings()
    assert s.deepseek_api_key == "dk-xxx"
    assert s.deepseek_model == "deepseek-chat"


def test_settings_rag_params(monkeypatch):
    """应读取 RAG 分块与检索参数，且为整数。"""
    monkeypatch.setenv("CHUNK_SIZE", "300")
    monkeypatch.setenv("CHUNK_OVERLAP", "30")
    monkeypatch.setenv("RETRIEVE_TOP_K", "5")
    from app.config import Settings

    s = Settings()
    assert s.chunk_size == 300
    assert s.chunk_overlap == 30
    assert s.retrieve_top_k == 5
    assert isinstance(s.chunk_size, int)


def test_settings_redis_config(monkeypatch):
    """应读取 Redis 与缓存 TTL 配置。"""
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("QA_CACHE_TTL", "7200")
    from app.config import Settings

    s = Settings()
    assert s.redis_url == "redis://localhost:6379/1"
    assert s.qa_cache_ttl == 7200


def test_settings_chroma_config(monkeypatch):
    """应读取 Chroma 持久化配置。"""
    monkeypatch.setenv("CHROMA_PERSIST_DIR", "data/chroma_test")
    monkeypatch.setenv("CHROMA_COLLECTION", "my_kb")
    from app.config import Settings

    s = Settings()
    assert s.chroma_persist_dir == "data/chroma_test"
    assert s.chroma_collection == "my_kb"


def test_get_settings_cached(monkeypatch):
    """get_settings 应返回单例（同一实例）。"""
    from app.config import get_settings

    # 清除可能的 lru_cache
    get_settings.cache_clear()
    a = get_settings()
    b = get_settings()
    assert a is b
