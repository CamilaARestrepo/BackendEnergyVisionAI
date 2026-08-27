from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class DetectedObjectORM(Base):
    __tablename__ = "detected_objects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_path = Column(String(500), nullable=False)
    image_hash = Column(String(64), unique=True)
    object_name = Column(String(200), nullable=False)
    object_category = Column(String(100), nullable=False, index=True)
    object_material = Column(String(200), nullable=True)
    object_brand = Column(String(100), nullable=True)
    object_condition = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True) # CHECK(0-1) done at app level or alembic
    description = Column(Text, nullable=True)
    reuse_suggestions = Column(Text, nullable=True) # JSON array stringified
    ai_provider = Column(String(50), nullable=False, index=True)
    ai_model = Column(String(100), nullable=False)
    
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    energy_data = relationship("EnergyDataORM", back_populates="detected_object", uselist=False, cascade="all, delete-orphan")
