from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from app.providers.base import AIProvider

class GeminiProvider(AIProvider):
    @property
    def available_models(self) -> list[str]:
        return ["gemini-3-flash-preview", "gemini-3.1-flash-lite-preview"]

    def supports_vision(self) -> bool:
        return True

    def get_model(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs) -> BaseChatModel:
        if not api_key:
            raise ValueError("Google Gemini requiere una API key válida.")
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, **kwargs)
