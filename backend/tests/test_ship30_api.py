import uuid
import pytest
from httpx import AsyncClient
from app.agent.providers import set_llm_provider_override
from app.agent.providers.fake_provider import FakeLLMProvider
from app.core.errors import ModelTimeoutException, ModelUnavailableException


@pytest.mark.asyncio
async def test_ship30_api_dedicated_endpoint_success(client: AsyncClient):
    # 1. Create a session
    sess_res = await client.post("/api/v1/sessions", json={"title": "Ship 30 API Session"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    fake_provider = FakeLLMProvider()
    set_llm_provider_override(fake_provider)

    try:
        # 2. Call dedicated POST /sessions/{session_id}/ship30 endpoint
        payload = {
            "topic": "How did Superhuman measure product market fit with Rahul Vohra?",
            "audience": "Seed Founders",
            "angle": "Quantitative PMF engine vs gut feeling",
            "tone": "Direct and actionable",
        }
        res = await client.post(f"/api/v1/sessions/{session_id}/ship30", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["session_id"] == session_id
        assert data["title"]
        assert len(data["content"]) > 500
        assert data["word_count"] >= 1000
        assert len(data["sources"]) > 0
        assert any("Rahul Vohra" in s["guest_name"] for s in data["sources"])
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["role"] == "assistant"
        assert data["metadata"]["skill"] == "ship30"

        # Also test via /api/sessions/{session_id}/ship30 alias
        res2 = await client.post(f"/api/sessions/{session_id}/ship30", json=payload)
        assert res2.status_code == 200
    finally:
        set_llm_provider_override(None)


@pytest.mark.asyncio
async def test_chat_api_auto_routes_to_ship30_skill(client: AsyncClient):
    sess_res = await client.post("/api/v1/sessions", json={"title": "Chat Routing Test"})
    session_id = sess_res.json()["id"]

    fake_provider = FakeLLMProvider()
    set_llm_provider_override(fake_provider)

    try:
        chat_payload = {
            "message": "Write a Ship 30 for 30 essay about Superhuman product market fit with Rahul Vohra",
        }
        res = await client.post(f"/api/v1/sessions/{session_id}/chat", json=chat_payload)
        assert res.status_code == 200
        data = res.json()

        assert data["intent"] == "ship30"
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["role"] == "assistant"
        assert len(data["sources"]) > 0
        assert any("Rahul Vohra" in s["guest_name"] for s in data["sources"])
        assert "Growth Engine" in data["assistant_message"]["content"] or "Pillar" in data["assistant_message"]["content"]
    finally:
        set_llm_provider_override(None)


@pytest.mark.asyncio
async def test_ship30_api_nonexistent_session_404(client: AsyncClient):
    random_id = uuid.uuid4()
    res = await client.post(f"/api/v1/sessions/{random_id}/ship30", json={"topic": "PLG"})
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_ship30_api_model_unavailable_503(client: AsyncClient):
    sess_res = await client.post("/api/v1/sessions", json={"title": "Error Test"})
    session_id = sess_res.json()["id"]

    set_llm_provider_override(FakeLLMProvider(should_raise=ModelUnavailableException("Ollama daemon is down")))
    try:
        res = await client.post(f"/api/v1/sessions/{session_id}/ship30", json={"topic": "Superhuman PMF"})
        assert res.status_code == 503
        data = res.json()
        assert data["error"]["code"] == "MODEL_UNAVAILABLE"
    finally:
        set_llm_provider_override(None)


@pytest.mark.asyncio
async def test_ship30_api_model_timeout_504(client: AsyncClient):
    sess_res = await client.post("/api/v1/sessions", json={"title": "Timeout Test"})
    session_id = sess_res.json()["id"]

    set_llm_provider_override(FakeLLMProvider(should_raise=ModelTimeoutException("Essay generation timed out")))
    try:
        res = await client.post(f"/api/v1/sessions/{session_id}/ship30", json={"topic": "Superhuman PMF"})
        assert res.status_code == 504
        data = res.json()
        assert data["error"]["code"] == "MODEL_TIMEOUT"
    finally:
        set_llm_provider_override(None)

