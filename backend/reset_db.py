import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import settings
from backend.app.core.database import init_db, get_database
from backend.app.services.rag_service import rag_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reset_db")

async def reset_database():
    logger.info("Connecting to MongoDB to perform clean reset...")
    db = await init_db()

    collections = ["users", "workspaces", "documents", "document_chunks", "conversations"]
    for col in collections:
        res = await db[col].delete_many({})
        logger.info(f"Cleared collection '{col}' (deleted {res.deleted_count} documents).")

    # Reset ChromaDB collections
    try:
        rag_service.client.delete_collection("workspace_document_chunks")
        rag_service.collection = rag_service.client.create_collection(
            name="workspace_document_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB vector collection reset successfully.")
    except Exception as e:
        logger.warning(f"ChromaDB reset note: {e}")

    logger.info("Database reset complete. Run 'python backend/seed.py' to re-seed demo data.")

if __name__ == "__main__":
    asyncio.run(reset_database())
