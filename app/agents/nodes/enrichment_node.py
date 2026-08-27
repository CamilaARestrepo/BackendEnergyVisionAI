"""
Nodo de enriquecimiento de datos del pipeline LangGraph.

Genera descripción técnica y sugerencias de reutilización para el objeto detectado.
Reutiliza el provider_context cargado en detection_node (sin consulta DB adicional).
"""

from app.agents.state import AgentState
from app.providers.cache import ProviderContext
from app.providers.factory import ProviderFactory
from app.utils.security import security_service
from app.utils.exceptions import ProviderNotConfiguredError, AIInferenceError
from app.utils.logger import logger
from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate


class EnrichmentResult(BaseModel):
    description: str = Field(
        description="Descripción técnica profunda, de 1 o 2 párrafos, del objeto material en sí."
    )
    reuse_suggestions: List[str] = Field(
        description="Lista de sugerencias útiles para reutilizar este objeto en la comunidad energética."
    )


ENRICH_SYSTEM = """Eres un experto en redactar fichas de objetos industriales recuperados.
Genera una descripción técnica profunda y sugiere métodos de upcycling/reutilización viables."""

enrich_prompt = ChatPromptTemplate.from_messages([
    ("system", ENRICH_SYSTEM),
    ("user", "El objeto es: {name}. Material: {material}. Estado: {condition}. "
             "Jerarquía LER: {ler}. Genera el conocimiento final.")
])


def _ctx_from_state(state: AgentState) -> ProviderContext | None:
    """Construye un ProviderContext desde el estado del agente."""
    raw = state.get("provider_context")
    if not raw:
        return None
    return ProviderContext(
        provider_name=raw["provider_name"],
        model_name=raw["model_name"],
        api_key_encrypted=raw.get("api_key_encrypted"),
        base_url=raw.get("base_url"),
    )


async def enrichment_node(state: AgentState) -> dict:
    """Enriquece el objeto con descripción técnica y sugerencias de reutilización."""
    if state.get("errors"):
        return {}

    obj_data = state.get("detected_object")
    waste_data = state.get("waste_classification")

    if not obj_data:
        return {"errors": ["Falta objeto detectado base para enriquecimiento."]}

    ctx = _ctx_from_state(state)
    if ctx is None:
        from app.providers.cache import provider_cache
        ctx = await provider_cache.get()
    if ctx is None:
        return {"errors": ["No hay proveedor de IA activo configurado."]}

    api_key = security_service.decrypt_api_key(ctx.api_key_encrypted)
    provider = ProviderFactory.get_provider(ctx.provider_name)

    try:
        model = provider.get_model(
            ctx.model_name,
            api_key=api_key,
            base_url=ctx.base_url,
            temperature=0.7,
        )
        model_structured = model.with_structured_output(EnrichmentResult)

        msg = enrich_prompt.invoke({
            "name": obj_data.get("name"),
            "material": obj_data.get("material"),
            "condition": obj_data.get("condition"),
            "ler": waste_data.get("waste_hierarchy_level", "") if waste_data else "",
        })

        logger.debug(f"EnrichmentNode: enriqueciendo '{obj_data.get('name')}' vía {ctx.provider_name}")
        result: EnrichmentResult = await model_structured.ainvoke(msg)

        # Enriquecer el objeto detectado con descripción y sugerencias
        obj_data["description"] = result.description
        obj_data["reuse_suggestions"] = result.reuse_suggestions

        return {"detected_object": obj_data}

    except (ProviderNotConfiguredError, AIInferenceError):
        raise
    except Exception as e:
        return {"errors": [f"Error al enriquecer información: {e}"]}
