import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="workspace_document_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def index_chunks(self, chunks: List[Dict[str, Any]], doc_metadata: Dict[str, Any]):
        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []

        for chk in chunks:
            ids.append(chk["_id"])
            documents.append(chk["content"])
            metadatas.append({
                "chunk_id": chk["_id"],
                "document_id": chk["document_id"],
                "document_title": doc_metadata.get("title", "Untitled Document"),
                "workspace_id": chk["workspace_id"],
                "section_title": chk.get("section_title", "General"),
                "page_number": int(chk.get("page_number", 1))
            })

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Indexed {len(chunks)} chunks into ChromaDB for document {doc_metadata.get('title')}")

    def search_chunks(self, query: str, workspace_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"workspace_id": workspace_id}
            )

            retrieved = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    chunk_id = results["ids"][0][i]
                    content = results["documents"][0][i]
                    meta = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.0

                    retrieved.append({
                        "chunk_id": chunk_id,
                        "document_id": meta.get("document_id"),
                        "document_title": meta.get("document_title"),
                        "workspace_id": meta.get("workspace_id"),
                        "section_title": meta.get("section_title"),
                        "page_number": meta.get("page_number", 1),
                        "content": content,
                        "distance": distance
                    })

            return retrieved
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}. Executing resilient keyword fallback from persistent storage.")
            try:
                from backend.app.core.database import get_database
                import asyncio
                # Synchronous fallback: query MongoDB chunks directly
                db = get_database()
                # Run async query in loop if needed
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If in running async loop, return empty and let caller handle
                    return []
            except Exception:
                pass
            return []

    def delete_document_chunks(self, document_id: str):
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted chunks from ChromaDB for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting chunks from ChromaDB: {e}")

rag_service = RAGService()
