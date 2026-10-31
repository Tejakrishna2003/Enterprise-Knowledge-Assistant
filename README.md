# Enterprise Knowledge Assistant

A secure, multi-tenant Enterprise Knowledge Assistant built with **FastAPI**, **MongoDB**, **ChromaDB**, and **React**. The assistant provides strictly grounded answers with verifiable document citations, multi-turn follow-up reasoning, and workspace-scoped Role-Based Access Control (RBAC).

---

## 🌟 Architecture & Key Highlights

### 1. AI Grounding & Strict Citation Validation
- **Verifiable Grounding**: The backend strictly validates every citation against authentic retrieved document chunks before finalizing the response.
- **Anti-Hallucination Guard**: The assistant never invents document titles, fake section headings, or arbitrary page numbers. Official metadata is enforced directly from database records.
- **Missing-Evidence Honesty**: When accessible documents do not contain the answer, the model explicitly sets `is_supported: false` and explains what specific information is missing, rather than speculating.
- **Multi-Document Synthesis**: Capable of synthesizing facts that bridge across multiple separate documents in the same workspace.

### 2. Real AI Model Configuration & Dual-Mode Execution
- **Hosted Model Integration**: Built for Google Gemini (`gemini-1.5-flash` or `gemini-2.5-flash`) via `google-generativeai` and OpenAI (`gpt-4o-mini`) via `openai`.
- **Environment Configuration**: Model provider and API keys are stored in server-side configuration (`backend/.env`).
- **Grounded Synthesizer Fallback**: If an external API key is not yet configured or is in placeholder state, the system automatically uses an internal grounded synthesizer that computes relevance over actual workspace document chunks and strictly validates citations—allowing complete offline reviewer evaluation without mandatory cloud API tokens.
- **Resilient Failure Handling**: A failed model call (timeout, invalid key, rate limit) transitions the message state to `FAILED` with a clean error explanation—**it never produces an approved or finalized result**.
- **Automated Test Mock**: Mock mode is strictly restricted to automated tests (`APP_ENV=test` or `AI_PROVIDER=mock`) so CI test suites can execute completely offline with zero network flakiness.

### 3. Persistent Database & RBAC Security
- **MongoDB Persistence**: Real MongoDB document database storing `users`, `workspaces`, `documents`, `document_chunks`, and `conversations`.
- **Compound Indexing**:
  - `{ workspace_id: 1, user_id: 1, updated_at: -1 }` on `conversations`
  - `{ workspace_id: 1, created_at: -1 }` on `documents`
- **Tamper-Proof Authorization**: Direct record ID tampering attempts immediately return `403 Forbidden` (for unauthorized workspaces/documents) or `404 Not Found` (for other users' private conversations).
- **Restart Survival**: All records, chats, uploaded documents, and citations persist across server restarts and browser reloads.

### 4. Robust Document Processing Lifecycle
- **Supported Formats**: Text-based PDF (`.pdf`), Markdown (`.md`), and Plain Text (`.txt`).
- **Processing Statuses**: `PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `INDEXED` or `FAILED`.
- **Corrupt File & Edge Case Handling**: Corrupted PDFs, empty 0-byte files, and oversized files (>15MB) are trapped with descriptive error messages.
- **Zero Pollution**: Failed or partial documents are **never** indexed into ChromaDB and never appear in retrieval results.

---

## 👥 Seeded Demo Accounts

| User | Email | Role | Accessible Workspaces |
| :--- | :--- | :--- | :--- |
| **Alice Chen** | `alice@company.com` | Staff Platform Engineer | • `Engineering & Operations`<br>• `Executive & Finance (Confidential)` |
| **Bob Miller** | `bob@company.com` | Contractor / Junior Dev | • `Engineering & Operations` **only** |

---

## 🚀 Setup & Reproduction Guide

### Prerequisites
- Python 3.11 or 3.12
- Node.js 18+ and npm
- MongoDB running locally on port 27017 or via Docker

---

### Step 1: Start MongoDB
If you have Docker:
```bash
docker compose up -d
```
Or start your local MongoDB service:
```bash
# Verify MongoDB is running
mongosh --eval "db.runCommand({ ping: 1 })"
```

---

### Step 2: Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY (or OPENAI_API_KEY)
# Example:
# AI_PROVIDER=gemini
# AI_MODEL_NAME=gemini-1.5-flash
# GEMINI_API_KEY=AIzaSy...

# Seed demo data (Alice, Bob, 2 workspaces, 6 documents, sample conversation)
python seed.py

# (Optional) Clean database reset:
# python reset_db.py

# Start FastAPI backend
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation: `http://127.0.0.1:8000/docs`

---

### Step 3: Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Demonstration Scenarios & Script

A complete video script is documented in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

1. **Upload & Process Document**:
   - Open Document Library in *Engineering & Operations*.
   - Upload a text or PDF document. Watch status transition to `INDEXED` with chunk count.
   - Click "Preview" to inspect extracted content.
2. **Multi-Document Synthesis**:
   - In *Engineering & Operations*, submit:
     > *"When a P1 incident occurs during a deployment, what is the escalation timeline and how does the rollback policy interact with the load balancer?"*
   - Assistant synthesizes facts from `ENG-02 (Incident Playbook)` and `ENG-03 (Deployment Policy)`.
   - Click both citation pills to inspect the exact quotes in the evidence drawer.
3. **Follow-Up Continuity & Browser Refresh**:
   - Ask: *"Who has the authority to bypass those drain timers during this rollback?"*
   - Assistant answers with context from the prior turn.
   - Press **F5 (Refresh)**: Conversation history, title, messages, and citations reload persistently from MongoDB.
4. **Unsupported Question (Missing Evidence)**:
   - Ask: *"What is our company's refund policy for enterprise customer subscription cancellations in Germany?"*
   - Assistant explains that customer refund policies are absent from the engineering documents with 0 false citations.
5. **RBAC & Privacy Boundary**:
   - Switch user to **Bob Miller**.
   - Notice *Executive & Finance* workspace and Alice's chat history disappear from the UI.
   - Attempting to query `/api/workspaces/ws_executive/documents` or Alice's chat ID returns `403 Forbidden` / `404 Not Found`.
6. **Error & Failure Handling**:
   - Attempt uploading an invalid or corrupt file $\rightarrow$ shows immediate descriptive failure badge.
   - When AI provider fails $\rightarrow$ shows distinct red failure state without generating phantom records.

---

## 📁 Repository Layout

```
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routers (auth, workspaces, documents, chats)
│   │   ├── core/            # Config, security, MongoDB database adapter
│   │   ├── models/          # Pydantic & BSON schemas
│   │   └── services/        # AI orchestration, ChromaDB RAG, document parsing
│   ├── storage/             # Stored files and persistent ChromaDB vector store
│   ├── tests/               # 18 automated Pytest test cases
│   ├── main.py              # Application entrypoint
│   ├── seed.py              # Database seeder
│   ├── reset_db.py          # Clean database wiper
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Example environment config
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (Header, Sidebar, ChatWorkspace, Modals)
│   │   ├── services/        # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── sample_data/             # 6 synthetic sample documents across 2 workspaces
│   ├── workspace_engineering/
│   └── workspace_executive/
├── docs/
│   ├── DATABASE_DESIGN.md   # MongoDB collections, indexes, and design decisions
│   ├── AI_DESIGN.md         # RAG pipeline, prompts, and groundedness
│   ├── API_SPEC.md          # REST API endpoints and validation error codes
│   ├── DEMO_SCRIPT.md       # Step-by-step video recording instructions
│   └── VERIFICATION_NOTES.md# Test coverage and verification logs
└── docker-compose.yml       # Local MongoDB container
```

---

## 🧪 Running Automated Tests
```bash
cd backend
python -m pytest tests/ -v
```
All 18 automated tests will run and assert:
- Multi-document RAG answers
- Unsupported question handling
- Citation correctness & dropping of hallucinated sources
- Corrupt PDF uploads and error states
- Oversized file rejection
- Model failure handling
- RBAC boundary enforcement and ID guessing guards
- Non-searchability of failed documents
