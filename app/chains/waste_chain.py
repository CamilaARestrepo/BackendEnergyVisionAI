"""
Chain de clasificación de residuos según jerarquía LER europea.

Encapsula la lógica de:
  1. Resolver el proveedor activo (vía caché compartido)
  2. Invocar el prompt de clasificación LER con los datos del objeto
  3. Retornar WasteResult validado con Pydantic
"""

from typing import Optional

from app.providers.cache import provider_cache, ProviderContext
from app.providers.factory import ProviderFactory
from app.utils.security import security_service
from app.utils.exceptions import ProviderNotConfiguredError, AIInferenceError
from app.utils.logger import logger
from app.prompts.waste_prompt import waste_prompt, WasteResult


class WasteChain:
    """
    Chain responsable de clasificar el objeto según la jerarquía de residuos LER europea.

    Determina:
    - Nivel jerárquico: reutilización → reparación → reciclaje → valorización → disposición
    - Código LER de 6 dígitos
    - Peligrosidad (boolean)
    - Notas de tratamiento recomendado
    """

    async def run(
        self,
        object_name: str,
        material: str,
        condition: str,
        ctx: Optional[ProviderContext] = None,
        temperature: float = 0.1,
    ) -> WasteResult:
        """
        Clasifica el residuo del objeto identificado.

        Args:
            object_name: Nombre del objeto detectado.
            material: Material principal del objeto.
            condition: Estado del objeto (funcional / dañado / obsoleto / desconocido).
            ctx: Contexto del proveedor pre-cargado. Si None, lo carga del caché.
            temperature: Temperatura del modelo (0.1 para clasificación determinista).

        Returns:
            WasteResult validado con Pydantic.

        Raises:
            ProviderNotConfiguredError: Si no hay proveedor activo.
            AIInferenceError: Si el modelo falla.
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
            model_structured = model.with_structured_output(WasteResult)

            formatted_prompt = waste_prompt.invoke(
                {
                    "detected_object": object_name,
                    "material": material or "No evaluado",
                    "condition": condition or "Desconocida",
                }
            )

            logger.debug(
                f"WasteChain: clasificando LER para '{object_name}' "
                f"vía {ctx.provider_name}/{ctx.model_name}"
            )
            result: WasteResult = await model_structured.ainvoke(formatted_prompt)
            logger.info(
                f"WasteChain: LER={result.ler_code}, "
                f"nivel={result.waste_hierarchy_level}, "
                f"peligroso={result.is_hazardous}"
            )
            return result

        except (ProviderNotConfiguredError, AIInferenceError):
            raise
        except Exception as e:
            raise AIInferenceError(
                f"Error al clasificar LER vía {ctx.provider_name}: {e}"
            ) from e


# Singleton para uso en nodos
waste_chain = WasteChain()
