"""应用配置管理。

使用 pydantic-settings 从环境变量 / .env 文件加载配置，
提供统一的全局访问入口 get_settings()（带缓存）。
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 演示用默认密钥（生产必须覆盖）。单独定义为常量便于统一引用与启动期检测。
DEFAULT_API_KEY = "sk-rag-demo-key-change-me"


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
    # CORS 允许的前端来源（逗号分隔，如 "http://localhost:8080,https://app.example.com"）
    cors_origins: str = "http://localhost:8080"

    # ===== 鉴权 =====
    # 演示用默认密钥；生产环境务必通过环境变量 API_KEY 覆盖为强随机值
    api_key: str = DEFAULT_API_KEY

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
    retrieve_top_k: int = 4          # 最终喂给 LLM 的文档数
    rerank_enabled: bool = True      # 是否启用 LLM 重排序
    rerank_top_n: int = 10           # 向量检索召回数（重排序候选）

    # ===== 向量库 =====
    chroma_persist_dir: str = "data/chroma"
    chroma_collection: str = "enterprise_kb"

    # ===== 原始文件持久化 =====
    # 上传的原始文件保存在此目录，供下载/在线预览使用
    uploads_dir: str = "data/uploads"

    # ===== Redis 缓存 =====
    redis_url: str = "redis://localhost:6379/0"
    qa_cache_ttl: int = 3600
    embedding_cache_ttl: int = 86400

    @property
    def is_default_api_key(self) -> bool:
        """是否仍在使用演示默认密钥（生产环境应为 False）。"""
        return self.api_key == DEFAULT_API_KEY

    @property
    def cors_origins_list(self) -> list[str]:
        """将逗号分隔的 CORS 来源字符串解析为列表。"""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """返回全局单例 Settings。测试中可调用 cache_clear() 重置。"""
    return Settings()
