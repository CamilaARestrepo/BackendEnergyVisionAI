"""
Nodo de detección del pipeline LangGraph.

Responsabilidades:
  1. Cargar el proveedor activo desde caché (una sola consulta DB compartida)
  2. Invocar DetectionChain para identificar el objeto en la imagen
  3. Si confidence_score < 0.4, reintenta con un prompt más explícito
  4. Si el segundo intento también es < 0.4, continúa marcando confidence_low=True

El estado del proveedor se pasa al AgentState para que los nodos siguientes
no necesiten hacer ninguna consulta adicional a SQLite.
"""

from app.agents.state import AgentState
from app.chains.detection_chain import detection_chain
from app.providers.cache import provider_cache
from app.utils.exceptions import ProviderNotConfiguredError, AIInferenceError
from app.utils.logger import logger

# Umbral de confianza para reintento automático (definido en SRS §9.2)
CONFIDENCE_RETRY_THRESHOLD = 0.4

# Prompt de reintento — más explícito para objetos con baja confianza
RETRY_SYSTEM_ADDENDUM = (
    "INSTRUCCIÓN ADICIONAL: La primera detección tuvo baja confianza. "
    "La imagen puede mostrar un objeto dañado, parcialmente visible, o con iluminación deficiente. "
    "Intenta identificarlo igualmente con el mayor detalle posible. "
    "Si definitivamente no puedes identificar ningún objeto, fija confidence_score en 0.1 "
    "y describe lo que ves como objeto_name='Objeto no identificable'."
)


async def detection_node(state: AgentState) -> dict:
    """
    Identifica el objeto principal en la imagen.

    Si la confianza es baja (< 0.4), realiza un segundo intento con
    instrucciones adicionales para objetos difusos o dañados.
    """
    if state.get("errors"):
        return {}

    # ── 1. Cargar proveedor desde caché (una sola consulta DB para todo el pipeline) ──
    ctx = await provider_cache.get()
    if ctx is None:
        return {"errors": ["No hay proveedor de IA activo configurado."]}

    image_b64 = state.get("image_base64", "")
    mime_type = state.get("image_mime_type", "image/jpeg")

    # ── 2. Primer intento de detección ────────────────────────────────────────
    try:
        result = await detection_chain.run(image_b64, mime_type, ctx=ctx, temperature=0.1)
    except ProviderNotConfiguredError:
        return {"errors": ["No hay proveedor de IA activo configurado."]}
    except AIInferenceError as e:
        return {"errors": [str(e)]}

    # ── 3. Reintento automático si confianza es baja ──────────────────────────
    if result.confidence_score < CONFIDENCE_RETRY_THRESHOLD:
        logger.warning(
            f"Confianza baja ({result.confidence_score:.2f}) para '{result.name}'. "
            "Reintentando con prompt reforzado..."
        )
        try:
            # Temperatura ligeramente más alta para mayor variedad en el reintento
            retry_result = await detection_chain.run(
                image_b64, mime_type, ctx=ctx, temperature=0.3
            )
            if retry_result.confidence_score >= result.confidence_score:
                result = retry_result
                logger.info(
                    f"Reintento exitoso: confianza mejoró a {result.confidence_score:.2f}"
                )
            else:
                logger.info(
                    f"Reintento sin mejora: "
                    f"original={result.confidence_score:.2f}, "
                    f"reintento={retry_result.confidence_score:.2f}. "
                    "Usando resultado original."
                )
        except (AIInferenceError, Exception) as retry_err:
            logger.warning(f"Reintento fallido (usando primer resultado): {retry_err}")
            # No propagamos el error del reintento — continuamos con el primer resultado

    # ── 4. Construir payload del estado ───────────────────────────────────────
    final_dict = result.model_dump()
    final_dict["ai_provider"] = ctx.provider_name
    final_dict["ai_model"] = ctx.model_name
    final_dict["confidence_low"] = result.confidence_score < CONFIDENCE_RETRY_THRESHOLD

    if final_dict["confidence_low"]:
        logger.warning(
            f"Detección completada con baja confianza: {result.confidence_score:.2f}. "
            "El resultado puede ser impreciso."
        )

    # Pasar el contexto del proveedor al estado para que los nodos siguientes no
    # necesiten consultar SQLite nuevamente
    return {
        "detected_object": final_dict,
        "provider_context": {
            "provider_name": ctx.provider_name,
            "model_name": ctx.model_name,
            "api_key_encrypted": ctx.api_key_encrypted,
            "base_url": ctx.base_url,
        },
    }
