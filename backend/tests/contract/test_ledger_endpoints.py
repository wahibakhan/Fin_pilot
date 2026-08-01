"""Contract test for /api/v1/ledger. Requires a live DB; skips without one."""

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


async def test_ledger_lists_combined_expense_and_income(
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
        json={
            "title": "Office Rent",
            "amount": "1000",
            "category_id": category_id,
            "date": "2026-07-01",
        },
        headers=headers,
    )
    await client.post(
        "/income",
        json={"source": "Consulting Fee", "amount": "5000", "date": "2026-07-03"},
        headers=headers,
    )

    response = await client.get("/ledger", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    types = {item["type"] for item in body["items"]}
    assert types == {"expense", "income"}


async def test_ledger_without_auth_is_401(client: AsyncClient):
    response = await client.get("/ledger")
    assert response.status_code == 401
