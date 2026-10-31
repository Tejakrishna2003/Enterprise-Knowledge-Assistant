import os
import uuid
import logging
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
import aiofiles

from backend.app.core.config import settings
from backend.app.core.database import get_database
from backend.app.models.document import DocumentResponse, DocumentDetailResponse
from backend.app.api.deps import verify_workspace_access
from backend.app.services.document_service import DocumentService, DocumentProcessingError
from backend.app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["Documents"])

@router.get("", response_model=List[DocumentResponse])
async def list_documents(workspace_id: str = Depends(verify_workspace_access)):
    db = get_database()
    docs = await db.documents.find({"workspace_id": workspace_id}).sort("created_at", -1).to_list(100)
    return [DocumentResponse(**d) for d in docs]

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: str = Depends(verify_workspace_access),
    file: UploadFile = File(...),
    title: str = Form(None)
):
    db = get_database()
    filename = file.filename or "uploaded_file"
    doc_title = title.strip() if title and title.strip() else filename

    # 1. Validate file extension
    valid_exts = [".txt", ".pdf", ".md"]
    has_valid_ext = any(filename.lower().endswith(ext) for ext in valid_exts)
    if not has_valid_ext and file.content_type not in ["text/plain", "application/pdf", "text/markdown"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a declared text-based format: .txt, .md, or text-based .pdf."
        )

    # 2. Read bytes and enforce size limits
    content_bytes = await file.read()
    file_size = len(content_bytes)

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    doc_id = f"doc_{uuid.uuid4().hex[:10]}"
    file_path = os.path.join(settings.DOCUMENTS_DIR, f"{doc_id}_{filename}")

    # Handle 0-byte empty file
    if file_size == 0:
        doc_record = {
            "_id": doc_id,
            "workspace_id": workspace_id,
            "title": doc_title,
            "filename": filename,
            "file_path": None,
            "file_type": file.content_type or "text/plain",
            "file_size": 0,
            "status": "FAILED",
            "error_message": "Uploaded file is empty (0 bytes).",
            "chunk_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.documents.insert_one(doc_record)
        return DocumentResponse(**doc_record)

    # 3. Preserve original file to disk
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content_bytes)

    # 4. Create initial PENDING record
    doc_record = {
        "_id": doc_id,
        "workspace_id": workspace_id,
        "title": doc_title,
        "filename": filename,
        "file_path": file_path,
        "file_type": file.content_type or ("application/pdf" if filename.endswith(".pdf") else "text/plain"),
        "file_size": file_size,
        "status": "PROCESSING",
        "error_message": None,
        "chunk_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await db.documents.insert_one(doc_record)

    # 5. Extract, chunk, and index
    try:
        extracted_text = DocumentService.extract_text(file_path, doc_record["file_type"])
        chunks = DocumentService.chunk_document(extracted_text, doc_id, workspace_id)

        if not chunks:
            raise DocumentProcessingError("No semantic chunks could be created from document.")

        # Insert chunks to MongoDB
        await db.document_chunks.insert_many(chunks)

        # Index chunks to ChromaDB ONLY once processing succeeds
        rag_service.index_chunks(chunks, doc_record)

        # Transition status to INDEXED
        await db.documents.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "status": "INDEXED",
                    "chunk_count": len(chunks),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        doc_record["status"] = "INDEXED"
        doc_record["chunk_count"] = len(chunks)

    except Exception as proc_err:
        logger.error(f"Document processing failed for {doc_id}: {proc_err}")
        clean_error = str(proc_err) if isinstance(proc_err, DocumentProcessingError) else "Failed to parse document content."
        
        # Cleanup any partial chunks so failed document is NEVER searchable
        await db.document_chunks.delete_many({"document_id": doc_id})
        rag_service.delete_document_chunks(doc_id)

        await db.documents.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "status": "FAILED",
                    "error_message": clean_error,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        doc_record["status"] = "FAILED"
        doc_record["error_message"] = clean_error

    return DocumentResponse(**doc_record)

@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    workspace_id: str = Depends(verify_workspace_access)
):
    db = get_database()
    doc = await db.documents.find_one({"_id": document_id, "workspace_id": workspace_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found in workspace '{workspace_id}'."
        )

    # Read extracted content if available
    raw_content = ""
    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            raw_content = DocumentService.extract_text(file_path, doc.get("file_type", "text/plain"))
        except Exception:
            raw_content = "Raw content unavailable or document processing failed."

    chunks_cursor = db.document_chunks.find({"document_id": document_id}).sort("chunk_index", 1)
    chunks = await chunks_cursor.to_list(100)

    return DocumentDetailResponse(
        **doc,
        raw_content=raw_content,
        chunks=chunks
    )
