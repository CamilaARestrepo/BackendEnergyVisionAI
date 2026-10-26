from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine import make_url, URL
from app.config import settings


def _force_async_driver(raw_url: str) -> URL:
    """
    Fuerza el driver asyncpg y desactiva el caché de sentencias preparadas.

    - Evita ``ModuleNotFoundError: psycopg`` cuando la URL llega como
      ``postgresql://`` en lugar de ``postgresql+asyncpg://``.
    - Evita ``DuplicatePreparedStatementError`` de pgbouncer (Supabase
      transaction pooler, puerto 6543), que no soporta prepared statements.
    """
    url = make_url(raw_url)
    if url.drivername in ("postgres", "postgresql", "postgresql+psycopg", "postgresql+psycopg2"):
        url = url.set(drivername="postgresql+asyncpg")
    # pgbouncer en modo transaction/statement no soporta prepared statements.
    url = url.update_query_dict({"prepared_statement_cache_size": "0"})
    return url


engine = create_async_engine(
    _force_async_driver(settings.DATABASE_URL),
    echo=(settings.LOG_LEVEL == "DEBUG"),
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={
        # Supabase exige SSL; asyncpg usa el parámetro "ssl" (no "sslmode").
        "ssl": "require",
        # Desactiva el caché interno de prepared statements de asyncpg
        # (requerido cuando se usa pgbouncer/pooler en modo transaction).
        "statement_cache_size": 0,
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db_session():
    """Dependency para Inyección en FastAPI."""
    async with AsyncSessionLocal() as session:
        yield session
