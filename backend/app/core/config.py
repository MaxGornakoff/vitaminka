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
    
    # CORS — принимается как строка и разбивается по запятой
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
    
    class Config:
        env_file = ".env"

settings = Settings()
