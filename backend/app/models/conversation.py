from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

class Citation(BaseModel):
    document_id: str
    document_title: str
    chunk_id: Optional[str] = None
    section_title: Optional[str] = None
    page_number: Optional[int] = 1
    snippet: str

class Message(BaseModel):
    id: str
    sender: str  # "user" | "assistant"
    content: str
    status: str = "COMPLETED"  # "PENDING" | "COMPLETED" | "FAILED"
    error_message: Optional[str] = None
    citations: List[Citation] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversationBase(BaseModel):
    id: str = Field(alias="_id")
    workspace_id: str
    user_id: str
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

class ConversationSummary(ConversationBase):
    message_count: int = 0

class ConversationDetail(ConversationBase):
    messages: List[Message] = []

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"

class SendMessageRequest(BaseModel):
    content: str
