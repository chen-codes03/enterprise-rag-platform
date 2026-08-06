"""FastAPI 应用入口。"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.routes import chat, documents, health
from app.config import get_settings
from app.core.logging import get_logger

ROOT_WELCOME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>企业知识库 RAG 智能问答平台</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      max-width: 720px;
      margin: 80px auto;
      padding: 40px;
      background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
      border-radius: 16px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.08);
      color: #2c3e50;
    }
    h1 { font-size: 28px; margin: 0 0 8px; color: #1a365d; }
    .subtitle { color: #5a7a9a; margin-bottom: 32px; font-size: 15px; }
    .card {
      background: #fff;
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 16px;
      border-left: 4px solid #3b82f6;
    }
    .card-title { font-weight: 600; color: #1e40af; margin-bottom: 8px; font-size: 16px; }
    .card-desc { color: #475569; font-size: 14px; margin: 0 0 12px; }
    code {
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 4px;
      color: #be185d;
      font-size: 13px;
    }
    a {
      color: #2563eb;
      text-decoration: none;
      font-weight: 500;
    }
    a:hover { text-decoration: underline; }
    .tag {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 12px;
      background: #dbeafe;
      color: #1e40af;
      font-size: 12px;
      margin-right: 6px;
    }
  </style>
</head>
<body>
  <h1>🧠 企业知识库 RAG 智能问答平台</h1>
  <p class="subtitle">基于 LangChain + FastAPI + Chroma + Redis 的 RAG 检索增强生成系统</p>

  <div class="card">
    <div class="card-title">📖 API 文档</div>
    <p class="card-desc">交互式 API 文档，可直接在浏览器中测试所有接口。</p>
    <div>
      <a href="/docs">Swagger UI 交互式文档</a>
      &nbsp;·&nbsp;
      <a href="/redoc">ReDoc 文档</a>
    </div>
  </div>

  <div class="card">
    <div class="card-title">🔍 快速测试</div>
    <p class="card-desc">在终端执行以下命令验证服务。</p>
    <code>curl http://localhost:8010/health</code><br><br>
    <code>curl -X POST http://localhost:8010/chat -H "X-API-Key: sk-rag-demo-key-change-me" -H "Content-Type: application/json" -d '{\"question\":\"报销流程是什么？\"}'</code>
  </div>

  <div class="card">
    <div class="card-title">🏷️ 技术栈</div>
    <div>
      <span class="tag">Python 3.11</span>
      <span class="tag">FastAPI</span>
      <span class="tag">LangChain</span>
      <span class="tag">Chroma</span>
      <span class="tag">Redis</span>
      <span class="tag">Docker</span>
    </div>
  </div>
</body>
</html>"""

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

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """根路径：返回欢迎页面。"""
        return ROOT_WELCOME_HTML

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
