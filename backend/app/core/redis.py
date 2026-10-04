"""Async Redis client lifecycle and request dependency."""

from typing import cast

from fastapi import Request
from redis.asyncio import Redis


def create_redis_client(redis_url: str) -> Redis:
    """Create a decoded async Redis client."""
    return cast(Redis, Redis.from_url(redis_url, decode_responses=True))


def get_redis(request: Request) -> Redis:
    """Return the application Redis client."""
    return cast(Redis, request.app.state.redis)
