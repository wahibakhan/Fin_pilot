"""Contract test for /api/v1/dashboard/summary. Requires a live DB; skips without one."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.user import User, UserRole


async def _create_user(db: AsyncSession, *, email: str) -> None:
    db.add(
        User(
            full_name="Test User",
            email=email,
            password_hash=hash_password("correct-password"),
            role=UserRole.ACCOUNTANT,
        )
    )
    await db.commit()


async def _login(client: AsyncClient, *, email: str) -> str:
    response = await client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_dashboard_summary_defaults_to_current_month(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email)
    token = await _login(client, email=unique_email)

    response = await client.get("/dashboard/summary", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {
        "total_income",
        "total_expenses",
        "net_profit",
        "monthly_summary",
        "expense_categories",
        "recent_transactions",
    }


async def test_dashboard_summary_with_explicit_period(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email)
    token = await _login(client, email=unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    category_resp = await client.post(
        "/categories", json={"name": f"Rent-{unique_email[:6]}"}, headers=headers
    )
    category_id = category_resp.json()["id"]
    await client.post(
        "/expenses",
        json={"title": "Rent", "amount": "1000", "category_id": category_id, "date": "2026-07-01"},
        headers=headers,
    )

    response = await client.get("/dashboard/summary?period=2026-07", headers=headers)

    assert response.status_code == 200
    assert response.json()["total_expenses"] == "1000.00"


async def test_dashboard_summary_without_auth_is_401(client: AsyncClient):
    response = await client.get("/dashboard/summary")
    assert response.status_code == 401
