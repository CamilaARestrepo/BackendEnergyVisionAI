from app.providers.base import AIProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider
from app.utils.exceptions import ProviderNotFoundError, MissingAPIKeyError


class ProviderFactory:
    _providers = {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "gemini": GeminiProvider(),
        "ollama": OllamaProvider(),
    }

    @classmethod
    def get_provider(cls, name: str) -> AIProvider:
        provider = cls._providers.get(name.lower())
        if not provider:
            raise ProviderNotFoundError(f"Provider {name} not found.")
        return provider
