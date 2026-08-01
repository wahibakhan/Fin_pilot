import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.core.config import get_settings
from src.core.db import Base

# Import every model module so Base.metadata is fully populated before
# autogenerate compares it against the live schema.
from src.models import (  # noqa: F401
    ai_interaction,
    audit_log,
    category,
    expense,
    income,
    journal_entry,
    refresh_token,
    user,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=settings.db_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    if settings.db_schema != "public":
        # Neon's pooler silently drops the asyncpg `search_path` startup
        # parameter, so it must be set as a regular statement instead. Safe
        # here because the whole migration run is one transaction on one
        # connection (see run_async_migrations/begin_transaction below) —
        # unlike app-runtime queries, this isn't at risk of a pooler handing
        # a later statement to a different backend connection mid-run.
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.db_schema}"'))
        connection.execute(text(f'SET search_path TO "{settings.db_schema}"'))
        # Commit this setup statement as its own top-level transaction.
        # Otherwise it leaves an uncommitted autobegin transaction open,
        # forcing Alembic's own begin_transaction() below to nest as a
        # SAVEPOINT rather than a real commit — everything (schema, tables,
        # alembic_version) then gets silently rolled back when the
        # connection closes at the end of the run, with no error raised.
        connection.commit()

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=settings.db_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # See src/core/db.py — required for pooled endpoints (e.g. Neon's
        # default pooler) that don't support asyncpg's prepared-statement cache.
        connect_args={"statement_cache_size": 0},
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
