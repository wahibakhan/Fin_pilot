"""AuthService integration tests. Require a reachable Postgres (see conftest.db_session);
they skip automatically when none is available."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AuthenticationError
from src.core.security import hash_password
from src.models.user import User, UserRole
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.services.auth_service import AuthService


async def _make_user(db: AsyncSession, *, email: str, password: str, role: UserRole = UserRole.ACCOUNTANT) -> User:
    user = User(
        full_name="Test User",
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.flush()
    await db.commit()
    return user


async def test_login_success_returns_token_pair(db_session: AsyncSession, unique_email: str):
    await _make_user(db_session, email=unique_email, password="correct-password")

    tokens = await AuthService(db_session).login(email=unique_email, password="correct-password")

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"


async def test_login_wrong_password_raises(db_session: AsyncSession, unique_email: str):
    await _make_user(db_session, email=unique_email, password="correct-password")

    with pytest.raises(AuthenticationError):
        await AuthService(db_session).login(email=unique_email, password="wrong-password")


async def test_login_unknown_email_raises(db_session: AsyncSession, unique_email: str):
    with pytest.raises(AuthenticationError):
        await AuthService(db_session).login(email=unique_email, password="anything")


async def test_login_inactive_user_raises(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email, password="correct-password")
    user.is_active = False
    await db_session.commit()

    with pytest.raises(AuthenticationError):
        await AuthService(db_session).login(email=unique_email, password="correct-password")


async def test_refresh_rotates_token_and_revokes_old_one(db_session: AsyncSession, unique_email: str):
    await _make_user(db_session, email=unique_email, password="correct-password")
    service = AuthService(db_session)
    first_pair = await service.login(email=unique_email, password="correct-password")

    second_pair = await service.refresh(refresh_token=first_pair.refresh_token)

    assert second_pair.refresh_token != first_pair.refresh_token

    # The original refresh token must now be revoked (rotation) and unusable.
    with pytest.raises(AuthenticationError):
        await service.refresh(refresh_token=first_pair.refresh_token)


async def test_refresh_with_garbage_token_raises(db_session: AsyncSession):
    with pytest.raises(AuthenticationError):
        await AuthService(db_session).refresh(refresh_token="not-a-real-token")


async def test_logout_revokes_refresh_token(db_session: AsyncSession, unique_email: str):
    await _make_user(db_session, email=unique_email, password="correct-password")
    service = AuthService(db_session)
    tokens = await service.login(email=unique_email, password="correct-password")

    await service.logout(refresh_token=tokens.refresh_token)

    record = await RefreshTokenRepository(db_session).get_active_by_token(tokens.refresh_token)
    assert record is None

    with pytest.raises(AuthenticationError):
        await service.refresh(refresh_token=tokens.refresh_token)
