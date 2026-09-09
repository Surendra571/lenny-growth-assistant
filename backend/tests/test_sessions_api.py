import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    # 1. Create with default title
    res = await client.post("/api/v1/sessions", json={})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "New Conversation"
    assert "id" in data
    assert "created_at" in data

    # 2. Create with custom title and metadata
    res2 = await client.post(
        "/api/v1/sessions",
        json={"title": "Pricing Discussion", "metadata": {"source": "web_ui"}},
    )
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["title"] == "Pricing Discussion"
    assert data2["metadata"]["source"] == "web_ui"


@pytest.mark.asyncio
async def test_get_session_by_id(client: AsyncClient):
    create_res = await client.post("/api/v1/sessions", json={"title": "Retention Curves"})
    session_id = create_res.json()["id"]

    res = await client.get(f"/api/v1/sessions/{session_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == session_id
    assert data["title"] == "Retention Curves"
    assert "messages" in data
    assert "artifacts" in data


@pytest.mark.asyncio
async def test_list_sessions_pagination(client: AsyncClient):
    for i in range(5):
        await client.post("/api/v1/sessions", json={"title": f"Session {i}"})

    # List with limit 3
    res = await client.get("/api/v1/sessions?limit=3&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3

    # List next page
    res_page2 = await client.get("/api/v1/sessions?limit=3&offset=3")
    assert res_page2.status_code == 200
    data_page2 = res_page2.json()
    assert len(data_page2) >= 2


@pytest.mark.asyncio
async def test_update_session_patch(client: AsyncClient):
    create_res = await client.post("/api/v1/sessions", json={"title": "Original Title"})
    session_id = create_res.json()["id"]

    # Patch title and metadata
    patch_res = await client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"title": "Updated Title", "metadata": {"status": "archived"}},
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["title"] == "Updated Title"
    assert updated_data["metadata"]["status"] == "archived"


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient):
    create_res = await client.post("/api/v1/sessions", json={"title": "Temporary Session"})
    session_id = create_res.json()["id"]

    # Delete
    del_res = await client.delete(f"/api/v1/sessions/{session_id}")
    assert del_res.status_code == 204

    # Subsequent GET returns 404
    get_res = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_res.status_code == 404
    error_payload = get_res.json()
    assert error_payload["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_nonexistent_session_404(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    res = await client.get(f"/api/v1/sessions/{fake_id}")
    assert res.status_code == 404
    error_payload = res.json()
    assert error_payload["error"]["code"] == "RESOURCE_NOT_FOUND"

