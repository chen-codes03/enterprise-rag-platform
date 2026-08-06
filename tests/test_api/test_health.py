"""T5.11 + 修复 C: 健康检查测试（含 redis/chroma 依赖检查）。"""

from app.api.deps import get_redis_dep


def test_health_no_auth_required(api_client):
    r = api_client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "app" in data


def test_health_returns_dependencies(api_client):
    """健康检查应返回 redis 与 chroma 依赖状态。"""
    r = api_client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "dependencies" in data
    assert data["dependencies"]["redis"] == "ok"
    assert data["dependencies"]["chroma"] == "ok"
    assert data["status"] == "ok"


def test_health_redis_down_reports_degraded(api_client):
    """redis 不可用时，依赖状态为 error，整体状态为 degraded。"""

    class _BadRedis:
        def ping(self):
            raise Exception("connection refused")

    api_client.app.dependency_overrides[get_redis_dep] = lambda: _BadRedis()
    try:
        r = api_client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["dependencies"]["redis"] == "error"
        assert data["status"] == "degraded"
    finally:
        api_client.app.dependency_overrides.pop(get_redis_dep, None)
