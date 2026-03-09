"""
Database Configuration - SQLAlchemy Async Engine
Industry standard: Async PostgreSQL with proper connection pooling
Reference: CVision/backend/app/core/database.py
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.config import settings


# Create async engine
# Neon PostgreSQL optimizations:
# - pool_pre_ping: Verify connections before use (handles scale-to-zero)
# - pool_size: 5 connections (Neon free tier limit)
# - max_overflow: 10 (burst capacity)
# - pool_recycle: 3600 (1 hour - handles Neon connection timeouts)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# Base class for all models
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models
    Industry standard: Common base with metadata
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions
    Industry standard: FastAPI dependency pattern
    Usage: @router.get("/endpoint")
           async def endpoint(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
