from typing import Any

from app.services.llm.base import LLMBase
from app.services.memory.memory import Memory


class SummaryMemory(Memory):
    """Longer-term summary memory for condensing debate context."""

    def __init__(self, llm: LLMBase):
        """Initialize with an LLM to create merged summaries.

        Args:
            llm: Language model used to build/update summaries.
        """
        self.storage = None
        self.llm = llm

    async def store_in_memory(self, key: str, data: Any) -> None:
        """Create and store a merged summary for the given key.

        Args:
            key: User identifier.
            data: Recent messages to merge into the existing summary.
        """
        old_summary = await self.retrieve_from_memory(key)
        # prompt = await build_summary_merge_prompt(
        #     recent_messages=data, previous_summary=old_summary or ""
        # )
        # merged_summary = await self.llm.generate_response([prompt])
        # await self.storage.save({"whatsapp_id": key, "data": merged_summary})

    async def retrieve_from_memory(self, key: str) -> Any:
        """Fetch the stored summary for a user key.

        Args:
            key: User identifier.

        Returns:
            str | None: Summary text if present.
        """
        doc = await self.storage.get({"whatsapp_id": key})
        return doc.get("summary") if doc else None

    async def delete_from_memory(self, key: str) -> None:
        """Delete the stored summary for a user key.

        Args:
            key: User identifier.
        """
        await self.storage.delete(key)
