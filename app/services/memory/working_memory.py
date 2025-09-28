import json
from app.services.memory.memory import Memory
from app.services.storage.cache_storage import CacheStorage
from typing import Any



class WorkingMemory(Memory):
    """Short-term working memory backed by the cache layer."""

    def __init__(self):
        """Initialize with a `CacheStorage` instance."""
        self.storage = CacheStorage()

    async def store_in_memory(self, key: str, data: Any) -> None:
        """Append to an existing list stored under the key.

        Args:
            key: Memory key.
            data: Data to store; must be a Python object (not pre-serialized).
        """
        if isinstance(data, str):
            raise ValueError("Data should not be a pre-serialized string.")
        existing_data = await self.retrieve_from_memory(key)
        if not isinstance(existing_data, list):
            existing_data = []
        if isinstance(data, list):
            existing_data.extend(data)
        else:
            existing_data.append(data)
        await self.storage.set(key, existing_data)

    async def retrieve_from_memory(self, key: str) -> Any:
        """Retrieve and deserialize data by key.

        Args:
            key: Memory key.

        Returns:
            Any: Python object or None.
        """
        raw = await self.storage.get(key)
        if raw is None:
            return None
        if isinstance(raw, (list, dict)):
            return raw
        return json.loads(raw)

    async def delete_from_memory(self, key: str) -> None:
        """Delete data from memory by key.

        Args:
            key: Memory key to delete.
        """
        await self.storage.delete(key)
