"""
Endpoints de configuración del proveedor de IA.

GET  /api/v1/settings       — Lista proveedores y activo actual
PUT  /api/v1/settings       — Guarda/actualiza configuración y activa el provider
POST /api/v1/settings/test  — Test REAL de conexión al proveedor (no es un mock)
"""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db_session
from app.domain.schemas.settings_schema import (
    SettingsResponse,
    ProviderSettingsSchema,
    SettingsUpdate,
    SettingsTestResponse,
)
from app.infrastructure.repositories.settings_repository import settings_repository
from app.providers.factory import ProviderFactory
from app.providers.cache import provider_cache
from app.utils.security import security_service
from app.utils.logger import logger

router = APIRouter(prefix="/settings", tags=["Settings"])

PROVIDERS_METADATA = [
    {
        "name": "openai",
        "display_name": "OpenAI",
        "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    },
    {
        "name": "anthropic",
        "display_name": "Anthropic Claude",
        "available_models": [
            "claude-opus-4-20251001",
            "claude-sonnet-4-20251001",
            "claude-haiku-4-20251001",
            "claude-3-5-sonnet-20241022",
        ],
    },
    {
        "name": "gemini",
        "display_name": "Google Gemini",
        "available_models": [
            "gemini-3-flash-preview",
            "gemini-3.1-flash-lite-preview",
        ],
    },
    {
        "name": "ollama",
        "display_name": "Ollama (Local)",
        "available_models": ["llava", "llava-phi3", "bakllava"],
    },
]


@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db_session)):
    """Retorna la configuración actual ofuscando la clave privada."""
    db_providers = await settings_repository.list(db)
    provider_map = {p.provider_name: p for p in db_providers}
    active = await settings_repository.get_active_provider(db)

    providers_list = []
    for pm in PROVIDERS_METADATA:
        db_p = provider_map.get(pm["name"])
        configured = db_p is not None
        # Ollama no requiere API key — siempre se considera configurado si existe
        has_key = bool(db_p and db_p.api_key) if pm["name"] != "ollama" else True

        providers_list.append(
            ProviderSettingsSchema(
                name=pm["name"],
                display_name=pm["display_name"],
                is_configured=configured,
                has_api_key=has_key,
                available_models=pm["available_models"],
            )
        )

    return SettingsResponse(
        active_provider=active.provider_name if active else None,
        active_model=active.model_name if active else None,
        providers=providers_list,
    )


@router.put("", status_code=status.HTTP_200_OK)
async def update_settings(
    settings_data: SettingsUpdate, db: AsyncSession = Depends(get_db_session)
):
    """Actualiza o crea la configuración del proveedor y lo activa."""
    valid_names = [p["name"] for p in PROVIDERS_METADATA]
    if settings_data.provider_name not in valid_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proveedor '{settings_data.provider_name}' desconocido. "
                   f"Opciones válidas: {', '.join(valid_names)}",
        )

    await settings_repository.update_or_create(db, settings_data)
    await settings_repository.set_active_provider(db, settings_data.provider_name)

    # Invalidar el caché para que el próximo scan use la nueva configuración
    provider_cache.invalidate()

    logger.info(
        f"Settings actualizados: provider={settings_data.provider_name}, "
        f"model={settings_data.model_name}"
    )
    return {
        "status": "success",
        "message": f"Proveedor '{settings_data.provider_name}' configurado y activado.",
    }


@router.post("/test", response_model=SettingsTestResponse)
async def test_provider_connection(
    settings_data: SettingsUpdate, db: AsyncSession = Depends(get_db_session)
):
    """
    Prueba la conexión REAL al proveedor de IA especificado.

    Envía un mensaje de prueba mínimo al modelo y mide la latencia.
    No guarda ningún dato. Retorna éxito/error con latencia en ms.
    """
    # Validar proveedor
    valid_names = [p["name"] for p in PROVIDERS_METADATA]
    if settings_data.provider_name not in valid_names:
        return SettingsTestResponse(
            success=False,
            error=f"Proveedor '{settings_data.provider_name}' desconocido.",
        )

    # Validar que Ollama tiene URL base
    if settings_data.provider_name == "ollama" and not settings_data.base_url:
        return SettingsTestResponse(
            success=False,
            error="Ollama requiere una URL base (e.g., http://localhost:11434).",
        )

    # Resolver la API key: usar la del payload o la que está en BD si ya fue guardada
    api_key = settings_data.api_key
    if not api_key and settings_data.provider_name != "ollama":
        existing = await settings_repository.list(db)
        for p in existing:
            if p.provider_name == settings_data.provider_name and p.api_key:
                api_key = security_service.decrypt_api_key(p.api_key)
                break

        if not api_key:
            return SettingsTestResponse(
                success=False,
                error="No se proporcionó clave API y no hay una guardada para este proveedor.",
            )

    # Hacer el test real
    try:
        provider = ProviderFactory.get_provider(settings_data.provider_name)
        model = provider.get_model(
            settings_data.model_name,
            api_key=api_key,
            base_url=settings_data.base_url,
            temperature=0.0,
            max_tokens=10,  # Respuesta mínima para minimizar costos
        )

        start = time.monotonic()
        # Mensaje de prueba mínimo (no multimodal — solo texto para el test)
        response = await model.ainvoke("Respond with OK only.")
        latency_ms = int((time.monotonic() - start) * 1000)

        # Algunos modelos (ej. Gemini preview) devuelven content como lista de bloques
        raw_content = response.content if hasattr(response, "content") else "OK"
        if isinstance(raw_content, list):
            # Extraer texto del primer bloque disponible
            raw_content = next(
                (block.get("text", "") if isinstance(block, dict) else str(block)
                 for block in raw_content),
                "OK",
            )
        model_response = str(raw_content)[:100]

        logger.info(
            f"Test de proveedor exitoso: {settings_data.provider_name}/"
            f"{settings_data.model_name} → {latency_ms}ms"
        )

        return SettingsTestResponse(
            success=True,
            latency_ms=latency_ms,
            model_response=model_response,
        )

    except Exception as e:
        error_msg = str(e)
        # Simplificar mensajes de error comunes para el usuario
        if "401" in error_msg or "Unauthorized" in error_msg or "invalid_api_key" in error_msg.lower():
            error_msg = "Clave API inválida o no autorizada."
        elif "404" in error_msg or "model_not_found" in error_msg.lower():
            error_msg = f"Modelo '{settings_data.model_name}' no encontrado. Verifica el nombre."
        elif "429" in error_msg or "rate_limit" in error_msg.lower():
            error_msg = "Límite de tasa alcanzado. Intenta en unos segundos."
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            error_msg = f"No se pudo conectar al proveedor. Verifica la URL y la conexión."

        logger.warning(
            f"Test de proveedor fallido: {settings_data.provider_name}/"
            f"{settings_data.model_name} → {e}"
        )

        return SettingsTestResponse(success=False, error=error_msg)
