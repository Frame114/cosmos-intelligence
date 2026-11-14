"""Database dependencies for request-scoped SQLAlchemy transactions."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import FeatureUnavailableError


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped transaction for API route dependencies."""

    factory: async_sessionmaker[AsyncSession] | None = getattr(
        request.app.state, "db_sessions", None
    )
    if factory is None:
        raise FeatureUnavailableError("database_unconfigured", "The database is not configured.")
    async with factory() as session:
        async with session.begin():
            yield session
