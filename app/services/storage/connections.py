from typing import Optional

import redis.asyncio as aioredis
from openai import AsyncOpenAI
from redis.asyncio.client import Redis

_redis_client: Optional[Redis[str]] = None
_openai_client: Optional[AsyncOpenAI] = None


async def get_redis_client(redis_url: str = "redis://redis:6379") -> Redis[str]:
    """Return a singleton async Redis client.

    Args:
        redis_url: Redis connection URL.

    Returns:
        Redis: Async Redis client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(redis_url, decode_responses=True)
    assert _redis_client is not None
    return _redis_client


async def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client configured from env vars.

    Returns:
        AsyncOpenAI: Asynchronous OpenAI client instance.
    """
    global _openai_client
    if _openai_client is None:
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        _openai_client = AsyncOpenAI(api_key=api_key)
    assert _openai_client is not None
    return _openai_client
