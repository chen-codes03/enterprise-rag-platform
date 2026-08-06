"""健康检查路由。

检查应用及关键依赖（Redis、Chroma 向量库）的连通性，返回结构化状态。
"""
from fastapi import APIRouter, Depends

from app.api.deps import get_redis_dep, get_store
from app.config import get_settings

router = APIRouter(tags=["health"])


def _check_redis(client) -> str:
    try:
        client.ping()
        return "ok"
    except Exception:
        return "error"


def _check_chroma(store) -> str:
    try:
        # get 不需要 embedding，轻量探测向量库可用性
        store.get(limit=1)
        return "ok"
    except Exception:
        return "error"


@router.get("/health")
def health(
    redis_client=Depends(get_redis_dep),
    store=Depends(get_store),
) -> dict:
    """健康检查：返回应用状态与 redis/chroma 依赖状态。"""
    settings = get_settings()
    deps_status = {
        "redis": _check_redis(redis_client),
        "chroma": _check_chroma(store),
    }
    overall = "ok" if all(v == "ok" for v in deps_status.values()) else "degraded"
    return {
        "status": overall,
        "app": settings.app_name,
        "env": settings.app_env,
        "dependencies": deps_status,
    }
