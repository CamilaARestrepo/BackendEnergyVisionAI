from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from app.providers.base import AIProvider

class OpenAIProvider(AIProvider):
    @property
    def available_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]

    def supports_vision(self) -> bool:
        return True

    def get_model(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs) -> BaseChatModel:
        if not api_key:
            raise ValueError("OpenAI requiere una API key válida.")
        return ChatOpenAI(model=model_name, api_key=api_key, **kwargs)
