from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.nodes import (
    validate_image_node,
    detection_node,
    waste_node,
    energy_node,
    enrichment_node,
    persist_node
)

builder = StateGraph(AgentState)

# Registrar Nodos
builder.add_node("validate_image", validate_image_node)
builder.add_node("detection", detection_node)
builder.add_node("waste", waste_node)
builder.add_node("energy", energy_node)
builder.add_node("enrichment", enrichment_node)
builder.add_node("persist", persist_node)

# Función de enrutamiento condicional post-validator
def should_continue_validation(state: AgentState):
    if state.get("errors"):
        return END
    return "detection"

# Función de enrutamiento condicional post-detection
def should_continue_detection(state: AgentState):
    if state.get("errors"):
        return END
    return "waste"

# Enlaces (Edges)
builder.add_edge(START, "validate_image")
builder.add_conditional_edges("validate_image", should_continue_validation, {
    "detection": "detection",
    END: END
})

builder.add_conditional_edges("detection", should_continue_detection, {
    "waste": "waste",
    END: END
})

# Happy path residual sequence
builder.add_edge("waste", "energy")
builder.add_edge("energy", "enrichment")
builder.add_edge("enrichment", "persist")
builder.add_edge("persist", END)

# Compilar grafo
vision_graph = builder.compile()

async def run_vision_pipeline(image_base64: str, mime_type: str) -> dict:
    """Ejecuta el pipeline completo y retorna el estado final o lanza exp."""
    initial_state = {
        "image_base64": image_base64,
        "image_mime_type": mime_type,
        "errors": []
    }
    
    # Run async invocation from graph
    final_state = await vision_graph.ainvoke(initial_state)
    return final_state
