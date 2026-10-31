import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api import auth, workspaces, documents, chats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("enterprise_assistant")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Enterprise Knowledge Assistant Backend...")
    await init_db()
    logger.info("Database and vector store initialized.")
    yield
    logger.info("Shutting down Enterprise Knowledge Assistant Backend...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Enterprise Knowledge Assistant with grounded RAG, citations, and RBAC.",
    version="1.0.0",
    lifespan=lifespan
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "### Enterprise Knowledge Assistant REST API\n\n"
            "**Role-Based Access Control (RBAC)**:\n"
            "- Pass the `X-User-Id` header with either:\n"
            "  - `usr_alice` (Staff Platform Engineer — access to Engineering & Executive workspaces)\n"
            "  - `usr_bob` (Contractor — access strictly to Engineering workspace)\n"
            "- Alternatively, authenticate via `/api/auth/login` and pass `Authorization: Bearer <token>`."
        ),
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "UserIdHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-User-Id",
            "description": "Seeded user identifier: 'usr_alice' or 'usr_bob'"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"UserIdHeader": []}, {"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api
app.include_router(auth.router, prefix="/api")
app.include_router(workspaces.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chats.router, prefix="/api")

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "ai_provider": settings.AI_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
