import json
import pytest
from unittest.mock import AsyncMock

from app.services.conversation.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_start_conversation_creates_topic_and_stance(monkeypatch):
    # Arrange
    mock_llm = AsyncMock()
    mock_llm.generate_response.return_value = json.dumps({
        "topic": "Cambio climático",
        "stance": "El cambio climático no es real"
    })

    mock_store = AsyncMock()
    mock_store.save.return_value = "conv-123"

    mock_cache = AsyncMock()

    service = ConversationService(llm=mock_llm, store=mock_store, cache=mock_cache)

    # Act
    result = await service.start_conversation({"role": "user", "content": "Debatamos sobre clima, tú niegas su existencia"})

    # Assert
    assert result["conversation_id"] == "conv-123"
    assert result["topic"] == "Cambio climático"
    assert result["stance"] == "El cambio climático no es real"
    mock_cache.store_in_memory.assert_awaited_once_with("conv-123:meta", {
        "topic": "Cambio climático",
        "stance": "El cambio climático no es real",
    })


@pytest.mark.asyncio
async def test_continue_conversation_builds_prompt_and_limits_history(monkeypatch):
    # Arrange
    mock_llm = AsyncMock()
    mock_llm.generate_response.return_value = "Respuesta persuasiva"

    mock_store = AsyncMock()
    mock_store.get.return_value = {"summary": "resumen previo"}

    mock_cache = AsyncMock()
    # simulate existing messages
    existing = [{"role": "user", "content": f"m{i}"} for i in range(6)]
    mock_cache.retrieve_from_memory.side_effect = [
        existing,  # history
        {"topic": "X", "stance": "Y"},  # meta
    ]

    service = ConversationService(llm=mock_llm, store=mock_store, cache=mock_cache)

    user_message = {"role": "user", "content": "nuevo argumento"}
    response, llm_msg = await service.continue_conversation("conv-1", user_message)

    # Assert
    assert response["conversation_id"] == "conv-1"
    # last 5 messages only
    assert len(response["message"]) == 5
    assert llm_msg["role"] == "assistant"
    assert isinstance(llm_msg["content"], str)


@pytest.mark.asyncio
async def test_persist_conversation_stores_cache_and_db():
    mock_llm = AsyncMock()
    mock_store = AsyncMock()
    mock_cache = AsyncMock()

    service = ConversationService(llm=mock_llm, store=mock_store, cache=mock_cache)

    user_message = {"role": "user", "content": "hola"}
    bot_message = {"role": "assistant", "content": "respuesta"}

    await service.persist_conversation("conv-9", user_message, bot_message)

    mock_cache.store_in_memory.assert_awaited_once()
    mock_store.save.assert_awaited_once()

