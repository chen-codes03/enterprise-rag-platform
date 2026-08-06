"""应用配置管理。

使用 pydantic-settings 从环境变量 / .env 文件加载配置，
提供统一的全局访问入口 get_settings()（带缓存）。
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。环境变量名不区分大小写，对应字段名。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== 应用 =====
    app_name: str = "企业知识库RAG智能问答平台"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ===== 鉴权 =====
    api_key: str = "sk-rag-demo-key-change-me"

    # ===== 模型层 =====
    model_provider: str = "deepseek"  # deepseek | qwen

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # 通义千问
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # ===== Embedding =====
    embedding_provider: str = "openai"
    embedding_api_key: str = ""
    embedding_base_url: str = "https://api.deepseek.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # ===== RAG =====
    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieve_top_k: int = 4

    # ===== 向量库 =====
    chroma_persist_dir: str = "data/chroma"
    chroma_collection: str = "enterprise_kb"

    # ===== Redis 缓存 =====
    redis_url: str = "redis://localhost:6379/0"
    qa_cache_ttl: int = 3600
    embedding_cache_ttl: int = 86400


@lru_cache
def get_settings() -> Settings:
    """返回全局单例 Settings。测试中可调用 cache_clear() 重置。"""
    return Settings()
