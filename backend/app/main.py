"""FastAPI 应用入口。"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, documents, health, history
from app.config import get_settings
from app.core.logging import get_logger
from app.db import init_db

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="企业知识库 RAG 智能问答平台 API",
        version="1.0.0",
    )

    # CORS 跨域支持（前后端分离模式下允许前端独立部署访问）
    # 明确指定允许的前端来源，避免 allow_origins=["*"] + allow_credentials=True
    # 这一浏览器规范明确拒绝的不安全组合。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(documents.router)
    app.include_router(history.router)

    # 初始化对话历史数据库
    init_db()

    @app.get("/")
    async def root():
        """根路径：返回服务信息（前端通过独立项目访问）。"""
        return JSONResponse(
            content={
                "message": "企业知识库 RAG 智能问答平台",
                "version": "1.0.0",
                "architecture": "前后端分离",
                "frontend": "http://localhost:8080",
                "api_docs": "/docs",
            }
        )

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
