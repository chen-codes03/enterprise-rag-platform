"""T4.1 RED: Redis 客户端测试。"""
import redis


def test_get_redis_client_returns_redis_instance(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from app.cache.redis_client import get_redis_client

    client = get_redis_client()
    assert isinstance(client, redis.Redis)


def test_get_redis_client_custom_url():
    from app.cache.redis_client import get_redis_client

    client = get_redis_client(url="redis://localhost:6380/1")
    assert isinstance(client, redis.Redis)
