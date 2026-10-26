import os
from pydantic import field_validator
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
    # Caché RAG por hash: si la imagen ya fue analizada, responde desde BD
    # sin volver a invocar las 4 llamadas LLM (ahorro de tokens/costo).
    ENABLE_IMAGE_CACHE: bool = True
    # Clave Fernet (base64) para descifrar api_key. Si se define, tiene
    # prioridad sobre SECRET_KEY_PATH. Útil en entornos efímeros (Railway).
    SECRET_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _force_asyncpg_driver(cls, v: str) -> str:
        """
        Garantiza que la URL use el driver asyncpg.

        Supabase (y otros proveedores) entregan la cadena como
        ``postgresql://`` o ``postgres://``. Si se deja así, SQLAlchemy
        intenta cargar psycopg por defecto y falla con
        ``ModuleNotFoundError: No module named 'psycopg'``.
        """
        v = v.strip().strip('"').strip("'")
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

settings = Settings()
