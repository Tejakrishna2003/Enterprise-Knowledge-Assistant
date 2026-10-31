import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None
is_mock_db: bool = False

async def init_db() -> AsyncIOMotorDatabase:
    global client, db, is_mock_db
    try:
        real_client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2500)
        # Ping server to confirm active persistent MongoDB
        await real_client.admin.command('ping')
        client = real_client
        db = client[settings.MONGODB_DB_NAME]
        is_mock_db = False
        logger.info(f"Connected to persistent MongoDB at {settings.MONGODB_URI} (Database: {settings.MONGODB_DB_NAME})")
    except Exception as e:
        if settings.ALLOW_IN_MEMORY_FALLBACK or settings.APP_ENV == "test":
            logger.warning(f"Could not connect to MongoDB ({e}). Test/Fallback mode active: initializing mongomock.")
            from mongomock_motor import AsyncMongoMockClient
            mock_client = AsyncMongoMockClient()
            client = mock_client
            db = client[settings.MONGODB_DB_NAME]
            is_mock_db = True
        else:
            logger.error(f"FATAL: Unable to connect to persistent MongoDB at {settings.MONGODB_URI}: {e}")
            raise ConnectionError(
                f"Failed to connect to persistent MongoDB at {settings.MONGODB_URI}. "
                "Ensure MongoDB service is running or start it with 'docker compose up -d'. "
                "Silent in-memory fallback is disabled in non-test environments."
            ) from e

    await create_indexes()
    return db

async def create_indexes():
    if db is None:
        return
    try:
        # Users indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("accessible_workspaces")

        # Documents indexes
        await db.documents.create_index([("workspace_id", 1), ("created_at", -1)])
        await db.documents.create_index("status")

        # Document Chunks indexes
        await db.document_chunks.create_index([("document_id", 1), ("chunk_index", 1)])
        await db.document_chunks.create_index("workspace_id")

        # Conversations indexes
        await db.conversations.create_index([("workspace_id", 1), ("user_id", 1), ("updated_at", -1)])

        logger.info("MongoDB compound indexes verified and active.")
    except Exception as idx_err:
        logger.warning(f"Index creation note: {idx_err}")

def get_database() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db

async def close_db():
    global client, db
    if client:
        client.close()
        logger.info("Closed MongoDB client connection.")
        client = None
        db = None
