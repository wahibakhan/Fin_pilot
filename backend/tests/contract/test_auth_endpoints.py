"""Contract tests for /api/v1/auth/*, matching contracts/openapi.yaml.

The 401-on-bad-token cases don't need a database (decode_token fails before
any DB lookup), so they run against `anonymous_client`. Everything else needs
a real Postgres via `client`/`db_session` and skips automatically without one.
"""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.user import User, UserRole


async def _create_user(db: AsyncSession, *, email: str, password: str) -> None:
    db.add(
        User(
            full_name="Ada Accountant",
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ACCOUNTANT,
        )
    )
    await db.commit()


async def test_me_without_token_is_401(anonymous_client: AsyncClient):
    response = await anonymous_client.get("/auth/me")

    assert response.status_code == 401


async def test_me_with_garbage_token_is_401(anonymous_client: AsyncClient):
    response = await anonymous_client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


async def test_login_with_bad_credentials_is_401(client: AsyncClient):
    # Needs a live DB (the lookup runs even for a nonexistent email), so this
    # uses `client`, which skips automatically without one.
    response = await client.post(
        "/auth/login", json={"email": "nobody@finpilot.demo", "password": "whatever"}
    )

    assert response.status_code == 401


async def test_login_missing_fields_is_422(anonymous_client: AsyncClient):
    response = await anonymous_client.post("/auth/login", json={"email": "a@b.com"})

    assert response.status_code == 422


async def test_full_login_me_logout_flow(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, password="correct-password")

    login_response = await client.post(
        "/auth/login", json={"email": unique_email, "password": "correct-password"}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert set(tokens) >= {"access_token", "refresh_token", "token_type"}

    me_response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == unique_email.lower()

    logout_response = await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 204

    refresh_response = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 401


async def test_login_then_refresh_rotates_tokens(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, password="correct-password")

    login_response = await client.post(
        "/auth/login", json={"email": unique_email, "password": "correct-password"}
    )
    first_tokens = login_response.json()

    refresh_response = await client.post(
        "/auth/refresh", json={"refresh_token": first_tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 200
    second_tokens = refresh_response.json()
    assert second_tokens["refresh_token"] != first_tokens["refresh_token"]
