"""健康检查路由。"""
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """健康检查。"""
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
