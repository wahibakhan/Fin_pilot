"""Contract tests for /api/v1/audit-logs. Requires a live DB; skips without one."""

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


async def test_audit_logs_forbidden_for_office_administrator(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email, role=UserRole.OFFICE_ADMINISTRATOR)
    token = await _login(client, email=unique_email)

    response = await client.get("/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


async def test_audit_logs_accessible_to_business_owner_and_lists_expense_creation(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email, role=UserRole.BUSINESS_OWNER)
    token = await _login(client, email=unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    category_resp = await client.post(
        "/categories", json={"name": f"Rent-{unique_email[:6]}"}, headers=headers
    )
    category_id = category_resp.json()["id"]
    create_resp = await client.post(
        "/expenses",
        json={"title": "Rent", "amount": "1000", "category_id": category_id, "date": "2026-07-01"},
        headers=headers,
    )
    expense_id = create_resp.json()["id"]

    response = await client.get(
        f"/audit-logs?entity_type=expense&entity_id={expense_id}", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["action"] == "create"
    assert body["items"][0]["entity_id"] == expense_id


async def test_audit_logs_without_auth_is_401(client: AsyncClient):
    response = await client.get("/audit-logs")
    assert response.status_code == 401
