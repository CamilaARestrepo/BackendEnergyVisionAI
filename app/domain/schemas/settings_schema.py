from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProviderSettingsSchema(BaseModel):
    name: str
    display_name: str
    is_configured: bool
    has_api_key: bool
    available_models: list[str]

class SettingsResponse(BaseModel):
    active_provider: Optional[str] = None
    active_model: Optional[str] = None
    providers: list[ProviderSettingsSchema]

class SettingsUpdate(BaseModel):
    provider_name: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None

class SettingsTestResponse(BaseModel):
    success: bool
    latency_ms: Optional[int] = None
    model_response: Optional[str] = None
    error: Optional[str] = None

class AISettingsSchema(BaseModel):
    id: int
    provider_name: str
    model_name: str
    has_api_key: bool
    base_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
