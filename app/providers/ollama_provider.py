from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from app.providers.base import AIProvider

class OllamaProvider(AIProvider):
    @property
    def available_models(self) -> list[str]:
        return ["llava", "llava-phi3", "bakllava"]

    def supports_vision(self) -> bool:
        return True

    def get_model(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs) -> BaseChatModel:
        actual_url = base_url or "http://localhost:11434/v1"
        return ChatOpenAI(model=model_name, api_key="ollama", base_url=actual_url, **kwargs)
