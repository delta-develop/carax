from typing import List


def format_conversation(messages: List[dict]) -> List[dict[str, str]]:
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


def message_from_user_input(text: str) -> dict[str, str]:
    """Create a normalized user message object.

    Args:
        text: User text.

    Returns:
        dict[str, str]: Message with `role=user` and stripped content.
    """
    return {"role": "user", "content": text.strip()}


def message_from_llm_output(text: str) -> dict[str, str]:
    """Create a normalized assistant message object.

    Args:
        text: LLM response text.

    Returns:
        dict[str, str]: Message with `role=assistant` and stripped content.
    """
    return {"role": "assistant", "content": text.strip()}
