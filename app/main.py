"""FastAPI 应用入口。

完整路由在 P5 阶段挂载；当前提供最小可用 app 对象便于导入与健康检查骨架。
"""
from fastapi import FastAPI

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="企业知识库 RAG 智能问答平台 API",
        version="0.1.0",
    )

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name, "env": settings.app_env}

    logger.info("FastAPI app created: %s", settings.app_name)
    return app


app = create_app()
