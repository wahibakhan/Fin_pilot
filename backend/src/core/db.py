from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings

settings = get_settings()

# statement_cache_size=0 disables asyncpg's client-side prepared-statement
# cache. Required for compatibility with connection poolers running in
# transaction-pooling mode (e.g. Neon's default pooled endpoint, PgBouncer)
# where prepared statements can't be safely reused across pooled
# connections; harmless against a direct, unpooled Postgres connection too.
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"statement_cache_size": 0},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False
)


class Base(DeclarativeBase):
    metadata = MetaData(schema=settings.db_schema)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
