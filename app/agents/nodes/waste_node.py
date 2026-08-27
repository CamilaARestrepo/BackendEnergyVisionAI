"""
Nodo de clasificación de residuos del pipeline LangGraph.

Delega a WasteChain la invocación del LLM.
Reutiliza el provider_context cargado en detection_node (sin consulta DB adicional).
"""

from app.agents.state import AgentState
from app.chains.waste_chain import waste_chain
from app.providers.cache import ProviderContext
from app.utils.exceptions import ProviderNotConfiguredError, AIInferenceError
from app.utils.logger import logger


def _ctx_from_state(state: AgentState) -> ProviderContext | None:
    """Construye un ProviderContext desde el estado del agente (si está disponible)."""
    raw = state.get("provider_context")
    if not raw:
        return None
    return ProviderContext(
        provider_name=raw["provider_name"],
        model_name=raw["model_name"],
        api_key_encrypted=raw.get("api_key_encrypted"),
        base_url=raw.get("base_url"),
    )


async def waste_node(state: AgentState) -> dict:
    """Clasifica el objeto según la jerarquía de residuos LER europea."""
    if state.get("errors"):
        return {}

    obj_data = state.get("detected_object")
    if not obj_data:
        return {"errors": ["No se ha detectado el objeto para clasificar su residuo."]}

    ctx = _ctx_from_state(state)  # Reutiliza el proveedor cargado en detection_node

    try:
        result = await waste_chain.run(
            object_name=obj_data.get("name", "Desconocido"),
            material=obj_data.get("material", "No evaluado"),
            condition=obj_data.get("condition", "Desconocida"),
            ctx=ctx,
            temperature=0.1,
        )
        return {"waste_classification": result.model_dump()}

    except ProviderNotConfiguredError:
        return {"errors": ["No hay proveedor de IA activo configurado."]}
    except AIInferenceError as e:
        return {"errors": [str(e)]}
    except Exception as e:
        return {"errors": [f"Error inesperado en clasificación LER: {e}"]}
