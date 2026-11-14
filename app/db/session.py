"""Async SQLAlchemy engine and request-scoped session helpers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str, **engine_options: object) -> AsyncEngine:
    """Create an async engine without logging or exposing the connection URL."""

    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        **engine_options,
    )


def get_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return a session factory whose sessions do not expire after commit."""

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a short-lived transaction and roll it back on failure."""

    async with factory() as session:
        async with session.begin():
            yield session
