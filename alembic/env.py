"""Alembic environment for asynchronous PostgreSQL migrations."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from typing import Any

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.db.models  # noqa: F401 - register all model metadata for migrations
from alembic import context
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configuration() -> dict[str, Any]:
    section = dict(config.get_section(config.config_ini_section) or {})
    database_url = os.environ.get("DATABASE_URL")
    database_url_file = os.environ.get("DATABASE_URL_FILE")
    if database_url_file:
        with open(database_url_file, encoding="utf-8") as secret_file:
            database_url = secret_file.read().strip()
    database_url = database_url or section.get("sqlalchemy.url")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be configured for database migrations.")
    section["sqlalchemy.url"] = database_url
    return section


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Render SQL without opening a connection or printing configured secrets."""

    section = _configuration()
    context.configure(
        url=section["sqlalchemy.url"],
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations(section: dict[str, Any]) -> None:
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run a migration against the configured PostgreSQL database."""

    section = _configuration()
    asyncio.run(_run_async_migrations(section))


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
