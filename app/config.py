import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TITLE: str = "EnergyVision AI API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Plataforma de Detección Inteligente de Objetos."
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ]

    
    MAX_IMAGE_SIZE_MB: int = 10
    UPLOADS_DIR: str = "./data/uploads"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY_PATH: str = "./data/secret.key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

settings = Settings()
