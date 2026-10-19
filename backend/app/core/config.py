import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "CredVista Credit Risk & Portfolio Intelligence"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./credvista.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # Default reporting cutoff (e.g. 2026-10-19)
    DEFAULT_REPORTING_DATE: str = "2026-10-19"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
