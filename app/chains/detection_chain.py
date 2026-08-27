"""
Chain de detección de objetos vía visión multimodal.

Encapsula la lógica de:
  1. Resolver el proveedor activo (vía caché)
  2. Instanciar el modelo con structured output
  3. Invocar el prompt de detección con la imagen en base64
  4. Retornar DetectionResult validado por Pydantic

Diseñada para ser instanciada como dependencia por detection_node y
retry_detection_node, manteniendo los nodos como coordinadores ligeros.
"""

from typing import Optional

from app.providers.cache import provider_cache, ProviderContext
from app.providers.factory import ProviderFactory
from app.utils.security import security_service
from app.utils.exceptions import ProviderNotConfiguredError, AIInferenceError
from app.utils.logger import logger
from app.prompts.detection_prompt import detection_prompt, DetectionResult


class DetectionChain:
    """
    Chain responsable de identificar el objeto principal en una imagen.

    Separa la responsabilidad de invocar el LLM del nodo del grafo,
    facilitando el testing con mocks y el reintento con prompts alternativos.
    """

    async def run(
        self,
        image_base64: str,
        mime_type: str,
        ctx: Optional[ProviderContext] = None,
        temperature: float = 0.1,
    ) -> DetectionResult:
        """
        Invoca el modelo de visión y retorna un DetectionResult estructurado.

        Args:
            image_base64: Imagen codificada en base64 (ya redimensionada).
            mime_type: MIME type real de la imagen (e.g., "image/jpeg").
            ctx: Contexto del proveedor pre-cargado. Si None, lo carga del caché.
            temperature: Temperatura del modelo (0.1 para detección precisa).

        Returns:
            DetectionResult validado con Pydantic.

        Raises:
            ProviderNotConfiguredError: Si no hay proveedor activo.
            AIInferenceError: Si el modelo falla al procesar la imagen.
        """
        if ctx is None:
            ctx = await provider_cache.get()
        if ctx is None:
            raise ProviderNotConfiguredError()

        api_key = security_service.decrypt_api_key(ctx.api_key_encrypted)
        provider = ProviderFactory.get_provider(ctx.provider_name)

        try:
            model = provider.get_model(
                ctx.model_name,
                api_key=api_key,
                base_url=ctx.base_url,
                temperature=temperature,
            )
            model_structured = model.with_structured_output(DetectionResult)

            # Normalizar formato de mime a lo que espera el prompt (jpeg no jpg)
            fmt = mime_type.split("/")[-1]
            if fmt == "jpg":
                fmt = "jpeg"

            formatted_prompt = detection_prompt.invoke(
                {"mime_type": f"image/{fmt}", "image_base64": image_base64}
            )

            logger.debug(
                f"DetectionChain: invocando {ctx.provider_name}/{ctx.model_name} "
                f"(temp={temperature})"
            )
            result: DetectionResult = await model_structured.ainvoke(formatted_prompt)
            logger.info(
                f"DetectionChain: detectado '{result.name}' "
                f"(confidence={result.confidence_score:.2f})"
            )
            return result

        except (ProviderNotConfiguredError, AIInferenceError):
            raise
        except Exception as e:
            raise AIInferenceError(
                f"Error del modelo {ctx.provider_name}/{ctx.model_name} en detección: {e}"
            ) from e


# Instancia singleton para uso en nodos
detection_chain = DetectionChain()
