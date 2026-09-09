import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_artifact_crud_flow(client: AsyncClient):
    # 1. Create a session
    sess_res = await client.post("/api/v1/sessions", json={"title": "Artifact Session"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # 2. Create an artifact in the session
    artifact_payload = {
        "session_id": session_id,
        "title": "Superhuman PMF Engine Framework",
        "artifact_type": "markdown",
        "content": "# Superhuman PMF Engine\n\n- The 40% disappointed rule\n- Segmentation analysis",
        "version": 1,
        "metadata": {"skill": "ship30", "word_count": 120},
    }
    create_res = await client.post(f"/api/v1/sessions/{session_id}/artifacts", json=artifact_payload)
    assert create_res.status_code == 201
    art_data = create_res.json()

    assert art_data["session_id"] == session_id
    assert art_data["title"] == "Superhuman PMF Engine Framework"
    assert art_data["artifact_type"] == "markdown"
    assert art_data["version"] == 1
    artifact_id = art_data["id"]

    # 3. Retrieve artifact by ID
    get_res = await client.get(f"/api/v1/artifacts/{artifact_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == artifact_id
    assert get_res.json()["content"] == artifact_payload["content"]

    # 4. List artifacts for session
    list_res = await client.get(f"/api/v1/sessions/{session_id}/artifacts")
    assert list_res.status_code == 200
    artifacts_list = list_res.json()
    assert len(artifacts_list) == 1
    assert artifacts_list[0]["id"] == artifact_id

    # Also list via /api/v1/artifacts/session/{session_id}
    list_res2 = await client.get(f"/api/v1/artifacts/session/{session_id}")
    assert list_res2.status_code == 200
    assert len(list_res2.json()) == 1

    # 5. Delete artifact
    del_res = await client.delete(f"/api/v1/artifacts/{artifact_id}")
    assert del_res.status_code == 204

    # 6. Verify deleted artifact returns 404
    get_del_res = await client.get(f"/api/v1/artifacts/{artifact_id}")
    assert get_del_res.status_code == 404


@pytest.mark.asyncio
async def test_artifact_session_isolation(client: AsyncClient):
    # Create Session A and Session B
    res_a = await client.post("/api/v1/sessions", json={"title": "Session A"})
    session_a = res_a.json()["id"]

    res_b = await client.post("/api/v1/sessions", json={"title": "Session B"})
    session_b = res_b.json()["id"]

    # Create artifact in Session A
    await client.post(
        f"/api/v1/sessions/{session_a}/artifacts",
        json={
            "session_id": session_a,
            "title": "Artifact for A",
            "artifact_type": "markdown",
            "content": "# Secret A",
        },
    )

    # Verify Session B list is empty
    list_b = await client.get(f"/api/v1/sessions/{session_b}/artifacts")
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0


@pytest.mark.asyncio
async def test_artifact_nonexistent_session_404(client: AsyncClient):
    random_id = uuid.uuid4()
    res = await client.post(
        f"/api/v1/sessions/{random_id}/artifacts",
        json={
            "session_id": str(random_id),
            "title": "Test",
            "artifact_type": "markdown",
            "content": "test",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_artifact_invalid_type_rejected(client: AsyncClient):
    sess_res = await client.post("/api/v1/sessions", json={"title": "Validation Test"})
    session_id = sess_res.json()["id"]

    res = await client.post(
        f"/api/v1/sessions/{session_id}/artifacts",
        json={
            "session_id": session_id,
            "title": "Invalid Type",
            "artifact_type": "executable_binary",
            "content": "binary content",
        },
    )
    assert res.status_code == 422

