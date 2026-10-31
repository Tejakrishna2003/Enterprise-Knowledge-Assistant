import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Knowledge Assistant"
    APP_ENV: str = "development"  # "development" | "production" | "test"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]

    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "knowledge_assistant"
    ALLOW_IN_MEMORY_FALLBACK: bool = False  # Strict real database persistence

    # Storage
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage")
    DOCUMENTS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "documents")
    CHROMA_PERSIST_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "chroma_db")

    # Upload Constraints
    MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB max file size

    # AI Configuration
    # Supported: "gemini" | "openai" | "mock"
    AI_PROVIDER: str = "gemini"
    AI_MODEL_NAME: str = "gemini-3.5-flash-lite"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Auth & JWT
    JWT_SECRET_KEY: str = "enterprise_knowledge_assistant_super_secret_jwt_key_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
