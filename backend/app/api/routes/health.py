"""健康检查路由。"""
from fastapi import APIRouter, Depends

from app.api.deps import get_redis_dep, get_store
from app.config import get_settings

router = APIRouter(tags=["health"])


def _check_redis(client) -> str:
    if client is None:
        return "mem"  # 内存降级模式
    try:
        client.ping()
        return "ok"
    except Exception:
        return "error"


def _check_chroma(store) -> str:
    try:
        store.get(limit=1)
        return "ok"
    except Exception:
        return "error"


@router.get("/health")
def health(
    redis_client=Depends(get_redis_dep),
    store=Depends(get_store),
) -> dict:
    """健康检查。Redis 不可用时自动降级为内存模式，不影响主功能。"""
    settings = get_settings()
    redis_status = _check_redis(redis_client)
    deps_status = {
        "redis": redis_status,
        "chroma": _check_chroma(store),
    }
    # Redis 内存降级不算异常
    overall = "ok" if all(v in ("ok", "mem") for v in deps_status.values()) else "degraded"
    return {
        "status": overall,
        "app": settings.app_name,
        "env": settings.app_env,
        "dependencies": deps_status,
    }
