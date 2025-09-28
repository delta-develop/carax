from typing import List, Dict
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from app.domain.message import MessageModel
from app.services.llm.llm_io import LLMConversationMessage


def domain_to_llm(msg: MessageModel) -> LLMConversationMessage:
    """Convierte un MessageModel (dominio) al payload que consume el LLM."""
    return LLMConversationMessage(role=msg.role, content=msg.content)


def llm_to_domain(
    msg: LLMConversationMessage,
    *,
    id: Optional[int] = None,
    created_at: Optional[datetime] = None,
) -> MessageModel:
    """Convierte un payload del LLM a MessageModel; permite inyectar id/created_at si ya existen."""
    return MessageModel(
        id=id,
        role=msg.role,
        content=msg.content,
        created_at=created_at or datetime.now(timezone.utc),
    )


# Helpers en lote (útiles para prompts o recuperaciones)
def many_domain_to_llm(items: Iterable[MessageModel]) -> List[LLMConversationMessage]:
    return [domain_to_llm(m) for m in items]


def many_llm_to_domain(
    items: Iterable[LLMConversationMessage],
    *,
    ids: Optional[Iterable[Optional[int]]] = None,
    created_ats: Optional[Iterable[Optional[datetime]]] = None,
) -> List[MessageModel]:
    len_items_list = len(list(items))
    ids = list(ids) if ids is not None else [None] * len_items_list
    created_ats = (
        list(created_ats) if created_ats is not None else [None] * len_items_list
    )
    # Re-iterar items con lista materializada para alinear zips
    items_list = list(items)
    return [
        llm_to_domain(m, id=i, created_at=ts)
        for m, i, ts in zip(items_list, ids, created_ats)
    ]


def format_conversation(messages: List[Dict]) -> List[Dict[str, str]]:
    """Filter and normalize a raw message list for the LLM.

    Args:
        messages: Sequence of raw message dicts.

    Returns:
        list[dict[str, str]]: Stripped messages with allowed roles only.
    """
    return [
        {"role": m["role"], "content": m["content"].strip()}
        for m in messages
        if m.get("role") in {"user", "assistant", "system"} and m.get("content")
    ]


def message_from_user_input(text: str) -> Dict[str, str]:
    """Create a normalized user message object.

    Args:
        text: User text.

    Returns:
        dict[str, str]: Message with `role=user` and stripped content.
    """
    return {"role": "user", "content": text.strip()}


def message_from_llm_output(text: str) -> Dict[str, str]:
    """Create a normalized assistant message object.

    Args:
        text: LLM response text.

    Returns:
        dict[str, str]: Message with `role=assistant` and stripped content.
    """
    return {"role": "assistant", "content": text.strip()}
