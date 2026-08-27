from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
import json

class EnergyDataSchema(BaseModel):
    id: int
    object_id: int
    energy_score: Optional[int] = Field(None, ge=0, le=100)
    kwh_per_unit: Optional[float] = None
    kwh_per_kg: Optional[float] = None
    valorization_methods: List[str] = Field(default_factory=list)
    waste_hierarchy_level: Optional[str] = None
    ler_code: Optional[str] = None
    is_hazardous: bool = False
    processing_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("valorization_methods", mode="before")
    @classmethod
    def parse_valorization_methods(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return [v] if v else []
        return v or []


class DetectedObjectBase(BaseModel):
    object_name: str
    object_category: str
    object_material: Optional[str] = None
    object_brand: Optional[str] = None
    object_condition: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    description: Optional[str] = None
    reuse_suggestions: List[str] = Field(default_factory=list)
    ai_provider: str
    ai_model: str

    @field_validator("reuse_suggestions", mode="before")
    @classmethod
    def parse_reuse_suggestions(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return [v] if v else []
        return v or []


class DetectedObjectCreate(DetectedObjectBase):
    image_path: str
    image_hash: str


class DetectedObjectUpdate(BaseModel):
    notes: Optional[str] = None
    reuse_suggestions: Optional[List[str]] = None


class DetectedObjectSchema(DetectedObjectBase):
    id: int
    image_path: str
    image_hash: str
    created_at: datetime
    updated_at: datetime
    energy_data: Optional[EnergyDataSchema] = None

    model_config = ConfigDict(from_attributes=True)
