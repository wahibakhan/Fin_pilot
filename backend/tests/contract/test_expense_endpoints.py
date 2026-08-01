"""Contract tests for /api/v1/expenses and /api/v1/categories. Require a live DB; skip without one."""

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


async def test_create_and_fetch_expense(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)

    category_resp = await client.post(
        "/categories", json={"name": f"Rent-{uuid.uuid4().hex[:6]}"}, headers=_auth_headers(token)
    )
    assert category_resp.status_code == 201
    category_id = category_resp.json()["id"]

    create_resp = await client.post(
        "/expenses",
        json={
            "title": "Office Rent",
            "amount": "50000",
            "category_id": category_id,
            "date": "2026-07-01",
            "description": "July rent",
        },
        headers=_auth_headers(token),
    )
    assert create_resp.status_code == 201
    expense = create_resp.json()
    assert expense["title"] == "Office Rent"

    get_resp = await client.get(f"/expenses/{expense['id']}", headers=_auth_headers(token))
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == expense["id"]


async def test_create_expense_bad_amount_is_422(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)
    category_resp = await client.post(
        "/categories", json={"name": f"Rent-{uuid.uuid4().hex[:6]}"}, headers=_auth_headers(token)
    )
    category_id = category_resp.json()["id"]

    # amount <= 0 fails Pydantic's gt=0 constraint at the request-schema layer,
    # so FastAPI rejects it with its standard 422 before the service ever runs.
    response = await client.post(
        "/expenses",
        json={
            "title": "Bad",
            "amount": "0",
            "category_id": category_id,
            "date": "2026-07-01",
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 422


async def test_create_expense_unknown_category_is_400(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)

    # A syntactically valid but nonexistent category passes Pydantic and is
    # rejected by ExpenseService's own validation instead -> 400 (FR-012).
    response = await client.post(
        "/expenses",
        json={
            "title": "Ghost category",
            "amount": "10",
            "category_id": str(uuid.uuid4()),
            "date": "2026-07-01",
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 400
    assert response.json()["field"] == "category_id"


async def test_create_expense_without_auth_is_401(client: AsyncClient):
    response = await client.post(
        "/expenses",
        json={"title": "x", "amount": "10", "category_id": str(uuid.uuid4()), "date": "2026-07-01"},
    )
    assert response.status_code == 401


async def test_delete_expense_forbidden_for_office_administrator(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    owner_email = f"owner-{unique_email}"
    admin_email = f"admin-{unique_email}"
    await _create_user(db_session, email=owner_email, role=UserRole.BUSINESS_OWNER)
    await _create_user(db_session, email=admin_email, role=UserRole.OFFICE_ADMINISTRATOR)
    owner_token = await _login(client, email=owner_email)
    admin_token = await _login(client, email=admin_email)

    category_resp = await client.post(
        "/categories",
        json={"name": f"Rent-{uuid.uuid4().hex[:6]}"},
        headers=_auth_headers(owner_token),
    )
    category_id = category_resp.json()["id"]
    create_resp = await client.post(
        "/expenses",
        json={
            "title": "Rent",
            "amount": "1000",
            "category_id": category_id,
            "date": "2026-07-01",
        },
        headers=_auth_headers(owner_token),
    )
    expense_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/expenses/{expense_id}", headers=_auth_headers(admin_token)
    )
    assert delete_resp.status_code == 403


async def test_category_duplicate_name_is_409(client: AsyncClient, db_session: AsyncSession, unique_email: str):
    await _create_user(db_session, email=unique_email, role=UserRole.ACCOUNTANT)
    token = await _login(client, email=unique_email)
    name = f"Rent-{uuid.uuid4().hex[:6]}"

    first = await client.post("/categories", json={"name": name}, headers=_auth_headers(token))
    assert first.status_code == 201

    second = await client.post("/categories", json={"name": name}, headers=_auth_headers(token))
    assert second.status_code == 409
