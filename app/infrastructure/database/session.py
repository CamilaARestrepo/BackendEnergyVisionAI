from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine import make_url
from app.config import settings


def _force_async_driver(raw_url: str) -> str:
    """
    Fuerza el driver asyncpg sin importar cómo venga la URL.

    Evita el error ``ModuleNotFoundError: No module named 'psycopg'``
    cuando el proveedor (Railway/Supabase) entrega la cadena como
    ``postgresql://`` en lugar de ``postgresql+asyncpg://``.
    """
    url = make_url(raw_url)
    if url.drivername in ("postgres", "postgresql", "postgresql+psycopg", "postgresql+psycopg2"):
        url = url.set(drivername="postgresql+asyncpg")
    return url.render_as_string(hide_password=False)


engine = create_async_engine(
    _force_async_driver(settings.DATABASE_URL),
    echo=(settings.LOG_LEVEL == "DEBUG"),
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
    # Supabase exige SSL; asyncpg usa el parámetro "ssl" (no "sslmode").
    connect_args={"ssl": "require"},
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
