import uuid
import pytest
from httpx import AsyncClient
from app.agent.providers import set_llm_provider_override
from app.agent.providers.fake_provider import FakeLLMProvider
from app.core.errors import ModelTimeoutException, ModelUnavailableException


@pytest.mark.asyncio
async def test_chat_api_success(client: AsyncClient):
    # 1. Create a session
    sess_res = await client.post("/api/v1/sessions", json={"title": "Chat API Test"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # 2. Configure fake provider
    fake_provider = FakeLLMProvider()
    set_llm_provider_override(fake_provider)

    try:
        # 3. Send chat message
        chat_payload = {
            "message": "How did Superhuman measure product market fit with Rahul Vohra?",
            "temperature": 0.5,
        }
        chat_res = await client.post(f"/api/v1/sessions/{session_id}/chat", json=chat_payload)
        assert chat_res.status_code == 200
        data = chat_res.json()

        assert data["session_id"] == session_id
        assert data["intent"] == "qa"
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["role"] == "assistant"
        assert len(data["sources"]) > 0
        assert any("Rahul Vohra" in s["guest_name"] for s in data["sources"])

        # Also test via /api/sessions/{session_id}/chat prefix
        chat_res2 = await client.post(f"/api/sessions/{session_id}/chat", json=chat_payload)
        assert chat_res2.status_code == 200
    finally:
        set_llm_provider_override(None)


@pytest.mark.asyncio
async def test_chat_api_nonexistent_session_404(client: AsyncClient):
    random_id = uuid.uuid4()
    res = await client.post(f"/api/v1/sessions/{random_id}/chat", json={"message": "Hello"})
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_chat_api_empty_message_422(client: AsyncClient):
    sess_res = await client.post("/api/v1/sessions", json={"title": "Empty Msg Test"})
    session_id = sess_res.json()["id"]

    # Empty string
    res = await client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": ""})
    assert res.status_code == 422

    # Whitespace string
    res_ws = await client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": "   \n  "})
    assert res_ws.status_code == 422


@pytest.mark.asyncio
async def test_chat_api_model_unavailable_503(client: AsyncClient):
    sess_res = await client.post("/api/v1/sessions", json={"title": "Error Test"})
    session_id = sess_res.json()["id"]

    set_llm_provider_override(FakeLLMProvider(should_raise=ModelUnavailableException("Ollama daemon unreachable")))
    try:
        res = await client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": "What is PLG?"})
        assert res.status_code == 503
        data = res.json()
        assert data["error"]["code"] == "MODEL_UNAVAILABLE"
        assert "Ollama daemon unreachable" in data["error"]["message"]
    finally:
        set_llm_provider_override(None)


@pytest.mark.asyncio
async def test_chat_api_model_timeout_504(client: AsyncClient):
    sess_res = await client.post("/api/v1/sessions", json={"title": "Timeout Test"})
    session_id = sess_res.json()["id"]

    set_llm_provider_override(FakeLLMProvider(should_raise=ModelTimeoutException("Inference execution timed out")))
    try:
        res = await client.post(f"/api/v1/sessions/{session_id}/chat", json={"message": "What is PLG?"})
        assert res.status_code == 504
        data = res.json()
        assert data["error"]["code"] == "MODEL_TIMEOUT"
        assert "timed out" in data["error"]["message"]
    finally:
        set_llm_provider_override(None)

