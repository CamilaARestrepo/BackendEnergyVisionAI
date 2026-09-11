"""
Entry point de la aplicación FastAPI — EnergyVision AI.

Responsabilidades:
- Crear instancia FastAPI con metadata completa
- Registrar todos los routers bajo prefijo /api/v1
- Configurar middleware CORS desde settings
- Lifespan: inicializar DB y directorios al arrancar
- Handler global de excepciones de dominio → HTTP responses semánticos
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import EnergyVisionBaseError


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos al arrancar y los libera al cerrar."""
    # Crear directorios requeridos
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)

    # Asegurar que el secret.key de Fernet exista (se genera automáticamente)
    # La instancia de SecurityService se encarga de esto al importarse
    from app.utils.security import security_service  # noqa: F401 — side effect import

    logger.info(f"🌱 Iniciando {settings.TITLE} v{settings.VERSION}")
    logger.info(f"   Database : {settings.DATABASE_URL}")
    logger.info(f"   Uploads  : {settings.UPLOADS_DIR}")
    logger.info(f"   CORS     : {settings.CORS_ORIGINS}")

    yield

    logger.info("🛑 Cerrando EnergyVision AI.")


# ── Importar routers (después de lifespan para evitar import circular) ────────

from app.api.v1.router import api_router  # noqa: E402


# ── Instancia FastAPI ─────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.TITLE,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Middleware CORS ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Handler global de excepciones de dominio ─────────────────────────────────

@app.exception_handler(EnergyVisionBaseError)
async def domain_exception_handler(request: Request, exc: EnergyVisionBaseError) -> JSONResponse:
    """
    Transforma excepciones de dominio en respuestas HTTP con código semántico.

    Permite que las capas de dominio/aplicación lancen excepciones tipadas
    sin conocer los códigos HTTP. El mapeo está en cada clase de excepción.
    """
    logger.warning(
        f"DomainError [{exc.__class__.__name__}] en {request.method} {request.url.path}: "
        f"{exc.message}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Captura excepciones no controladas para evitar exponer stack traces al cliente.
    Siempre registra el error completo en el log del servidor.
    """
    logger.exception(
        f"Excepción no controlada en {request.method} {request.url.path}: {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Consulte los logs para más detalles."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(api_router, prefix="/api/v1")

# Servir archivos de imagen subidos (thumbnails del historial)
app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Endpoint de salud para monitoreo. Retorna estado y versión del sistema."""
    return {"status": "ok", "version": settings.VERSION, "title": settings.TITLE}
