"""
Caché en memoria del proveedor de IA activo.

Problema que resuelve:
  En el pipeline actual, cada nodo (detection, waste, energy, enrichment)
  abre su propia sesión SQLite para leer el proveedor activo. En un scan
  típico esto genera 4 consultas idénticas a la misma fila.

Solución:
  Un caché singleton en memoria que almacena los datos del proveedor activo.
  Se invalida automáticamente al actualizar la configuración via PUT /settings.

Uso en nodos del agente:
    from app.providers.cache import provider_cache
    ctx = await provider_cache.get()  # {'name': 'anthropic', 'model': '...', ...}
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from app.utils.logger import logger


@dataclass
class ProviderContext:
    """Contexto completo del proveedor activo, listo para uso en nodos."""

    provider_name: str
    model_name: str
    api_key_encrypted: Optional[str]  # Key cifrada con Fernet (se descifra al usar)
    base_url: Optional[str]


class ProviderCache:
    """
    Caché thread-safe en memoria del proveedor de IA activo.

    - `get()`: retorna el contexto cacheado o lo carga desde DB si no existe.
    - `invalidate()`: limpia el caché (llamar tras PUT /settings).
    - TTL de 5 minutos como seguridad adicional.
    """

    _TTL_SECONDS: int = 300  # 5 minutos

    def __init__(self) -> None:
        self._context: Optional[ProviderContext] = None
        self._loaded_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get(self) -> Optional[ProviderContext]:
        """
        Retorna el proveedor activo desde caché o lo carga desde SQLite.

        Returns:
            ProviderContext si hay uno configurado, None si no hay ninguno activo.
        """
        import time

        async with self._lock:
            now = time.monotonic()
            if self._context is not None and (now - self._loaded_at) < self._TTL_SECONDS:
                return self._context

            # Cache miss o TTL expirado — cargar desde DB
            logger.debug("ProviderCache: cargando proveedor activo desde SQLite...")
            ctx = await self._load_from_db()
            self._context = ctx
            self._loaded_at = now

            if ctx:
                logger.debug(f"ProviderCache: proveedor cargado → {ctx.provider_name}/{ctx.model_name}")
            else:
                logger.warning("ProviderCache: no hay proveedor activo configurado.")

            return ctx

    def invalidate(self) -> None:
        """Limpia el caché. Llamar tras cualquier cambio en ai_settings."""
        self._context = None
        self._loaded_at = 0.0
        logger.info("ProviderCache: caché invalidado.")

    async def _load_from_db(self) -> Optional[ProviderContext]:
        """Carga el proveedor activo desde SQLite usando una sesión propia."""
        from app.infrastructure.database.session import AsyncSessionLocal
        from app.infrastructure.repositories.settings_repository import settings_repository

        async with AsyncSessionLocal() as db:
            active = await settings_repository.get_active_provider(db)
            if not active:
                return None
            return ProviderContext(
                provider_name=active.provider_name,
                model_name=active.model_name,
                api_key_encrypted=active.api_key,
                base_url=active.base_url,
            )


# Singleton global — importar desde aquí en todos los nodos y endpoints
provider_cache = ProviderCache()
