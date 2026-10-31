import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from backend.main import app
from backend.app.services.rag_service import rag_service
from backend.app.core.database import get_database

@pytest.mark.asyncio
async def test_corrupt_pdf_upload_fails_gracefully():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        # Provide corrupt PDF header and garbage bytes
        corrupt_bytes = b"%PDF-1.4\n%corrupted garbage bytes without EOF or xref\x00\xFF"
        files = {
            "file": ("corrupt_report.pdf", corrupt_bytes, "application/pdf")
        }
        data = {"title": "Corrupt Audit Report"}
        response = await ac.post("/api/workspaces/ws_engineering/documents", headers=headers, files=files, data=data)
        assert response.status_code == 201
        doc = response.json()
        assert doc["status"] == "FAILED"
        assert "pdf" in doc["error_message"].lower() or "malformed" in doc["error_message"].lower() or "corrupt" in doc["error_message"].lower()

@pytest.mark.asyncio
async def test_failed_document_not_in_retrieval_results():
    """
    Ensures failed or partially processed documents never enter ChromaDB or contaminate vector retrieval.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        # Upload a corrupt PDF
        corrupt_bytes = b"%PDF-1.4\n%invalid body"
        files = {"file": ("broken_manual.pdf", corrupt_bytes, "application/pdf")}
        res = await ac.post("/api/workspaces/ws_engineering/documents", headers=headers, files=files)
        doc = res.json()
        failed_doc_id = doc["_id"]

        # Check ChromaDB directly
        results = rag_service.search_chunks(query="broken manual", workspace_id="ws_engineering", top_k=10)
        retrieved_doc_ids = [r["document_id"] for r in results]
        assert failed_doc_id not in retrieved_doc_ids

@pytest.mark.asyncio
async def test_oversized_file_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        # Generate 16 MB dummy payload
        big_bytes = b"X" * (16 * 1024 * 1024)
        files = {
            "file": ("huge_dump.txt", big_bytes, "text/plain")
        }
        response = await ac.post("/api/workspaces/ws_engineering/documents", headers=headers, files=files)
        assert response.status_code == 400
        assert "exceeds" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_model_failure_marks_message_failed_and_does_not_finalize():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        # Create a test conversation
        create_res = await ac.post(
            "/api/workspaces/ws_engineering/conversations",
            headers=headers,
            json={"title": "Model Failure Test"}
        )
        conv_id = create_res.json()["_id"]

        # Mock AIService.generate_response to simulate an upstream LLM API outage
        with patch("backend.app.api.chats.AIService.generate_response", side_effect=RuntimeError("Simulated Upstream LLM Gateway Timeout")):
            msg_res = await ac.post(
                f"/api/workspaces/ws_engineering/conversations/{conv_id}/messages",
                headers=headers,
                json={"content": "What is the P1 SLA timeline?"}
            )
            # Must return 502 Bad Gateway
            assert msg_res.status_code == 502
            assert "model" in msg_res.json()["detail"].lower() or "timeout" in msg_res.json()["detail"].lower()

        # Reopen conversation and verify message is marked FAILED, NOT COMPLETED
        conv_res = await ac.get(f"/api/workspaces/ws_engineering/conversations/{conv_id}", headers=headers)
        conv = conv_res.json()
        assert len(conv["messages"]) == 2
        asst_msg = conv["messages"][1]
        assert asst_msg["status"] == "FAILED"
        assert asst_msg["citations"] == []
        assert "Model Failure" in asst_msg["content"]

@pytest.mark.asyncio
async def test_citation_strictly_validated_against_retrieved_chunks():
    """
    Validates that AIService._strictly_validate_citations drops hallucinated document IDs and stamps true chunk metadata.
    """
    from backend.app.services.ai_service import AIService

    valid_chunks = [
        {
            "chunk_id": "chk_eng_02_1",
            "document_id": "doc_eng_02",
            "document_title": "Incident Response Playbook & Escalation SLAs",
            "section_title": "Section 2: Escalation Timelines & On-Call SLAs",
            "page_number": 1,
            "content": "P1 Incidents: The Primary On-Call Engineer must acknowledge the alert within 15 minutes."
        }
    ]

    # Model hallucinated a fake document "doc_fake_999" and a valid document "doc_eng_02"
    raw_model_output = {
        "answer": "Here is the answer citing both valid and invented sources.",
        "is_supported": True,
        "citations": [
            {
                "document_id": "doc_eng_02",
                "chunk_id": "chk_eng_02_1",
                "snippet": "acknowledge the alert within 15 minutes"
            },
            {
                "document_id": "doc_fake_999",
                "chunk_id": "chk_fake_999_0",
                "snippet": "Invented fake snippet from fake doc"
            }
        ]
    }

    cleaned = AIService._strictly_validate_citations(raw_model_output, valid_chunks)
    # Hallucinated citation must be dropped!
    assert len(cleaned["citations"]) == 1
    cit = cleaned["citations"][0]
    assert cit["document_id"] == "doc_eng_02"
    assert cit["document_title"] == "Incident Response Playbook & Escalation SLAs"
    assert cit["page_number"] == 1
    assert "15 minutes" in cit["snippet"]
