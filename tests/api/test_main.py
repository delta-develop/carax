import os
import pytest
from fastapi.testclient import TestClient

import app.main as main_mod


@pytest.fixture
def client():
    # Ensure API key is set for auth
    os.environ["API_KEY"] = os.getenv("API_KEY", "dev-leonardo-key")
    return TestClient(main_mod.app)


def test_author_requires_auth(client):
    # no auth
    r = client.get("/author")
    assert r.status_code == 401

    # with auth
    headers = {"Authorization": f"Bearer {os.environ['API_KEY']}"}
    r = client.get("/author", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "name" in data and "project" in data


def test_chat_new_conversation_uses_service(client, monkeypatch):
    headers = {"Authorization": f"Bearer {os.environ['API_KEY']}"}

    class DummyService:
        async def start_conversation(self, msg):
            return {"conversation_id": "conv-x", "topic": "T", "stance": "S"}

    # override dependency to return our dummy
    monkeypatch.setattr(main_mod, "get_conversation_service", lambda request: DummyService())

    r = client.post("/chat", json={"message": "inicia"}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["conversation_id"] == "conv-x"


def test_chat_existing_conversation_returns_response(client, monkeypatch):
    headers = {"Authorization": f"Bearer {os.environ['API_KEY']}"}

    class DummyService:
        async def continue_conversation(self, conv_id, msg):
            return {"conversation_id": conv_id, "message": [msg]}, {"role": "assistant", "content": "ok"}

        async def persist_conversation(self, *args, **kwargs):
            return None

    monkeypatch.setattr(main_mod, "get_conversation_service", lambda request: DummyService())

    r = client.post("/chat", json={"conversation_id": "conv-1", "message": "hola"}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["conversation_id"] == "conv-1"
    assert isinstance(data.get("message"), list)

