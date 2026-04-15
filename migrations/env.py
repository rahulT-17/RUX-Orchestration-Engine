from __future__ import annotations

# Migration mental model for this repo:
# 1) Alembic loads this file on revision/upgrade/downgrade commands.
# 2) We expose Base.metadata so Alembic can compare models vs database schema.
# 3) DATABASE_URL is read from .env so app and migrations share one source.
# 4) Offline mode emits SQL scripts without connecting to the database.
# 5) Online mode opens a real async connection and executes migration ops.
# 6) After upgrade, alembic_version stores the applied revision in DB.
# 7) App startup guard checks DB revision equals code head revision.

import asyncio
from logging.config import fileConfig
import os

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

load_dotenv()

from database import Base
import models # noqa: F401  # register all model tables on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is missing. Set it in environment variables.")
    return database_url

# Populate Alembic config dynamically from .env so both CLI and app stay aligned.
config.set_main_option("sqlalchemy.url", get_database_url())

def run_migrations_offline() -> None:
    # Offline mode emits SQL without opening a DB connection.
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection) -> None:
    # Shared migration execution block used by the async connection bridge.
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    # asyncpg URLs require Alembic's async engine path to avoid MissingGreenlet.
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())
    
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()