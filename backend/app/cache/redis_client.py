"""Redis 客户端封装。"""
from __future__ import annotations

import logging

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_redis_client(url: str | None = None, decode_responses: bool = True) -> redis.Redis | None:
    """构造 Redis 客户端。连接失败时返回 None，调用方可优雅降级。"""
    url = url or get_settings().redis_url
    try:
        client = redis.Redis.from_url(url, decode_responses=decode_responses)
        # 测试连接
        client.ping()
        return client
    except Exception as e:
        logger.warning("Redis 连接失败: %s，将使用内存模式", e)
        return None
