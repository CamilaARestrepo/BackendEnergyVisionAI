"""
Nodo de cálculo de potencial energético del pipeline LangGraph.

Delega a EnergyChain la invocación del LLM.
Reutiliza el provider_context cargado en detection_node (sin consulta DB adicional).
"""

from app.agents.state import AgentState
from app.chains.energy_chain import energy_chain
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


async def energy_node(state: AgentState) -> dict:
    """Calcula el potencial energético del objeto clasificado."""
    if state.get("errors"):
        return {}

    obj_data = state.get("detected_object")
    waste_data = state.get("waste_classification")
    if not obj_data or not waste_data:
        return {"errors": ["Falta información de contexto base para calcular energía."]}

    ctx = _ctx_from_state(state)  # Reutiliza el proveedor cargado en detection_node

    try:
        result = await energy_chain.run(
            object_name=obj_data.get("name", "Desconocido"),
            ler_code=waste_data.get("ler_code", "Desconocido"),
            ctx=ctx,
            temperature=0.2,
        )
        return {"energy_data": result.model_dump()}

    except ProviderNotConfiguredError:
        return {"errors": ["No hay proveedor de IA activo configurado."]}
    except AIInferenceError as e:
        return {"errors": [str(e)]}
    except Exception as e:
        return {"errors": [f"Error inesperado en cálculo energético: {e}"]}
