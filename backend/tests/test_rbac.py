import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_alice_can_access_both_workspaces():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Alice headers
        headers = {"X-User-Id": "usr_alice"}
        
        # Test listing workspaces
        response = await ac.get("/api/workspaces", headers=headers)
        assert response.status_code == 200
        workspaces = response.json()
        ws_ids = [w["_id"] for w in workspaces]
        assert "ws_engineering" in ws_ids
        assert "ws_executive" in ws_ids

@pytest.mark.asyncio
async def test_bob_only_sees_engineering_workspace():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Bob headers
        headers = {"X-User-Id": "usr_bob"}
        
        response = await ac.get("/api/workspaces", headers=headers)
        assert response.status_code == 200
        workspaces = response.json()
        ws_ids = [w["_id"] for w in workspaces]
        assert "ws_engineering" in ws_ids
        assert "ws_executive" not in ws_ids

@pytest.mark.asyncio
async def test_bob_forbidden_from_executive_workspace():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_bob"}
        
        # Attempt to access restricted workspace details
        response = await ac.get("/api/workspaces/ws_executive", headers=headers)
        assert response.status_code == 403
        assert "forbidden" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_bob_forbidden_from_executive_documents_by_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_bob"}
        
        # Attempt to access confidential doc directly
        response = await ac.get("/api/workspaces/ws_executive/documents/doc_exec_01", headers=headers)
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_bob_cannot_access_alices_private_conversations():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Attempt to access Alice's conversation using Bob's credentials
        headers = {"X-User-Id": "usr_bob"}
        response = await ac.get("/api/workspaces/ws_engineering/conversations/conv_alice_demo_01", headers=headers)
        assert response.status_code in [403, 404]
