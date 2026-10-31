# Enterprise Knowledge Assistant — Database Design Document

## 1. Executive Summary & Database Selection Rationale

For the **Enterprise Knowledge Assistant**, we selected **MongoDB** (NoSQL document database) combined with **ChromaDB** (embedded vector store).

### Why MongoDB?
1. **Domain Alignment with Enterprise AI Workflows**: Knowledge assistants store complex, semi-structured conversational turns, rich message citations, and variable metadata. MongoDB's native BSON document format allows nested representation of messages, token metrics, and citation pointers without requiring awkward multi-table joins.
2. **Atomic Updates for Real-Time Streaming & Chats**: Appending messages, updating chunk status, and maintaining conversation history is an $O(1)$ atomic push operation (`$push`) in MongoDB.
3. **Strict RBAC via Compound Indexing**: Access isolation is enforced at query time using compound indexes over `{ workspace_id: 1, user_id: 1 }` and `{ accessible_workspaces: 1 }`.
4. **Guaranteed Persistence Across Restarts**: The system connects strictly to persistent MongoDB (`mongodb://localhost:27017` or MongoDB Atlas/Docker) to ensure that all documents, conversations, chunks, and citations survive application restarts and browser refreshes without silent in-memory data loss. In-memory adapters are strictly reserved for isolated unit tests (`APP_ENV=test`).

---

## 2. Collections & Document Schemas

### 2.1 Collection: `users`
Stores user identities, credentials, role descriptions, and workspace access grants.

```json
{
  "_id": "usr_alice",
  "email": "alice@company.com",
  "full_name": "Alice Chen",
  "role": "Staff Platform Engineer",
  "hashed_password": "$2b$12$...",
  "accessible_workspaces": ["ws_engineering", "ws_executive"],
  "created_at": "2026-10-30T08:00:00Z"
}
```

- **Primary Key**: `_id` (String / UUID)
- **Indexes**:
  - `email`: `{ email: 1 }` (Unique index)
  - `accessible_workspaces`: `{ accessible_workspaces: 1 }` (Multikey index for access checks)

---

### 2.2 Collection: `workspaces`
Represents isolated departmental or project knowledge domains.

```json
{
  "_id": "ws_engineering",
  "name": "Engineering & Operations",
  "description": "System architecture, incident runbooks, and deployment standards.",
  "department": "Engineering",
  "created_at": "2026-10-30T08:00:00Z"
}
```

- **Primary Key**: `_id` (String / UUID)
- **Indexes**:
  - `department`: `{ department: 1 }`

---

### 2.3 Collection: `documents`
Tracks uploaded files, their processing state, metadata, and error details.

```json
{
  "_id": "doc_eng_01",
  "workspace_id": "ws_engineering",
  "title": "System Architecture & Service Specifications",
  "filename": "ENG-01_system_architecture.txt",
  "file_path": "storage/documents/ENG-01_system_architecture.txt",
  "file_type": "text/plain",
  "file_size": 1840,
  "status": "INDEXED", // "PENDING" | "PROCESSING" | "INDEXED" | "FAILED"
  "error_message": null,
  "chunk_count": 3,
  "created_at": "2026-10-30T08:30:00Z",
  "updated_at": "2026-10-30T08:30:05Z"
}
```

- **Primary Key**: `_id` (String / UUID)
- **Indexes**:
  - Compound: `{ workspace_id: 1, created_at: -1 }` (Ensures fast retrieval of workspace documents)
  - Status: `{ status: 1 }` (For background processing workers)

---

### 2.4 Collection: `document_chunks`
Stores segmented text chunks extracted from documents, including page numbers and section headers. These are indexed for relational inspection and mirrored into ChromaDB for vector similarity search.

```json
{
  "_id": "chk_eng_01_0",
  "document_id": "doc_eng_01",
  "workspace_id": "ws_engineering",
  "chunk_index": 0,
  "section_title": "Section 1: Overview and Core Services",
  "page_number": 1,
  "content": "Our production platform operates on a distributed microservices architecture...",
  "token_count": 94,
  "created_at": "2026-10-30T08:30:05Z"
}
```

- **Primary Key**: `_id` (String)
- **Indexes**:
  - Compound: `{ document_id: 1, chunk_index: 1 }` (Unique ordered reconstruction)
  - Filter: `{ workspace_id: 1 }`

---

### 2.5 Collection: `conversations`
Maintains conversational state, multi-turn history, and exact grounded citations linking AI responses back to the source document chunks.

```json
{
  "_id": "conv_alice_001",
  "workspace_id": "ws_engineering",
  "user_id": "usr_alice",
  "title": "P1 Escalation and Rollback Query",
  "created_at": "2026-10-30T09:00:00Z",
  "updated_at": "2026-10-30T09:02:15Z",
  "messages": [
    {
      "id": "msg_001",
      "sender": "user",
      "content": "When a P1 incident occurs during a deployment, what is the escalation timeline and how does the rollback policy interact with the load balancer?",
      "status": "COMPLETED",
      "timestamp": "2026-10-30T09:00:00Z"
    },
    {
      "id": "msg_002",
      "sender": "assistant",
      "content": "Based on the internal documentation:\n\n1. **Escalation Timeline**...",
      "status": "COMPLETED",
      "citations": [
        {
          "document_id": "doc_eng_02",
          "document_title": "Incident Response Playbook",
          "chunk_id": "chk_eng_02_1",
          "section_title": "Section 2: Escalation Timelines & On-Call SLAs",
          "page_number": 1,
          "snippet": "P1 Incidents: The Primary On-Call Engineer must acknowledge the alert within 15 minutes..."
        },
        {
          "document_id": "doc_eng_03",
          "document_title": "Production Deployment Strategies & Automated Rollback Policy",
          "chunk_id": "chk_eng_03_2",
          "section_title": "Section 3: Rollback Policy and Load Balancer Interaction",
          "page_number": 1,
          "snippet": "The Application Load Balancer (ALB) instantly redirects the 100% traffic weight pointer back to the previous stable Blue environment..."
        }
      ],
      "timestamp": "2026-10-30T09:00:05Z"
    }
  ]
}
```

- **Primary Key**: `_id` (String / UUID)
- **Indexes**:
  - Compound: `{ workspace_id: 1, user_id: 1, updated_at: -1 }` (Private conversation isolation)

---

## 3. Role-Based Access Control (RBAC) & Boundary Enforcement

1. **Authentication Layer**: Injects the authenticated user object (`user_id`, `accessible_workspaces`).
2. **Workspace Isolation Guard**:
   ```python
   if workspace_id not in current_user.accessible_workspaces:
       raise HTTPException(status_code=403, detail="Access to this workspace is forbidden.")
   ```
3. **Conversation Privacy Guard**:
   Queries always enforce user ownership:
   ```python
   query = {"_id": conversation_id, "user_id": current_user.id, "workspace_id": workspace_id}
   ```
   Even if a user supplies a valid `conversation_id` belonging to someone else, the database returns `null`, producing an explicit `404 Not Found` or `403 Forbidden`.
4. **Vector Search Grounding Filter**:
   ChromaDB vector queries enforce metadata partitioning:
   ```python
   where={"workspace_id": active_workspace_id}
   ```
   Chunks from unauthorized or other workspaces can never bleed into the semantic context.

---

## 4. Failure States & Transactional Safeguards

- **Atomic Message States**: When an AI request begins, the message is marked with `status: "PENDING"`.
- If an LLM or embedding call fails (e.g. rate limit, invalid key), the message is updated to `status: "FAILED"` with an error message.
- A failed model call **never** produces a completed message or false citations, satisfying the core assignment requirement: *"A failed model call must be shown as a failure and must not create an approved or finalized result."*
