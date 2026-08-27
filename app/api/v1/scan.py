"""
Endpoint POST /api/v1/scan — Orquestador del pipeline de detección multimodal.

Flujo:
1. Recibe imagen vía multipart/form-data
2. Valida tamaño antes de pasar al agente (doble capa de seguridad)
3. Invoca el grafo LangGraph completo de forma asíncrona
4. Retorna el objeto persistido, datos energéticos y metadatos del análisis
"""

import time
import base64

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.object_repository import object_repository
from app.domain.schemas.object_schema import DetectedObjectSchema, EnergyDataSchema
from app.agents.graph import run_vision_pipeline
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import ImageTooLargeError

from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/scan", tags=["Scanner Multimodal"])


class ScanEnergyResponse(BaseModel):
    """Datos energéticos incluidos en la respuesta de un scan."""
    energy_score: Optional[int] = None
    kwh_per_unit: Optional[float] = None
    kwh_per_kg: Optional[float] = None
    valorization_methods: list[str] = []
    waste_hierarchy_level: Optional[str] = None
    ler_code: Optional[str] = None
    is_hazardous: bool = False


class ScanResponse(BaseModel):
    """Respuesta completa del endpoint POST /scan."""
    scan_id: int
    object: DetectedObjectSchema
    energy: Optional[ScanEnergyResponse] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    processing_time_ms: int


@router.post("", response_model=ScanResponse)
async def scan_object(
    image: UploadFile = File(..., description="Imagen física del objeto a analizar."),
    notes: str = Form(None, description="Anotaciones extra opcionales."),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Orquesta el motor de inferencia multimodelo delegando al agente LangGraph.

    El pipeline ejecuta los nodos: validate → detect → waste → energy → enrich → persist.
    """
    start_time = time.time()

    # ── Validación de tamaño (doble capa: middleware + handler) ──────────────
    bytes_data = await image.read()
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024

    if len(bytes_data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"La imagen excede los {settings.MAX_IMAGE_SIZE_MB} MB permitidos.",
        )

    logger.info(
        f"Scan iniciado: archivo='{image.filename}', "
        f"content_type='{image.content_type}', "
        f"tamaño={len(bytes_data):,}B"
    )

    # ── Codificar en base64 y lanzar el pipeline ─────────────────────────────
    b64_img = base64.b64encode(bytes_data).decode("utf-8")
    # Nota: el validate_image_node re-validará con magic bytes y hará resize
    final_state = await run_vision_pipeline(b64_img, image.content_type or "image/jpeg")

    if final_state.get("errors"):
        errors_str = " | ".join(final_state["errors"])
        logger.warning(f"Pipeline falló: {errors_str}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error en inferencia IA: {errors_str}",
        )

    db_id = final_state.get("db_record_id")
    if not db_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El pipeline no retornó un ID de registro válido.",
        )

    # ── Fetch canónico desde DB (mismo schema que GET /objects/{id}) ─────────
    db_obj = await object_repository.get_by_id_with_energy(db, db_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El objeto fue procesado pero no se encontró en la base de datos.",
        )

    processing_time = int((time.time() - start_time) * 1000)
    logger.info(f"Scan completado: id={db_id}, tiempo={processing_time}ms")

    # Mapear energy_data
    energy_response = None
    if db_obj.energy_data:
        ed = db_obj.energy_data
        from app.domain.schemas.object_schema import EnergyDataSchema as _EDS
        import json
        methods = ed.valorization_methods
        if isinstance(methods, str):
            try:
                methods = json.loads(methods)
            except Exception:
                methods = []
        energy_response = ScanEnergyResponse(
            energy_score=ed.energy_score,
            kwh_per_unit=ed.kwh_per_unit,
            kwh_per_kg=ed.kwh_per_kg,
            valorization_methods=methods,
            waste_hierarchy_level=ed.waste_hierarchy_level,
            ler_code=ed.ler_code,
            is_hazardous=ed.is_hazardous,
        )

    return ScanResponse(
        scan_id=db_id,
        object=DetectedObjectSchema.model_validate(db_obj),
        energy=energy_response,
        ai_provider=db_obj.ai_provider,
        ai_model=db_obj.ai_model,
        processing_time_ms=processing_time,
    )
