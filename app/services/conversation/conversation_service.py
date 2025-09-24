from typing import Any, Dict, List, Optional, Tuple

from app.prompts.build_prompt import (
    build_conversation_prompt,
    build_new_conversation_prompt,
)

import json

from app.utils.message_adapter import (
    format_conversation,
    message_from_user_input,
    message_from_llm_output,
)
from app.services.llm.base import LLMBase
from app.services.storage.base import Storage
from app.services.memory.memory import Memory


class ConversationService:
    """Coordinates debate conversations between the user and the bot.

    This service encapsulates the debate workflow: starting a new conversation,
    continuing an existing one with coherent argumentative context, and
    persisting the interaction into long and short term storage.

    Attributes:
        llm: Large language model client used to generate persuasive responses.
        store: Persistent storage for conversation metadata and summaries.
        cache: Ephemeral storage for recent message history per conversation.
    """

    def __init__(self, *, llm: LLMBase, store: Storage, cache: Memory) -> None:
        """Initialize the conversation service.

        Args:
            llm: LLM client implementing `generate_response`.
            store: Storage backend with `save` and `get` for persistence.
            cache: Working-memory backend with `store_in_memory` and `retrieve_from_memory`.
        """
        self.llm = llm
        self.store = store
        self.cache = cache

    async def start_conversation(self, user_message: Dict[str, str]) -> Dict[str, str]:
        """Start a new debate given the user's first message.

        The first message defines the topic and the stance the bot must adopt.
        This method delegates to the prompt builder to extract that structure,
        stores metadata, and returns an identifier for subsequent turns.

        Args:
            user_message: Normalized message dict from the user to initialize the debate.

        Returns:
            dict: A dictionary with keys `conversation_id`, `topic`, and `stance`.
        """
        new_conversation_prompt = build_new_conversation_prompt(user_message["content"])
        llm_response = await self.llm.generate_response(
            [{"role": "user", "content": new_conversation_prompt}]
        )
        llm_response_dict: Dict[str, str] = json.loads(llm_response)
        topic_and_stance: Dict[str, str] = {
            "topic": llm_response_dict["topic"],
            "stance": llm_response_dict["stance"],
        }
        conversation_id = await self.store.save(topic_and_stance)

        await self.cache.store_in_memory(f"{conversation_id}:meta", topic_and_stance)

        return conversation_id

    async def continue_conversation(
        self, conversation_id: str, user_message: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Continue an ongoing debate with the latest user message.

        It composes a debate prompt from topic/stance, short-term history, and
        any available summary, then asks the LLM for the next persuasive reply.

        Args:
            conversation_id: Identifier of the existing conversation.
            user_message: The latest message from the user.

        Returns:
            Tuple[dict, dict]:
                - Response envelope with `conversation_id` and the last 5 messages.
                - The assistant message as a message dict for downstream persistence.
        """
        cache_stored_messages = await self.cache.retrieve_from_memory(conversation_id)
        topic_and_stance = await self.cache.retrieve_from_memory(
            f"{conversation_id}:meta"
        )
        messages_summary = await self.store.get(
            filters={"id": conversation_id, "table": "summary"}
        )

        conversation_prompt = build_conversation_prompt(
            topic_and_stance, cache_stored_messages, messages_summary, user_message
        )

        llm_response = await self.llm.generate_response(
            [{"role": "user", "content": conversation_prompt}]
        )

        llm_formated_response = message_from_llm_output(llm_response)

        messages: List[Dict[str, str]] = list(cache_stored_messages or [])
        messages.append(user_message)
        messages.append(llm_formated_response)

        response: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "message": messages[-5:],
        }

        return response, llm_formated_response

    async def persist_conversation(
        self,
        conversation_id: str,
        user_message: Dict[str, str],
        llm_formated_response: Dict[str, str],
    ) -> None:
        """Persist the latest user/bot turn into cache and durable storage.

        Args:
            conversation_id: Conversation identifier to associate with the turn.
            user_message: The user's message dict (role/content).
            llm_formated_response: The assistant's message dict (role/content).
        """
        data: Dict[str, Any] = {
            "user_message": user_message,
            "bot_message": llm_formated_response,
        }

        await self.cache.store_in_memory(conversation_id, data)

        data["conversation_id"] = conversation_id

        await self.store.save(data)
