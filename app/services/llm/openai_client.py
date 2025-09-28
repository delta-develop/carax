import os
from typing import Any, Dict, List, Optional

from app.services.llm.base import LLMBase
from app.services.storage.connections import get_openai_client
from openai import AsyncOpenAI


class OpenAIClient(LLMBase):
    """Async OpenAI client implementing the LLMBase interface.

    Generates chat completions for debate turns and offers a minimal
    interpretation fallback for structured prompts.
    """

    def __init__(self) -> None:
        """Initialize model and temperature from environment variables."""
        self.model = os.getenv("OPENAI_MODEL")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.7))
        self.client: Optional[AsyncOpenAI] = None

    async def get_client(self) -> AsyncOpenAI:
        """Lazily initialize and return the OpenAI client instance."""
        if self.client is None:
            self.client = await get_openai_client()
        return self.client

    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a response using the configured chat model.

        Args:
            messages: Conversation history for the model.

        Returns:
            str: Trimmed model response text.
        """
        if not self.client:
            self.client = await self.get_client()
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
        )
        return response.choices[0].message.content.strip()

    async def interpret(self, user_input: str) -> Dict[str, Any]:
        """Return a trivial interpretation payload for raw input.

        Args:
            user_input: Raw user text.

        Returns:
            dict: Minimal structure with default intent and echo of input.
        """
        return {"intent": "default", "message": user_input}
