import redis.asyncio as aioredis
from openai import AsyncOpenAI


_redis_client = None
_openai_client = None


async def get_redis_client(redis_url="redis://redis:6379"):
    """Return a singleton async Redis client.

    Args:
        redis_url: Redis connection URL.

    Returns:
        Redis: Async Redis client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(redis_url, decode_responses=True)
    return _redis_client


async def get_openai_client():
    """Return a singleton AsyncOpenAI client configured from env vars.

    Returns:
        AsyncOpenAI: Asynchronous OpenAI client instance.
    """
    global _openai_client
    if _openai_client is None:
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client
