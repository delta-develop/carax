import json
from typing import Any

from app.services.storage.connections import get_redis_client


class CacheStorage:
    """Redis-backed working memory for short-term debate context.

    Provides simple get/set/delete operations plus utilities to append user-bot
    interactions, enabling fast retrieval of the latest turns within a debate.
    """

    def __init__(self, namespace="memory"):
        """Initialize the cache wrapper.

        Args:
            namespace: Prefix applied to all Redis keys.
        """
        self.namespace = namespace

    async def _get_redis(self):
        """Get a Redis client connection (singleton)."""
        return await get_redis_client()

    def _make_key(self, key: str) -> str:
        """Build a namespaced Redis key.

        Args:
            key: Base key.

        Returns:
            str: Namespaced key.
        """
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Any:
        """Fetch and deserialize a value by key.

        Args:
            key: Cache key to retrieve.

        Returns:
            Any | None: Deserialized value or None if missing.
        """
        redis = await self._get_redis()
        data = await redis.get(self._make_key(key))
        if data is not None:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return None

    async def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """Serialize and store a value, optionally with TTL.

        Args:
            key: Cache key.
            value: Value to serialize and store.
            ttl: Expiration in seconds; 0 disables expiration.
        """
        redis = await self._get_redis()
        data = json.dumps(value)
        namespaced_key = self._make_key(key)
        if ttl > 0:
            await redis.set(namespaced_key, data, ex=ttl)
        else:
            await redis.set(namespaced_key, data)

    async def delete(self, key: str) -> None:
        """Remove a key from Redis.

        Args:
            key: Key to delete.
        """
        redis = await self._get_redis()
        await redis.delete(self._make_key(key))

    async def append_interaction(
        self, key: str, user_msg: str, assistant_msg: str
    ) -> None:
        """Append a user/assistant turn to the conversation list.

        Args:
            key: Conversation key.
            user_msg: User message text.
            assistant_msg: Assistant reply text.
        """
        await self._get_redis()
        current = await self.get(key) or []
        current.append({"role": "user", "content": user_msg})
        current.append({"role": "assistant", "content": assistant_msg})
        await self.set(key, current)

    async def get_raw(self, key: str) -> str:
        """Retrieve the unparsed Redis value for a key.

        Args:
            key: Cache key.

        Returns:
            str: Raw stored value.
        """
        redis = await self._get_redis()
        return await redis.get(self._make_key(key))
