from app.prompts.constants import CONVERSATION_PROMPT, NEW_CONVERSATION_PROMPT


def build_conversation_prompt(
    topic_and_stance, redis_stored_messages, messages_summary, last_message
):
    prompt = CONVERSATION_PROMPT.format(
        topic_and_stance=topic_and_stance,
        redis_messages=redis_stored_messages,
        summary=messages_summary,
        last_message=last_message,
    )

    return prompt


def build_new_conversation_prompt(message):
    prompt = NEW_CONVERSATION_PROMPT.format(message=message)

    return prompt
