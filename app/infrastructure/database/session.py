from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
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
