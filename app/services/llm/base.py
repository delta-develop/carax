from abc import ABC, abstractmethod
from typing import Dict


class LLMBase(ABC):
    """Contract for LLM clients used by the debate bot."""

    @abstractmethod
    async def interpret(self, user_input: str) -> Dict[str, str]:
        """Infer intent or structure from a raw user input.

        Args:
            user_input: Raw message from the user.

        Returns:
            dict: Parsed fields (e.g., intent, entities).
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_response(self, messages: list) -> str:
        """Generate a chat response from a structured message list.

        Args:
            messages: Sequence of dicts with `role` and `content`.

        Returns:
            str: Model response text.
        """
        raise NotImplementedError
