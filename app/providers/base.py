from abc import ABC, abstractmethod
from typing import Optional, Any
from langchain_core.language_models import BaseChatModel

class AIProvider(ABC):
    @abstractmethod
    def get_model(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs) -> BaseChatModel:
        """Instancia el modelo de chat LangChain configurado."""
        pass

    @abstractmethod
    def supports_vision(self) -> bool:
        """Determina si soporta imágenes (vision)."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """Lista de modelos validos soportados."""
        pass
