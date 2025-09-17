from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Storage(ABC):
    """Abstract contract for durable storage backends.

    Supports async operations to persist conversation artifacts needed by the
    debate bot (topics, stances, messages, summaries).
    """

    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> None:
        """Persist a single record.

        Args:
            data: The record payload to store.
        """
        raise NotImplementedError

    @abstractmethod
    async def get(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve records filtered by the provided criteria.

        Args:
            filters: Key-value pairs defining the query.

        Returns:
            List[Dict[str, Any]]: Matching records.
        """
        raise NotImplementedError

    @abstractmethod
    async def bulk_load(self, data: Dict) -> List[Dict[str, Any]]:
        """Insert multiple records efficiently.

        Args:
            data: Container with the records to insert.

        Returns:
            List[Dict[str, Any]]: Inserted records or their identifiers.
        """
        raise NotImplementedError

    @abstractmethod
    async def setup(self) -> None:
        """Initialize storage structures (tables, indices)."""
        raise NotImplementedError
