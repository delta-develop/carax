from abc import ABC, abstractmethod
from typing import Any


class Memory(ABC):
    """Abstract contract for memory backends used by the debate bot."""

    @abstractmethod
    async def store_in_memory(self, key: str, data: Any) -> None:
        """Store data under a memory key.

        Args:
            key: Memory key (e.g., conversation or user identifier).
            data: Payload to store.
        """
        raise NotImplementedError

    @abstractmethod
    async def retrieve_from_memory(self, key: str) -> Any:
        """Retrieve data by memory key.

        Args:
            key: Memory key.

        Returns:
            Any: Stored value or None.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_from_memory(self, key: str) -> None:
        """Delete data for a memory key.

        Args:
            key: Memory key.
        """
        raise NotImplementedError
