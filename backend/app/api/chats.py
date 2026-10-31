import uuid
import logging
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.database import get_database
from backend.app.models.user import UserInDB
from backend.app.models.conversation import (
    ConversationSummary,
    ConversationDetail,
    CreateConversationRequest,
    SendMessageRequest,
    Message,
    Citation
)
from backend.app.api.deps import get_current_user, verify_workspace_access
from backend.app.services.rag_service import rag_service
from backend.app.services.ai_service import AIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces/{workspace_id}/conversations", tags=["Chat & Conversations"])

@router.get("", response_model=List[ConversationSummary])
async def list_conversations(
    workspace_id: str = Depends(verify_workspace_access),
    current_user: UserInDB = Depends(get_current_user)
):
    db = get_database()
    cursor = db.conversations.find({
        "workspace_id": workspace_id,
        "user_id": current_user.id
    }).sort("updated_at", -1)

    convs = await cursor.to_list(100)
    summaries = []
    for c in convs:
        msgs = c.get("messages", [])
        summaries.append(ConversationSummary(
            **c,
            message_count=len(msgs)
        ))
    return summaries

@router.post("", response_model=ConversationDetail, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: CreateConversationRequest,
    workspace_id: str = Depends(verify_workspace_access),
    current_user: UserInDB = Depends(get_current_user)
):
    db = get_database()
    conv_id = f"conv_{uuid.uuid4().hex[:12]}"
    conv_record = {
        "_id": conv_id,
        "workspace_id": workspace_id,
        "user_id": current_user.id,
        "title": req.title or "New Conversation",
        "messages": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await db.conversations.insert_one(conv_record)
    return ConversationDetail(**conv_record)

@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    workspace_id: str = Depends(verify_workspace_access),
    current_user: UserInDB = Depends(get_current_user)
):
    db = get_database()
    conv = await db.conversations.find_one({
        "_id": conversation_id,
        "workspace_id": workspace_id,
        "user_id": current_user.id
    })
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or access denied."
        )
    return ConversationDetail(**conv)

@router.post("/{conversation_id}/messages", response_model=Message)
async def send_message(
    conversation_id: str,
    req: SendMessageRequest,
    workspace_id: str = Depends(verify_workspace_access),
    current_user: UserInDB = Depends(get_current_user)
):
    db = get_database()
    conv = await db.conversations.find_one({
        "_id": conversation_id,
        "workspace_id": workspace_id,
        "user_id": current_user.id
    })
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or access denied."
        )

    user_query = req.content.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    # 1. Save user turn
    user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    user_message = {
        "id": user_msg_id,
        "sender": "user",
        "content": user_query,
        "status": "COMPLETED",
        "citations": [],
        "timestamp": datetime.now(timezone.utc)
    }

    # 2. Add pending placeholder for assistant
    asst_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    pending_asst_message = {
        "id": asst_msg_id,
        "sender": "assistant",
        "content": "",
        "status": "PENDING",
        "citations": [],
        "timestamp": datetime.now(timezone.utc)
    }

    await db.conversations.update_one(
        {"_id": conversation_id},
        {
            "$push": {"messages": {"$each": [user_message, pending_asst_message]}},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )

    # 3. Contextual Retrieval Query Formulation (Resolves follow-up pronouns)
    existing_messages = conv.get("messages", [])
    retrieval_query = user_query
    if existing_messages:
        # If there are prior turns, append context keywords to improve vector match
        prev_user_msgs = [m["content"] for m in existing_messages if m["sender"] == "user"]
        if prev_user_msgs:
            retrieval_query = f"{user_query} (Context: {prev_user_msgs[-1][:80]})"

    # Retrieve context chunks strictly scoped to workspace_id
    relevant_chunks = rag_service.search_chunks(retrieval_query, workspace_id=workspace_id, top_k=5)

    # Resilient fallback to MongoDB chunks if vector search returned empty
    if not relevant_chunks:
        import re
        doc_cursor = db.documents.find({"workspace_id": workspace_id, "status": "INDEXED"})
        doc_list = await doc_cursor.to_list(100)
        doc_map = {d["_id"]: d.get("title", "Document") for d in doc_list}
        
        cursor = db.document_chunks.find({"workspace_id": workspace_id})
        mongo_chunks = await cursor.to_list(100)
        query_words = set(re.findall(r'\w+', user_query.lower()))
        
        matched = []
        for chk in mongo_chunks:
            if chk.get("document_id") not in doc_map:
                continue
            content = chk.get("content", "")
            matches = sum(1 for w in query_words if len(w) > 3 and w in content.lower())
            if matches > 0:
                matched.append({
                    "chunk_id": chk.get("_id"),
                    "document_id": chk.get("document_id"),
                    "document_title": doc_map.get(chk.get("document_id"), "Document"),
                    "workspace_id": workspace_id,
                    "section_title": chk.get("section_title", "General"),
                    "page_number": chk.get("page_number", 1),
                    "content": content,
                    "score": matches
                })
        matched.sort(key=lambda x: x.get("score", 0), reverse=True)
        relevant_chunks = matched[:5]

    # 4. Generate AI response with grounded citations
    try:
        history = existing_messages + [user_message]
        ai_result = await AIService.generate_response(
            query=user_query,
            context_chunks=relevant_chunks,
            conversation_history=history
        )

        completed_asst_message = {
            "id": asst_msg_id,
            "sender": "assistant",
            "content": ai_result["answer"],
            "status": "COMPLETED",
            "error_message": None,
            "citations": ai_result.get("citations", []),
            "timestamp": datetime.now(timezone.utc)
        }

        # Auto-update conversation title from first user query
        update_fields = {
            "messages.$[elem]": completed_asst_message,
            "updated_at": datetime.now(timezone.utc)
        }
        if conv.get("title") == "New Conversation" and len(existing_messages) == 0:
            short_title = user_query[:40] + ("..." if len(user_query) > 40 else "")
            update_fields["title"] = short_title

        await db.conversations.update_one(
            {"_id": conversation_id},
            {"$set": update_fields},
            array_filters=[{"elem.id": asst_msg_id}]
        )

        return Message(**completed_asst_message)

    except Exception as llm_err:
        logger.error(f"AI generation failed for conversation {conversation_id}: {llm_err}")
        clean_error = "The AI model service encountered a processing error. No finalized response was saved."
        if "API_KEY" in str(llm_err):
            clean_error = "AI Model API key is missing or invalid in server environment configuration (.env)."
        elif "quota" in str(llm_err).lower() or "rate" in str(llm_err).lower():
            clean_error = "AI Provider rate limit reached. Please wait a moment and retry."

        failed_asst_message = {
            "id": asst_msg_id,
            "sender": "assistant",
            "content": f"⚠️ **Model Failure**: {clean_error}",
            "status": "FAILED",
            "error_message": clean_error,
            "citations": [],
            "timestamp": datetime.now(timezone.utc)
        }

        # Persist failed state to DB; NEVER create an approved/finalized response
        await db.conversations.update_one(
            {"_id": conversation_id},
            {"$set": {"messages.$[elem]": failed_asst_message, "updated_at": datetime.now(timezone.utc)}},
            array_filters=[{"elem.id": asst_msg_id}]
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=clean_error
        )
