from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import QueuePool
from app.config import settings
from typing import AsyncGenerator


# Create async engine with Neon-specific optimizations
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=QueuePool,
    pool_size=5,  # Neon free tier limit
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # 30 minutes
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "statement_timeout": "30000",  # 30 seconds
            "idle_in_transaction_session_timeout": "10000"
        }
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
