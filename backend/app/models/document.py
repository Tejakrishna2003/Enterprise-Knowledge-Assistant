from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

class DocumentChunk(BaseModel):
    id: str = Field(alias="_id")
    document_id: str
    workspace_id: str
    chunk_index: int
    section_title: str
    page_number: int
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

class DocumentBase(BaseModel):
    id: str = Field(alias="_id")
    workspace_id: str
    title: str
    filename: str
    file_type: str
    file_size: int
    status: str = "PENDING"  # PENDING, PROCESSING, INDEXED, FAILED
    error_message: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

class DocumentResponse(DocumentBase):
    pass

class DocumentDetailResponse(DocumentBase):
    raw_content: Optional[str] = None
    chunks: Optional[List[DocumentChunk]] = []
