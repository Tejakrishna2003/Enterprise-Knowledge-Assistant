import os
import sys
import shutil
import asyncio
import logging
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import settings
from backend.app.core.database import init_db, get_database
from backend.app.core.security import get_password_hash
from backend.app.services.document_service import DocumentService
from backend.app.services.rag_service import rag_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

SAMPLE_DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")

USERS = [
    {
        "_id": "usr_alice",
        "email": "alice@company.com",
        "full_name": "Alice Chen",
        "role": "Staff Platform Engineer",
        "hashed_password": get_password_hash("alice123"),
        "accessible_workspaces": ["ws_engineering", "ws_executive"],
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": "usr_bob",
        "email": "bob@company.com",
        "full_name": "Bob Miller",
        "role": "Contractor / Junior Dev",
        "hashed_password": get_password_hash("bob123"),
        "accessible_workspaces": ["ws_engineering"],
        "created_at": datetime.now(timezone.utc)
    }
]

WORKSPACES = [
    {
        "_id": "ws_engineering",
        "name": "Engineering & Operations",
        "description": "System architecture, deployment runbooks, and incident response SLAs.",
        "department": "Engineering",
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": "ws_executive",
        "name": "Executive & Finance (Confidential)",
        "description": "Corporate development, Project Falcon acquisition, and executive compensation.",
        "department": "Executive",
        "created_at": datetime.now(timezone.utc)
    }
]

async def seed():
    logger.info("Initializing database for seeding...")
    db = await init_db()

    # 1. Clean existing collections in MongoDB and ChromaDB
    await db.users.delete_many({})
    await db.workspaces.delete_many({})
    await db.documents.delete_many({})
    await db.document_chunks.delete_many({})
    await db.conversations.delete_many({})

    try:
        rag_service.client.delete_collection("workspace_document_chunks")
        rag_service.collection = rag_service.client.create_collection(
            name="workspace_document_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB vector store cleared and reset.")
    except Exception as chroma_err:
        logger.warning(f"ChromaDB reset note: {chroma_err}")

    # 2. Insert Users
    await db.users.insert_many(USERS)
    logger.info(f"Seeded {len(USERS)} users (Alice & Bob).")

    # 3. Insert Workspaces
    await db.workspaces.insert_many(WORKSPACES)
    logger.info(f"Seeded {len(WORKSPACES)} workspaces.")

    # 4. Ingest and index synthetic sample documents
    doc_specs = [
        # Workspace 1: Engineering
        {
            "id": "doc_eng_01",
            "workspace_id": "ws_engineering",
            "title": "System Architecture & Service Specifications",
            "filename": "ENG-01_system_architecture.txt",
            "source_path": os.path.join(SAMPLE_DATA_ROOT, "workspace_engineering", "ENG-01_system_architecture.txt")
        },
        {
            "id": "doc_eng_02",
            "workspace_id": "ws_engineering",
            "title": "Incident Response Playbook & Escalation SLAs",
            "filename": "ENG-02_incident_response_playbook.txt",
            "source_path": os.path.join(SAMPLE_DATA_ROOT, "workspace_engineering", "ENG-02_incident_response_playbook.txt")
        },
        {
            "id": "doc_eng_03",
            "workspace_id": "ws_engineering",
            "title": "Production Deployment & Rollback Policy",
            "filename": "ENG-03_deployment_and_rollback_policy.txt",
            "source_path": os.path.join(SAMPLE_DATA_ROOT, "workspace_engineering", "ENG-03_deployment_and_rollback_policy.txt")
        },
        # Workspace 2: Executive
        {
            "id": "doc_exec_01",
            "workspace_id": "ws_executive",
            "title": "Q3 2026 Executive Financial Performance & Budget",
            "filename": "EXEC-01_q3_financial_performance.txt",
            "source_path": os.path.join(SAMPLE_DATA_ROOT, "workspace_executive", "EXEC-01_q3_financial_performance.txt")
        },
        {
            "id": "doc_exec_02",
            "workspace_id": "ws_executive",
            "title": "Project Falcon Acquisition Blueprint",
            "filename": "EXEC-02_project_falcon_merger_strategy.txt",
            "source_path": os.path.join(SAMPLE_DATA_ROOT, "workspace_executive", "EXEC-02_project_falcon_merger_strategy.txt")
        },
        {
            "id": "doc_exec_03",
            "workspace_id": "ws_executive",
            "title": "Executive Compensation & Equity Vesting",
            "filename": "EXEC-03_executive_compensation_and_equity.txt",
            "source_path": os.path.join(SAMPLE_DATA_ROOT, "workspace_executive", "EXEC-03_executive_compensation_and_equity.txt")
        }
    ]

    for spec in doc_specs:
        src = spec["source_path"]
        if not os.path.exists(src):
            logger.warning(f"File {src} does not exist. Skipping.")
            continue

        dest = os.path.join(settings.DOCUMENTS_DIR, f"{spec['id']}_{spec['filename']}")
        shutil.copyfile(src, dest)
        file_size = os.path.getsize(dest)

        extracted_text = DocumentService.extract_text(dest, "text/plain")
        chunks = DocumentService.chunk_document(extracted_text, spec["id"], spec["workspace_id"])

        doc_record = {
            "_id": spec["id"],
            "workspace_id": spec["workspace_id"],
            "title": spec["title"],
            "filename": spec["filename"],
            "file_path": dest,
            "file_type": "text/plain",
            "file_size": file_size,
            "status": "INDEXED",
            "error_message": None,
            "chunk_count": len(chunks),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.documents.insert_one(doc_record)

        if chunks:
            await db.document_chunks.insert_many(chunks)
            rag_service.index_chunks(chunks, doc_record)

        logger.info(f"Ingested and indexed: {spec['title']} ({len(chunks)} chunks).")

    # Add a sample failed document to demonstrate failure status handling per assignment requirements
    failed_doc = {
        "_id": "doc_eng_failed_sample",
        "workspace_id": "ws_engineering",
        "title": "Corrupt Legacy Architecture Spec (broken_manual.pdf)",
        "filename": "broken_manual.pdf",
        "file_path": os.path.join(settings.DOCUMENTS_DIR, "broken_manual.pdf"),
        "file_type": "application/pdf",
        "file_size": 1024,
        "status": "FAILED",
        "error_message": "Invalid PDF format: file header corrupted or missing EOF marker.",
        "chunk_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await db.documents.insert_one(failed_doc)
    logger.info("Inserted sample FAILED document for error handling demonstration.")

    # 5. Create an initial conversation for Alice demonstrating multi-doc synthesis
    sample_conversation = {
        "_id": "conv_alice_demo_01",
        "workspace_id": "ws_engineering",
        "user_id": "usr_alice",
        "title": "P1 Escalation & Deployment Rollback Policy",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "messages": [
            {
                "id": "msg_user_01",
                "sender": "user",
                "content": "When a P1 incident occurs during a deployment, what is the escalation timeline and how does the rollback policy interact with the load balancer?",
                "status": "COMPLETED",
                "citations": [],
                "timestamp": datetime.now(timezone.utc)
            },
            {
                "id": "msg_asst_01",
                "sender": "assistant",
                "content": (
                    "Based on the **Incident Response Playbook** and the **Deployment & Rollback Policy**, here is the procedure when a P1 incident occurs during a deployment:\n\n"
                    "1. **Escalation Timeline**:\n"
                    "   - The **Primary On-Call Engineer** must acknowledge the alert within **15 minutes**.\n"
                    "   - If unacknowledged within 15 minutes, automated paging escalates to the Secondary On-Call and Engineering Director.\n"
                    "   - An **Incident Commander (IC)** (VP of Infrastructure or designated Staff SRE) is assigned within **25 minutes** of the alert.\n\n"
                    "2. **Rollback & Load Balancer Interaction**:\n"
                    "   - The **Application Load Balancer (ALB)** immediately redirects 100% of traffic back to the previous stable Blue environment.\n"
                    "   - The ALB enforces a **30-second connection draining period** on the failed Green cluster to let active HTTP requests finish.\n"
                    "   - **Emergency Authority**: If a P1 incident is active, the designated **Incident Commander** has unilateral authority to initiate an immediate hard-cut rollback, bypassing normal drain timers."
                ),
                "status": "COMPLETED",
                "error_message": None,
                "citations": [
                    {
                        "document_id": "doc_eng_02",
                        "document_title": "Incident Response Playbook & Escalation SLAs",
                        "chunk_id": "chk_doc_eng_02_1",
                        "section_title": "Section 2: Escalation Timelines & On-Call SLAs",
                        "page_number": 1,
                        "snippet": "P1 Incidents: The Primary On-Call Engineer must acknowledge the alert within 15 minutes. If unacknowledged within 15 minutes, automated paging escalates to the Secondary On-Call and Engineering Director."
                    },
                    {
                        "document_id": "doc_eng_03",
                        "document_title": "Production Deployment & Rollback Policy",
                        "chunk_id": "chk_doc_eng_03_2",
                        "section_title": "Section 3: Rollback Policy and Load Balancer Interaction",
                        "page_number": 1,
                        "snippet": "The Application Load Balancer (ALB) instantly redirects the 100% traffic weight pointer back to the previous stable Blue environment. The load balancer enforces a 30-second connection draining period on the failed Green cluster."
                    }
                ],
                "timestamp": datetime.now(timezone.utc)
            }
        ]
    }
    await db.conversations.insert_one(sample_conversation)
    logger.info("Created sample conversation for Alice demonstrating multi-document synthesis.")
    logger.info("Database seeding successfully completed!")

if __name__ == "__main__":
    asyncio.run(seed())
