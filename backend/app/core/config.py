from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Vitaminka Assistant"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://vitaminka:vitaminka@localhost:5432/vitaminka_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # LLM provider
    LLM_PROVIDER: str = "cohere"

    # Cohere
    COHERE_API_KEY: str = ""
    COHERE_MODEL: str = "command-r-plus-08-2024"

    # Embeddings + RAG
    COHERE_EMBED_MODEL: str = "embed-multilingual-v3.0"
    CHROMA_PERSIST_DIR: str = "/app/chroma"
    CHROMA_COLLECTION_NAME: str = "products"
    RAG_TOP_K: int = 5
    
    # Admin
    ADMIN_SECRET: str = "change-me-in-production"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-in-production"

    # Catalog auto-sync
    CATALOG_SYNC_INTERVAL_HOURS: int = 6

    # CORS — принимается как строка и разбивается по запятой
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
    
    class Config:
        env_file = ".env"

settings = Settings()
