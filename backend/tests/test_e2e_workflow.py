from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from app.agent.providers import FakeLLMProvider, set_llm_provider_override
from app.core.errors import ModelUnavailableException


@pytest.fixture(autouse=True)
def reset_provider():
    set_llm_provider_override(None)
    yield
    set_llm_provider_override(None)


@pytest.mark.asyncio
async def test_full_end_to_end_user_workflow(client: AsyncClient):
    """
    Simulates the complete Phase 9 product flow:
    1. Check system health and readiness.
    2. Create a new conversation session.
    3. Ask a grounded Lenny question -> verify citations and answer.
    4. Ask a context follow-up question -> verify multi-turn flow.
    5. Ask to turn previous topic into a Ship 30 for 30 article -> verify auto-routing and artifact generation.
    6. Retrieve session artifacts -> verify artifact was auto-persisted.
    7. Create a second isolated session -> verify strict session boundary isolation.
    8. Switch back to original session -> verify history and artifacts remain intact.
    """
    set_llm_provider_override(FakeLLMProvider())

    # Step 1: Check System Health
    health_res = await client.get("/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "ok"
    assert "llm_provider" in health_data

    with patch("app.api.v1.health.check_db_health", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = True
        ready_res = await client.get("/ready")
        assert ready_res.status_code == 200
        ready_data = ready_res.json()
        assert ready_data["status"] == "ready"
        assert ready_data["database"] == "connected"

    # Step 2: Create Session 1
    create_res = await client.post("/api/v1/sessions", json={"title": "PMF Strategy Session"})
    assert create_res.status_code == 201
    session_1 = create_res.json()
    session_1_id = session_1["id"]

    # Step 3: Grounded Q&A turn
    chat_1_res = await client.post(
        f"/api/v1/sessions/{session_1_id}/chat",
        json={"message": "How did Rahul Vohra measure PMF for Superhuman?"},
    )
    assert chat_1_res.status_code == 200
    chat_1 = chat_1_res.json()
    assert chat_1["intent"] == "qa"
    assert "Rahul Vohra" in chat_1["assistant_message"]["content"]
    assert len(chat_1["sources"]) > 0
    assert any("Rahul Vohra" in s["guest_name"] for s in chat_1["sources"])

    # Step 4: Multi-turn contextual follow-up
    chat_2_res = await client.post(
        f"/api/v1/sessions/{session_1_id}/chat",
        json={"message": "How does this compare to Elena Verna's B2B growth loops?"},
    )
    assert chat_2_res.status_code == 200
    chat_2 = chat_2_res.json()
    assert len(chat_2["sources"]) > 0

    # Step 5: Ship 30 for 30 Synthesis (auto-routed)
    chat_3_res = await client.post(
        f"/api/v1/sessions/{session_1_id}/chat",
        json={"message": "Turn that into a Ship 30 for 30 article."},
    )
    assert chat_3_res.status_code == 200
    chat_3 = chat_3_res.json()
    assert chat_3["intent"] == "ship30"
    assistant_msg = chat_3["assistant_message"]
    assert "Growth Engine" in assistant_msg["content"] or "Pillar" in assistant_msg["content"]
    assert assistant_msg["metadata"]["word_count"] > 500
    assert "artifact_id" in assistant_msg["metadata"]
    artifact_id = assistant_msg["metadata"]["artifact_id"]

    # Step 6: Verify artifact retrieval in Session 1
    artifacts_res = await client.get(f"/api/v1/sessions/{session_1_id}/artifacts")
    assert artifacts_res.status_code == 200
    artifacts_list = artifacts_res.json()
    assert len(artifacts_list) >= 1
    persisted_art = next((a for a in artifacts_list if a["id"] == artifact_id), None)
    assert persisted_art is not None
    assert persisted_art["artifact_type"] == "markdown"

    # Step 7: Create second session and verify session isolation
    create_2_res = await client.post("/api/v1/sessions", json={"title": "Session Two - Pricing"})
    assert create_2_res.status_code == 201
    session_2_id = create_2_res.json()["id"]

    session_2_messages_res = await client.get(f"/api/v1/sessions/{session_2_id}/messages")
    assert session_2_messages_res.status_code == 200
    assert len(session_2_messages_res.json()) == 0

    session_2_artifacts_res = await client.get(f"/api/v1/sessions/{session_2_id}/artifacts")
    assert session_2_artifacts_res.status_code == 200
    assert len(session_2_artifacts_res.json()) == 0

    # Step 8: Return to Session 1 and verify full state preservation
    session_1_messages_res = await client.get(f"/api/v1/sessions/{session_1_id}/messages")
    assert session_1_messages_res.status_code == 200
    s1_messages = session_1_messages_res.json()
    # 3 user messages + 3 assistant messages = 6 messages
    assert len(s1_messages) == 6


@pytest.mark.asyncio
async def test_end_to_end_provider_failure_and_recovery(client: AsyncClient):
    """
    Simulates failure path:
    1. Create a session.
    2. Attempt inference when provider fails with 503 Model Unavailable.
    3. Ensure user receives structured error response without leaked secrets.
    4. Ensure session remains intact and is not corrupted.
    5. Restore healthy provider.
    6. Retry message and verify successful response.
    """
    failing_provider = FakeLLMProvider(
        should_raise=ModelUnavailableException(
            "Cannot connect to Ollama daemon at http://localhost:11434. Is Ollama running?"
        )
    )
    set_llm_provider_override(failing_provider)

    # 1. Create session
    create_res = await client.post("/api/v1/sessions", json={"title": "Failure Recovery Test"})
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # 2. Send message while Ollama is down
    failed_chat = await client.post(
        f"/api/v1/sessions/{session_id}/chat",
        json={"message": "What is the Sean Ellis PMF question?"},
    )
    assert failed_chat.status_code == 503
    err = failed_chat.json()["error"]
    assert err["code"] == "MODEL_UNAVAILABLE"
    assert "Cannot connect to Ollama daemon" in err["message"]

    # 3. Session remains healthy
    session_res = await client.get(f"/api/v1/sessions/{session_id}")
    assert session_res.status_code == 200
    assert session_res.json()["title"] == "Failure Recovery Test"

    # 4. Restore provider
    set_llm_provider_override(FakeLLMProvider())

    # 5. Retry chat -> successful grounded answer
    success_chat = await client.post(
        f"/api/v1/sessions/{session_id}/chat",
        json={"message": "How did Rahul Vohra measure PMF for Superhuman?"},
    )
    assert success_chat.status_code == 200
    data = success_chat.json()
    assert data["intent"] == "qa"
    assert "Rahul Vohra" in data["assistant_message"]["content"]

