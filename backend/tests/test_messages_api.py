import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_messages(client: AsyncClient):
    # 1. Create Session
    session_res = await client.post("/api/v1/sessions", json={"title": "PMF Q&A"})
    session_id = session_res.json()["id"]

    # 2. Add User Message
    msg1_res = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"role": "user", "content": "How did Superhuman measure PMF?"},
    )
    assert msg1_res.status_code == 201
    msg1 = msg1_res.json()
    assert msg1["role"] == "user"
    assert msg1["content"] == "How did Superhuman measure PMF?"
    assert msg1["session_id"] == session_id

    # 3. Add Assistant Message
    msg2_res = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"role": "assistant", "content": "Rahul Vohra used the 40% disappointed metric."},
    )
    assert msg2_res.status_code == 201
    msg2 = msg2_res.json()
    assert msg2["role"] == "assistant"

    # 4. List Messages
    list_res = await client.get(f"/api/v1/sessions/{session_id}/messages")
    assert list_res.status_code == 200
    messages = list_res.json()
    assert len(messages) == 2
    assert messages[0]["content"] == "How did Superhuman measure PMF?"
    assert messages[1]["content"] == "Rahul Vohra used the 40% disappointed metric."


@pytest.mark.asyncio
async def test_create_message_nonexistent_session_404(client: AsyncClient):
    fake_session_id = str(uuid.uuid4())
    res = await client.post(
        f"/api/v1/sessions/{fake_session_id}/messages",
        json={"role": "user", "content": "Hello in nonexistent session"},
    )
    assert res.status_code == 404
    error = res.json()
    assert error["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_message_empty_content_rejected(client: AsyncClient):
    session_res = await client.post("/api/v1/sessions", json={})
    session_id = session_res.json()["id"]

    # Whitespace only
    res = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"role": "user", "content": "   "},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_message_invalid_role_rejected(client: AsyncClient):
    session_res = await client.post("/api/v1/sessions", json={})
    session_id = session_res.json()["id"]

    # Invalid role
    res = await client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"role": "invalid_role", "content": "Valid text"},
    )
    assert res.status_code == 422

