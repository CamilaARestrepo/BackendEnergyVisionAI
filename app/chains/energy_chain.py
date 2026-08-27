"""
Chain de cálculo de potencial energético.

Encapsula la lógica de:
  1. Resolver el proveedor activo (vía caché compartido)
  2. Invocar el prompt energético con datos del objeto y su clasificación LER
  3. Retornar EnergyResult validado con Pydantic
"""

from typing import Optional

from app.providers.cache import provider_cache, ProviderContext
from app.providers.factory import ProviderFactory
from app.utils.security import security_service
from app.utils.exceptions import ProviderNotConfiguredError, AIInferenceError
from app.utils.logger import logger
from app.prompts.energy_prompt import energy_prompt, EnergyResult


class EnergyChain:
    """
    Chain responsable de estimar el potencial energético de un objeto.

    Calcula:
    - energy_score (0-100): índice de aprovechamiento energético
    - kwh_per_unit: energía recuperable por unidad del objeto
    - kwh_per_kg: energía recuperable por kilogramo de material
    - valorization_methods: lista de vectores de valorización aplicables
    """

    async def run(
        self,
        object_name: str,
        ler_code: str,
        ctx: Optional[ProviderContext] = None,
        temperature: float = 0.2,
    ) -> EnergyResult:
        """
        Calcula el potencial energético del objeto identificado.

        Args:
            object_name: Nombre del objeto detectado.
            ler_code: Código LER asignado por WasteChain (e.g., "16 02 14").
            ctx: Contexto del proveedor pre-cargado. Si None, lo carga del caché.
            temperature: Temperatura del modelo (0.2 para variedad calculada).

        Returns:
            EnergyResult validado con Pydantic.

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
            model_structured = model.with_structured_output(EnergyResult)

            formatted_prompt = energy_prompt.invoke(
                {
                    "detected_object": object_name,
                    "waste_classification": ler_code or "Desconocido",
                }
            )

            logger.debug(
                f"EnergyChain: calculando potencial para '{object_name}' "
                f"(LER={ler_code}) vía {ctx.provider_name}/{ctx.model_name}"
            )
            result: EnergyResult = await model_structured.ainvoke(formatted_prompt)
            logger.info(
                f"EnergyChain: score={result.energy_score}, "
                f"kwh/unit={result.kwh_per_unit}, "
                f"métodos={len(result.valorization_methods)}"
            )
            return result

        except (ProviderNotConfiguredError, AIInferenceError):
            raise
        except Exception as e:
            raise AIInferenceError(
                f"Error al calcular energía vía {ctx.provider_name}: {e}"
            ) from e


# Singleton para uso en nodos
energy_chain = EnergyChain()
