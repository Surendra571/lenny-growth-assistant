import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base
import app.models  # Ensure all ORM models are registered

# Primary database engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

_is_fallback_sqlite = False


async def init_db() -> bool:
    """
    Initialize database schema. If configured PostgreSQL database is unreachable,
    gracefully switch to local SQLite persistence to maintain full application functionality.
    """
    global engine, AsyncSessionLocal, _is_fallback_sqlite

    # Test configured database
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database connected and verified schemas on: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
        return True
    except Exception as e:
        logger.warning(f"Configured PostgreSQL unavailable ({e}). Initializing local SQLite fallback persistence...")
        
        # Fallback to local SQLite database
        fallback_url = "sqlite+aiosqlite:///lenny_assistant.db"
        engine = create_async_engine(
            fallback_url,
            echo=False,
        )
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        _is_fallback_sqlite = True

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Local SQLite fallback persistence initialized successfully ({fallback_url}).")
        return True


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an asynchronous database session
    with automatic rollback on error and clean teardown.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """
    Quick connectivity health check for active database.
    """
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False
