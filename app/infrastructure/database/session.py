from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=(settings.LOG_LEVEL == "DEBUG"),
    future=True,
    # SQLite isolation adjustments
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
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
