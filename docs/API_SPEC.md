# Enterprise Knowledge Assistant — API Specification

The backend provides a RESTful API built on **FastAPI**. Interactive Swagger UI documentation is available at `/docs` and OpenAPI JSON at `/openapi.json`.

---

## 1. Authentication & Session

Authentication uses Bearer Tokens or Demo Session Headers. The backend extracts `Authorization: Bearer <token>` or `X-User-Id: <user_id>`.

### Seeded Demo Accounts:
- **Alice Chen**: `usr_alice` (Senior Engineer: access to `ws_engineering` & `ws_executive`)
- **Bob Miller**: `usr_bob` (Contractor: access **only** to `ws_engineering`)

---

## 2. Endpoints Overview

### 2.1 Authentication & User Context
- `GET /api/auth/me`: Returns current user profile and list of accessible workspaces.
- `POST /api/auth/switch-user`: Switches the active demo session user (`alice` or `bob`).

### 2.2 Workspaces
- `GET /api/workspaces`: Lists all workspaces accessible to the authenticated user.
  - Returns `401 Unauthorized` if unauthenticated.
- `GET /api/workspaces/{workspace_id}`: Returns workspace metadata.
  - Returns `403 Forbidden` if user is not a member of this workspace.

### 2.3 Documents
- `GET /api/workspaces/{workspace_id}/documents`: Lists all documents in the workspace with processing status (`PENDING`, `INDEXED`, `FAILED`).
  - Returns `403 Forbidden` if user is not authorized for `workspace_id`.
- `POST /api/workspaces/{workspace_id}/documents`: Upload a new document (`.txt` or `.pdf` as `multipart/form-data`).
  - Returns `201 Created` with document record.
  - Returns `400 Bad Request` if file format is unsupported or file is empty.
  - Returns `403 Forbidden` if user lacks access.
- `GET /api/workspaces/{workspace_id}/documents/{document_id}`: Returns full document details and raw text for the source preview viewer.
  - Returns `404 Not Found` if document does not exist.
  - Returns `403 Forbidden` if document is outside user's accessible workspaces.

### 2.4 Conversations & Chat
- `GET /api/workspaces/{workspace_id}/conversations`: Returns list of saved conversations owned by the user in this workspace.
  - Filtered by `user_id == current_user.id` and `workspace_id == workspace_id`.
- `POST /api/workspaces/{workspace_id}/conversations`: Creates a new conversation thread.
  - Request body: `{ "title": "Optional title" }`
- `GET /api/workspaces/{workspace_id}/conversations/{conversation_id}`: Reopens an existing conversation thread with full message history and citations.
  - Returns `404 Not Found` / `403 Forbidden` if the user is not the owner or lacks workspace access.
- `POST /api/workspaces/{workspace_id}/conversations/{conversation_id}/messages`: Submits a user query, triggers RAG vector retrieval, and returns the AI answer with citations.
  - Request body: `{ "content": "Question text" }`
  - Response: Assistant message object with status (`COMPLETED` or `FAILED`), answer, and `citations` array.

---

## 3. Error Responses & Validation Statuses

| Status Code | Scenario | Payload Example |
| :--- | :--- | :--- |
| `400 Bad Request` | Invalid upload or missing question | `{"detail": "Unsupported file format. Please upload .txt or .pdf files."}` |
| `401 Unauthorized` | Missing or invalid user identity | `{"detail": "Authentication required."}` |
| `403 Forbidden` | Accessing restricted workspace or private chat | `{"detail": "Access to workspace 'ws_executive' is forbidden for user 'usr_bob'."}` |
| `404 Not Found` | Document or conversation ID does not exist | `{"detail": "Conversation not found."}` |
| `502 Bad Gateway` / `500 Internal Error` | AI Model API failure or timeout | `{"detail": "Model execution failed. No finalized message was saved."}` |
