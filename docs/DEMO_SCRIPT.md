# 24-Hour Mandatory Demo Video Recording Script

Use this storyboard to record the demo video required by the 4SightAI hiring assignment. Target duration: **4 to 7 minutes**.

---

## 🎬 Scene 1: Introduction & Architecture (0:00 - 0:45)
- **On Screen**: Application opened in the browser (`http://localhost:5173`) and VS Code showing the repository structure.
- **Narrate**:
  > *"Hello, this is my submission for the 4SightAI Enterprise Knowledge Assistant hiring assignment. The solution is built with a FastAPI backend, persistent MongoDB for conversations and documents, ChromaDB for workspace-isolated semantic retrieval, and a modern React frontend. It provides strictly grounded multi-turn answers with verified citations, role-based access control, and resilient error states."*

---

## 🎬 Scene 2: Document Ingestion & Processing Status (0:45 - 1:45)
- **On Screen**:
  1. Show that you are logged in as **Alice Chen** in the **Engineering & Operations** workspace.
  2. Click **Document Library**: Show the three pre-seeded documents with their `INDEXED` status badges and chunk counts.
  3. Click **Upload Document**:
     - First, demonstrate validation: Try uploading an invalid or empty file to show the clear `FAILED` error badge (`"Uploaded file is empty (0 bytes)"` or format error).
     - Next, upload a valid text document (`sample_data/workspace_engineering/ENG-01_system_architecture.txt` or a new note).
     - Show the upload progress indicator and the transition from `PROCESSING` to `INDEXED`.
  4. Click **Preview** on one of the documents to show the full extracted content and chunk viewer.
- **Narrate**:
  > *"Documents undergo a clear lifecycle: pending, processing, indexed, or failed. Failed or invalid documents are rejected with clear error messages and are never indexed into the vector database. Permitted users can review the original content in the preview drawer."*

---

## 🎬 Scene 3: Multi-Document Synthesis & Verified Citations (1:45 - 3:00)
- **On Screen**:
  1. Click **New Chat** or navigate to the chat workspace.
  2. Ask the multi-document synthesis question (click the pre-built card or type):
     > *"When a P1 incident occurs during a deployment, what is the escalation timeline and how does the rollback policy interact with the load balancer?"*
  3. Watch the assistant response generate with structured markdown.
  4. Point out the citation pills at the bottom.
  5. **Click on each citation pill**:
     - The first citation opens the drawer displaying `ENG-02 (Incident Response Playbook)` with the 15-minute on-call SLA.
     - The second citation displays `ENG-03 (Deployment & Rollback Policy)` with the 30-second load balancer connection drain.
- **Narrate**:
  > *"Notice that this answer requires synthesizing facts from two separate documents: the incident response playbook for the escalation timeline, and the deployment policy for the load balancer interaction. The backend strictly validates every citation against authentic retrieved chunks to prevent hallucinated references. When I click a citation, the user can inspect the exact section, page, and verbatim quote."*

---

## 🎬 Scene 4: Follow-Up Turn & Browser Refresh Persistence (3:00 - 4:00)
- **On Screen**:
  1. In the same thread, ask a contextual follow-up question:
     > *"Who has the authority to bypass those drain timers during this rollback?"*
  2. The assistant responds:
     > *"The designated Incident Commander (IC) has unilateral emergency authority to initiate an immediate hard-cut rollback and bypass the 30-second connection drain timers."* with a citation to `ENG-03 Section 3`.
  3. **Press the Browser Refresh Button (F5)** or reload the page.
  4. Show that the chat thread, title, full message history, and citations remain completely intact.
- **Narrate**:
  > *"The assistant resolves contextual pronouns from previous turns. Now I reload the browser. All conversation state, messages, and citations survive because they are stored persistently in MongoDB, not held in temporary frontend memory."*

---

## 🎬 Scene 5: Unsupported Question (Missing Evidence) (4:00 - 4:45)
- **On Screen**:
  1. Ask an unsupported question outside the workspace knowledge base:
     > *"What is our company's refund policy for enterprise customer subscription cancellations in Germany?"*
  2. Show the assistant's honest response:
     > *"The accessible documents in this workspace do not contain information regarding customer subscription refund policies or cancellation terms in Germany. The provided engineering documents strictly cover system architecture, incident response playbooks, and production deployment policies."*
  3. Notice the amber badge indicating missing evidence and **zero hallucinated citations**.
- **Narrate**:
  > *"When documents do not support an answer, the assistant never hallucinates. It explicitly states that the evidence is absent from the accessible documents and explains what is missing."*

---

## 🎬 Scene 6: RBAC & Private History Boundary (4:45 - 5:45)
- **On Screen**:
  1. Open the user switcher in the top header and switch to **Bob Miller (Contractor)**.
  2. Notice that the workspace dropdown **only displays Engineering & Operations**; the confidential Executive workspace is completely hidden from Bob.
  3. Notice that Bob's conversation list does not contain Alice's private chats.
  4. Demonstrate direct API protection in terminal or Swagger UI at `http://127.0.0.1:8000/docs`:
     - Run in terminal:
       ```bash
       curl -i -H "X-User-Id: usr_bob" http://127.0.0.1:8000/api/workspaces/ws_executive/documents
       # -> HTTP/1.1 403 Forbidden: "Access to workspace 'ws_executive' is forbidden for your user role."
       ```
     - Attempting to query Alice's conversation ID as Bob:
       ```bash
       curl -i -H "X-User-Id: usr_bob" http://127.0.0.1:8000/api/workspaces/ws_engineering/conversations/conv_alice_demo_01
       # -> HTTP/1.1 404 Not Found: "Conversation 'conv_alice_demo_01' not found or access denied."
       ```
- **Narrate**:
  > *"Role-based access control is strictly enforced at the database query and API routing levels. Restricted workspaces and private conversation histories are inaccessible through both the UI and direct API calls."*

---

## 🎬 Scene 7: Model / Processing Failure & Limitations (5:45 - 6:30)
- **On Screen**:
  1. Show what happens if the AI model fails or if a network error occurs:
     - The assistant displays a clear failure state card with a Retry option.
     - The message is marked as `FAILED` in the database—no finalized or unapproved result is ever saved.
  2. Briefly state the known limitations:
     - Scanned OCR is outside scope (only text-based PDFs and text files are supported).
     - Queries are scoped to one workspace at a time by design.
- **Narrate**:
  > *"Failed model calls are always presented as failures and never create approved results. All assignment requirements and test cases are verified. Thank you."*
