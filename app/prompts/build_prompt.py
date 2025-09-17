from app.prompts.constants import CONVERSATION_PROMPT, NEW_CONVERSATION_PROMPT


def build_conversation_prompt(
    topic_and_stance, redis_stored_messages, messages_summary, last_message
):
    """Compose the prompt for an ongoing debate turn.

    Args:
        topic_and_stance: Dict with the debate topic and the bot's stance.
        redis_stored_messages: Recent short-term history (working memory).
        messages_summary: Optional long-term summary to compress context.
        last_message: Latest user message dict.

    Returns:
        str: Fully rendered prompt string for the LLM.
    """
    prompt = CONVERSATION_PROMPT.format(
        topic_and_stance=topic_and_stance,
        redis_messages=redis_stored_messages,
        summary=messages_summary,
        last_message=last_message,
    )

    return prompt


def build_new_conversation_prompt(message):
    """Compose the prompt that extracts topic and stance from the first message.

    Args:
        message: Initial user text that sets the debate.

    Returns:
        str: Prompt tailored to get a structured topic/stance response.
    """
    prompt = NEW_CONVERSATION_PROMPT.format(message=message)

    return prompt
