import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.core.db import Base, get_db
from src.main import app
from src.models import (  # noqa: F401 -- registers models on Base.metadata
    refresh_token,
    user,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """A real Postgres-backed session, rolled back after each test.

    Skips (rather than fails) when no database is reachable, so this suite
    stays runnable in environments without Postgres/Docker available; it
    passes for real once DATABASE_URL points at a live database.
    """
    settings = get_settings()
    # See src/core/db.py — required for pooled endpoints (e.g. Neon's
    # default pooler) that don't support asyncpg's prepared-statement cache.
    engine = create_async_engine(settings.database_url, connect_args={"statement_cache_size": 0})

    try:
        async with engine.connect() as probe:
            await probe.run_sync(lambda _: None)
    except Exception as exc:  # pragma: no cover - environment-dependent
        await engine.dispose()
        pytest.skip(f"No reachable database at {settings.database_url}: {exc}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anonymous_client() -> AsyncIterator[AsyncClient]:
    """A client for endpoints/paths that don't need a real DB (e.g. bad-token 401s)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac


@pytest.fixture
def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@finpilot.demo"
