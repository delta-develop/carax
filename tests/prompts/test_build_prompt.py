from app.prompts.build_prompt import build_conversation_prompt, build_new_conversation_prompt


def test_build_new_conversation_prompt_includes_message_text():
    msg = "Debatamos sobre IA, tú estás en contra"
    prompt = build_new_conversation_prompt(msg)
    assert msg in prompt


def test_build_conversation_prompt_renders_all_parts():
    topic_and_stance = {"topic": "IA", "stance": "En contra"}
    redis_messages = [{"role": "user", "content": "m1"}]
    summary = {"summary": "resumen"}
    last_message = {"role": "user", "content": "último"}

    prompt = build_conversation_prompt(topic_and_stance, redis_messages, summary, last_message)

    assert "IA" in prompt
    assert "En contra" in prompt or str(topic_and_stance) in prompt
    assert "resumen" in prompt or str(summary) in prompt
    assert "último" in prompt
