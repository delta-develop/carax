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
from app.domain.message import MessageModel
from app.domain.llm_output import AssistantReply
from app.domain.meta import MetaModel
from app.services.llm.llm_io import LLMConversationMessage, LLMConversationRequest


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

    async def start_conversation(self, message: LLMConversationMessage) -> str:
        message.content = build_new_conversation_prompt(message.content)

        llm_request = LLMConversationRequest(messages=[message])

        raw_llm_response = await self.llm.generate_response(llm_request.messages)

        print(f"RAW LLM RESPONSE:    {raw_llm_response}")

        try:
            llm_response_dict = json.loads(raw_llm_response)
            topic_and_stance = MetaModel(**llm_response_dict)
        except Exception as e:
            raise ValueError("Topic and stance not processed.")

        conversation_id = await self.store.save(topic_and_stance.model_dump())

        await self.cache.store_in_memory(
            f"{conversation_id}:meta", topic_and_stance.model_dump()
        )

        return conversation_id

    async def continue_conversation(
        self, conversation_id: str, user_message: LLMConversationMessage
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
        print(f"Cache stored messages: {cache_stored_messages}")

        topic_and_stance = await self.cache.retrieve_from_memory(
            f"{conversation_id}:meta"
        )

        conversation_prompt_str = build_conversation_prompt(
            topic_and_stance=topic_and_stance,
            redis_stored_messages=cache_stored_messages,
            last_message=user_message.model_dump(),
        )

        conversation_prompt_obj = LLMConversationMessage(
            role="system", content=conversation_prompt_str
        )

        full_context = LLMConversationRequest(messages=[conversation_prompt_obj])

        print(f"full context: {full_context}")

        llm_response = await self.llm.generate_response(full_context.messages)

        llm_validated_response = LLMConversationMessage(
            role="assistant", content=llm_response
        )

        messages: List[Dict[str, str]] = list(cache_stored_messages or [])

        if messages and user_message.role != "system":
            messages.append(user_message.model_dump())

        messages.append(llm_validated_response.model_dump())

        response: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "message": messages[-5:],
        }

        return response, llm_validated_response

    async def persist_conversation(
        self,
        conversation_id: str,
        user_message: LLMConversationMessage,
        llm_formated_response: LLMConversationMessage,
    ) -> None:
        """Persist the latest user/bot turn into cache and durable storage.

        Args:
            conversation_id: Conversation identifier to associate with the turn.
            user_message: The user's message dict (role/content).
            llm_formated_response: The assistant's message dict (role/content).
        """
        turn_messages = [user_message, llm_formated_response]

        await self.cache.store_in_memory(
            conversation_id,
            [message.model_dump() for message in turn_messages],
        )

        data = {"conversation_id": conversation_id, "messages": turn_messages}

        await self.store.save(data)
