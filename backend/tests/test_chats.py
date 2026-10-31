import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_reopen_seeded_conversation_and_citations():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        response = await ac.get("/api/workspaces/ws_engineering/conversations/conv_alice_demo_01", headers=headers)
        assert response.status_code == 200
        conv = response.json()
        assert conv["_id"] == "conv_alice_demo_01"
        assert len(conv["messages"]) >= 2
        
        # Check citations on assistant message
        asst_msg = next(m for m in conv["messages"] if m["sender"] == "assistant")
        assert len(asst_msg["citations"]) >= 2
        titles = [c["document_title"] for c in asst_msg["citations"]]
        assert any("Incident Response" in t for t in titles)
        assert any("Deployment" in t for t in titles)

@pytest.mark.asyncio
async def test_multi_document_rag_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        
        # Create conversation
        create_res = await ac.post(
            "/api/workspaces/ws_engineering/conversations",
            headers=headers,
            json={"title": "Multi-Doc Test"}
        )
        assert create_res.status_code == 201
        conv_id = create_res.json()["_id"]

        # Send multi-document question
        query = "When a P1 incident occurs during a deployment, what is the escalation timeline and how does the rollback policy interact with the load balancer?"
        msg_res = await ac.post(
            f"/api/workspaces/ws_engineering/conversations/{conv_id}/messages",
            headers=headers,
            json={"content": query}
        )
        assert msg_res.status_code == 200
        msg = msg_res.json()
        assert msg["status"] == "COMPLETED"
        assert len(msg["citations"]) >= 2
        assert "15 minutes" in msg["content"] or "Incident Commander" in msg["content"]

@pytest.mark.asyncio
async def test_unsupported_question_handles_missing_evidence():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        
        # Create conversation
        create_res = await ac.post(
            "/api/workspaces/ws_engineering/conversations",
            headers=headers,
            json={"title": "Unsupported Test"}
        )
        conv_id = create_res.json()["_id"]

        # Ask unsupported question
        query = "What is our company's refund policy for enterprise customer subscription cancellations in Germany?"
        msg_res = await ac.post(
            f"/api/workspaces/ws_engineering/conversations/{conv_id}/messages",
            headers=headers,
            json={"content": query}
        )
        assert msg_res.status_code == 200
        msg = msg_res.json()
        assert msg["status"] == "COMPLETED"
        # Must indicate missing evidence
        content_lower = msg["content"].lower()
        assert any(phrase in content_lower for phrase in ["do not contain", "missing", "absent", "not found"])
