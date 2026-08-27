from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict):
    image_base64: str                               # Imagen en base64 (post-resize, lista para IA)
    image_mime_type: str                            # "image/jpeg" | "image/png" | "image/webp"
    image_hash: Optional[str]                       # SHA-256 de la imagen procesada (idempotencia)
    provider_context: Optional[Dict[str, Any]]      # Contexto del proveedor activo (cargado una vez)
    detected_object: Optional[Dict[str, Any]]       # Resultado del nodo de detección
    waste_classification: Optional[Dict[str, Any]]  # Resultado del nodo de residuos (LER)
    energy_data: Optional[Dict[str, Any]]           # Resultado del nodo energético
    enriched_data: Optional[Dict[str, Any]]         # Datos adicionales del nodo de enriquecimiento
    db_record_id: Optional[int]                     # ID del registro persistido en SQLite
    errors: List[str]                               # Errores acumulados no fatales

