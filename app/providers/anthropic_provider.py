from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from app.providers.base import AIProvider

class AnthropicProvider(AIProvider):
    @property
    def available_models(self) -> list[str]:
        return ["claude-opus-4", "claude-sonnet-4", "claude-haiku", "claude-3-5-sonnet-20241022"]

    def supports_vision(self) -> bool:
        return True

    def get_model(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs) -> BaseChatModel:
        if not api_key:
            raise ValueError("Anthropic requiere una API key válida.")
        return ChatAnthropic(model=model_name, api_key=api_key, **kwargs)
