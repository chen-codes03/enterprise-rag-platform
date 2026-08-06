"""FastAPI 应用入口。"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from app.api.routes import chat, documents, health
from app.config import get_settings
from app.core.logging import get_logger

WEB_DIR = Path(__file__).parent / "web"

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="企业知识库 RAG 智能问答平台 API",
        version="0.1.0",
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(documents.router)

    @app.get("/")
    async def root():
        """根路径：返回可视化问答界面。"""
        return FileResponse(WEB_DIR / "index.html")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("未处理异常: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "内部服务器错误"},
        )

    logger.info("FastAPI app created: %s", settings.app_name)
    return app


app = create_app()
