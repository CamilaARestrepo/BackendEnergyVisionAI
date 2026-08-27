from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class AISettingsORM(Base):
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_name = Column(String(50), nullable=False, unique=True)
    model_name = Column(String(100), nullable=False)
    api_key = Column(Text, nullable=True) # Cifrada con Fernet
    base_url = Column(String(300), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    extra_config = Column(Text, nullable=True) # JSON
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
