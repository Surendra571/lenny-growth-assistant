import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_session_isolation_guarantee(client: AsyncClient):
    """
    Verify that messages belonging to Session A never leak into Session B,
    and deleting Session A leaves Session B completely intact.
    """
    # 1. Create Session A and Session B
    session_a_res = await client.post("/api/v1/sessions", json={"title": "Session A"})
    session_a_id = session_a_res.json()["id"]

    session_b_res = await client.post("/api/v1/sessions", json={"title": "Session B"})
    session_b_id = session_b_res.json()["id"]

    # 2. Add Messages to Session A
    await client.post(
        f"/api/v1/sessions/{session_a_id}/messages",
        json={"role": "user", "content": "Message A1 - PMF Inquiry"},
    )
    await client.post(
        f"/api/v1/sessions/{session_a_id}/messages",
        json={"role": "assistant", "content": "Message A2 - PMF Answer"},
    )

    # 3. Add Messages to Session B
    await client.post(
        f"/api/v1/sessions/{session_b_id}/messages",
        json={"role": "user", "content": "Message B1 - Pricing Inquiry"},
    )

    # 4. Fetch Session A Messages -> Strictly contains A1 and A2
    res_a = await client.get(f"/api/v1/sessions/{session_a_id}/messages")
    assert res_a.status_code == 200
    msgs_a = res_a.json()
    assert len(msgs_a) == 2
    assert msgs_a[0]["content"] == "Message A1 - PMF Inquiry"
    assert msgs_a[1]["content"] == "Message A2 - PMF Answer"
    assert not any("Message B1" in m["content"] for m in msgs_a)

    # 5. Fetch Session B Messages -> Strictly contains B1
    res_b = await client.get(f"/api/v1/sessions/{session_b_id}/messages")
    assert res_b.status_code == 200
    msgs_b = res_b.json()
    assert len(msgs_b) == 1
    assert msgs_b[0]["content"] == "Message B1 - Pricing Inquiry"
    assert not any("Message A" in m["content"] for m in msgs_b)

    # 6. Delete Session A -> Session B remains completely intact
    del_res = await client.delete(f"/api/v1/sessions/{session_a_id}")
    assert del_res.status_code == 204

    # Verify Session A is deleted
    assert (await client.get(f"/api/v1/sessions/{session_a_id}")).status_code == 404

    # Verify Session B still has its message
    res_b_after = await client.get(f"/api/v1/sessions/{session_b_id}/messages")
    assert res_b_after.status_code == 200
    assert len(res_b_after.json()) == 1
    assert res_b_after.json()[0]["content"] == "Message B1 - Pricing Inquiry"

