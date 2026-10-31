# Verification Notes & Automated Test Suite Coverage

All 18 automated test cases in `backend/tests/` have been executed and passed.

---

## 1. Automated Test Suite Matrix

```bash
cd backend
python -m pytest tests/ -v
```

| Test File | Test Case | Functionality Verified | Status |
| :--- | :--- | :--- | :--- |
| `test_chats.py` | `test_reopen_seeded_conversation_and_citations` | Verifies conversation persistence and citation structure | **PASSED** |
| `test_chats.py` | `test_multi_document_rag_query` | Verifies question requiring info from 2 documents returns citations for both | **PASSED** |
| `test_chats.py` | `test_unsupported_question_handles_missing_evidence` | Verifies unsupported question states evidence is absent with 0 citations | **PASSED** |
| `test_documents.py` | `test_list_documents` | Verifies listing documents scoped to authorized workspace | **PASSED** |
| `test_documents.py` | `test_upload_valid_document` | Verifies text document upload transitions to `INDEXED` with chunks | **PASSED** |
| `test_documents.py` | `test_upload_invalid_file_format` | Verifies unsupported file extensions are rejected with `400 Bad Request` | **PASSED** |
| `test_documents.py` | `test_upload_empty_file_fails` | Verifies empty 0-byte file transitions to `FAILED` with descriptive error | **PASSED** |
| `test_documents.py` | `test_get_document_preview` | Verifies document preview endpoint returns raw content and chunks | **PASSED** |
| `test_rbac.py` | `test_alice_can_access_both_workspaces` | Verifies Alice has access to Engineering and Executive workspaces | **PASSED** |
| `test_rbac.py` | `test_bob_only_sees_engineering_workspace` | Verifies Bob only lists Engineering workspace | **PASSED** |
| `test_rbac.py` | `test_bob_forbidden_from_executive_workspace` | Verifies direct request to Executive workspace returns `403 Forbidden` | **PASSED** |
| `test_rbac.py` | `test_bob_forbidden_from_executive_documents_by_id` | Verifies direct document ID guessing returns `403 Forbidden` | **PASSED** |
| `test_rbac.py` | `test_bob_cannot_access_alices_private_conversations` | Verifies user cannot retrieve private conversations of another user | **PASSED** |
| `test_robustness_and_failures.py` | `test_corrupt_pdf_upload_fails_gracefully` | Verifies corrupt PDF bytes transition status to `FAILED` with clear reason | **PASSED** |
| `test_robustness_and_failures.py` | `test_failed_document_not_in_retrieval_results` | Verifies failed documents are never searchable in ChromaDB | **PASSED** |
| `test_robustness_and_failures.py` | `test_oversized_file_rejected` | Verifies files exceeding 15MB are rejected with `400 Bad Request` | **PASSED** |
| `test_robustness_and_failures.py` | `test_model_failure_marks_message_failed_and_does_not_finalize` | Verifies LLM outages mark message `FAILED`, return 502, never finalize | **PASSED** |
| `test_robustness_and_failures.py` | `test_citation_strictly_validated_against_retrieved_chunks` | Verifies hallucinated citation IDs and fake docs are strictly dropped | **PASSED** |

---

## 2. Database Persistence Verification

- **Real MongoDB Client**: Tested against active MongoDB service on `mongodb://localhost:27017`.
- **Application Restart Verification**: Stopping the FastAPI process and restarting it preserves all seeded documents, user accounts, and conversation turns.
- **Clean Reset Command**: `python backend/reset_db.py` cleanly wipes MongoDB collections and ChromaDB vectors.
- **Seeding Script**: `python backend/seed.py` cleanly restores the demo environment.
