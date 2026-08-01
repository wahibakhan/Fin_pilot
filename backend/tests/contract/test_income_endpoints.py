"""Contract tests for /api/v1/income. Require a live DB; skip without one."""

import uuid

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


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_fetch_income(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)

    create_resp = await client.post(
        "/income",
        json={"source": "Consulting Fee", "amount": "5000", "date": "2026-07-01"},
        headers=_auth_headers(token),
    )
    assert create_resp.status_code == 201
    income = create_resp.json()
    assert income["source"] == "Consulting Fee"

    get_resp = await client.get(f"/income/{income['id']}", headers=_auth_headers(token))
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == income["id"]


async def test_create_income_bad_amount_is_422(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)

    response = await client.post(
        "/income",
        json={"source": "Bad", "amount": "0", "date": "2026-07-01"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 422


async def test_create_income_without_auth_is_401(client: AsyncClient):
    response = await client.post(
        "/income", json={"source": "x", "amount": "10", "date": "2026-07-01"}
    )
    assert response.status_code == 401


async def test_delete_income_forbidden_for_office_administrator(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    owner_email = f"owner-{unique_email}"
    admin_email = f"admin-{unique_email}"
    await _create_user(db_session, email=owner_email, role=UserRole.BUSINESS_OWNER)
    await _create_user(db_session, email=admin_email, role=UserRole.OFFICE_ADMINISTRATOR)
    owner_token = await _login(client, email=owner_email)
    admin_token = await _login(client, email=admin_email)

    create_resp = await client.post(
        "/income",
        json={"source": "Invoice", "amount": "1000", "date": "2026-07-01"},
        headers=_auth_headers(owner_token),
    )
    income_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/income/{income_id}", headers=_auth_headers(admin_token))
    assert delete_resp.status_code == 403


async def test_search_income_by_keyword(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)
    marker = uuid.uuid4().hex[:8]

    await client.post(
        "/income",
        json={"source": f"Consulting-{marker}", "amount": "1000", "date": "2026-07-01"},
        headers=_auth_headers(token),
    )
    await client.post(
        "/income",
        json={"source": "Product Sales", "amount": "2000", "date": "2026-07-02"},
        headers=_auth_headers(token),
    )

    response = await client.get(f"/income?q=Consulting-{marker}", headers=_auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["source"] == f"Consulting-{marker}"
