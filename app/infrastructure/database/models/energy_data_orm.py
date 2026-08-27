from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class EnergyDataORM(Base):
    __tablename__ = "energy_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_id = Column(Integer, ForeignKey("detected_objects.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    energy_score = Column(Integer, nullable=True) # 0-100
    kwh_per_unit = Column(Float, nullable=True)
    kwh_per_kg = Column(Float, nullable=True)
    valorization_methods = Column(Text, nullable=False) # JSON array stringified
    waste_hierarchy_level = Column(String(50), nullable=True)
    ler_code = Column(String(20), nullable=True)
    is_hazardous = Column(Boolean, nullable=True, default=False)
    processing_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=func.now())

    detected_object = relationship("DetectedObjectORM", back_populates="energy_data")
