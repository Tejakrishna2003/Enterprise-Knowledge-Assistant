import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_list_documents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        response = await ac.get("/api/workspaces/ws_engineering/documents", headers=headers)
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) >= 3
        titles = [d["title"] for d in docs]
        assert any("Incident Response" in t for t in titles)

@pytest.mark.asyncio
async def test_upload_valid_document():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        files = {
            "file": ("test_guide.txt", b"# Guide\nThis is a test guide content for automated testing.\n", "text/plain")
        }
        data = {"title": "Automated Test Guide"}
        response = await ac.post("/api/workspaces/ws_engineering/documents", headers=headers, files=files, data=data)
        assert response.status_code == 201
        doc = response.json()
        assert doc["status"] == "INDEXED"
        assert doc["title"] == "Automated Test Guide"
        assert doc["chunk_count"] >= 1

@pytest.mark.asyncio
async def test_upload_invalid_file_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        files = {
            "file": ("malicious.exe", b"\x4D\x5A\x90\x00", "application/x-msdownload")
        }
        response = await ac.post("/api/workspaces/ws_engineering/documents", headers=headers, files=files)
        assert response.status_code == 400
        assert "unsupported" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_upload_empty_file_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        files = {
            "file": ("empty_notes.txt", b"", "text/plain")
        }
        response = await ac.post("/api/workspaces/ws_engineering/documents", headers=headers, files=files)
        assert response.status_code == 201
        doc = response.json()
        assert doc["status"] == "FAILED"
        assert "empty" in doc["error_message"].lower()

@pytest.mark.asyncio
async def test_get_document_preview():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-Id": "usr_alice"}
        response = await ac.get("/api/workspaces/ws_engineering/documents/doc_eng_01", headers=headers)
        assert response.status_code == 200
        doc = response.json()
        assert doc["_id"] == "doc_eng_01"
        assert len(doc["raw_content"]) > 50
        assert len(doc["chunks"]) > 0
