"""Contract tests for /api/v1/reports/*. Require a live DB; skip without one."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.user import User, UserRole


async def _create_user(db: AsyncSession, *, email: str, role: UserRole) -> None:
    db.add(
        User(
            full_name="Test User",
            email=email,
            password_hash=hash_password("correct-password"),
            role=role,
        )
    )
    await db.commit()


async def _login(client: AsyncClient, *, email: str) -> str:
    response = await client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_profit_and_loss_accessible_to_office_administrator(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email, role=UserRole.OFFICE_ADMINISTRATOR)
    token = await _login(client, email=unique_email)

    response = await client.get(
        "/reports/profit-and-loss?date_from=2026-07-01&date_to=2026-07-31",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


async def test_balance_sheet_forbidden_for_office_administrator(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email, role=UserRole.OFFICE_ADMINISTRATOR)
    token = await _login(client, email=unique_email)

    response = await client.get(
        "/reports/balance-sheet?date_from=2026-07-01&date_to=2026-07-31",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_trial_balance_forbidden_for_office_administrator(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email, role=UserRole.OFFICE_ADMINISTRATOR)
    token = await _login(client, email=unique_email)

    response = await client.get(
        "/reports/trial-balance?date_from=2026-07-01&date_to=2026-07-31",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_balance_sheet_accessible_to_accountant(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)

    response = await client.get(
        "/reports/balance-sheet?date_from=2026-07-01&date_to=2026-07-31",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


async def test_invalid_date_range_is_400(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)

    response = await client.get(
        "/reports/profit-and-loss?date_from=2026-07-31&date_to=2026-07-01",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


async def test_reports_without_auth_is_401(client: AsyncClient):
    response = await client.get("/reports/profit-and-loss?date_from=2026-07-01&date_to=2026-07-31")
    assert response.status_code == 401
