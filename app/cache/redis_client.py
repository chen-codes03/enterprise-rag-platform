"""Redis 客户端封装。"""
from __future__ import annotations

import redis

from app.config import get_settings


def get_redis_client(url: str | None = None, decode_responses: bool = True) -> redis.Redis:
    """构造 Redis 客户端。未指定 url 时取 Settings.redis_url。

    redis.Redis.from_url 为惰性连接，构造时不触发真实连接。
    """
    url = url or get_settings().redis_url
    return redis.Redis.from_url(url, decode_responses=decode_responses)
