"""Permission-matrix sweep: all 3 roles x every mutating/restricted endpoint.
Directly verifies FR-003, FR-022, SC-007 (100% correct allow/deny). Requires
a reachable Postgres; skips automatically without one."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.user import User, UserRole

ALL_ROLES = [UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT, UserRole.OFFICE_ADMINISTRATOR]
DELETE_ALLOWED = {UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT}
SENSITIVE_REPORTS_ALLOWED = {UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT}
AUDIT_LOG_ALLOWED = {UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT}


async def _create_user_and_login(client: AsyncClient, db: AsyncSession, *, role: UserRole, email: str) -> str:
    db.add(
        User(full_name="Test User", email=email, password_hash=hash_password("correct-password"), role=role)
    )
    await db.commit()
    response = await client.post("/auth/login", json={"email": email, "password": "correct-password"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_expense_create_allowed_for_every_role(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    for role in ALL_ROLES:
        token = await _create_user_and_login(
            client, db_session, role=role, email=f"{role.value}-{unique_email}"
        )
        category_resp = await client.post(
            "/categories", json={"name": f"Cat-{role.value}-{unique_email[:6]}"}, headers=_headers(token)
        )
        assert category_resp.status_code == 201, role
        category_id = category_resp.json()["id"]

        response = await client.post(
            "/expenses",
            json={"title": "Rent", "amount": "100", "category_id": category_id, "date": "2026-07-01"},
            headers=_headers(token),
        )
        assert response.status_code == 201, f"expense create should be allowed for {role}"


async def test_expense_delete_allowed_only_for_owner_and_accountant(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    for role in ALL_ROLES:
        token = await _create_user_and_login(
            client, db_session, role=role, email=f"{role.value}-{unique_email}"
        )
        category_resp = await client.post(
            "/categories", json={"name": f"Cat-{role.value}-{unique_email[:6]}"}, headers=_headers(token)
        )
        category_id = category_resp.json()["id"]
        create_resp = await client.post(
            "/expenses",
            json={"title": "Rent", "amount": "100", "category_id": category_id, "date": "2026-07-01"},
            headers=_headers(token),
        )
        expense_id = create_resp.json()["id"]

        response = await client.delete(f"/expenses/{expense_id}", headers=_headers(token))
        expected = 204 if role in DELETE_ALLOWED else 403
        assert response.status_code == expected, f"expense delete for {role} expected {expected}"


async def test_income_delete_allowed_only_for_owner_and_accountant(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    for role in ALL_ROLES:
        token = await _create_user_and_login(
            client, db_session, role=role, email=f"{role.value}-{unique_email}"
        )
        create_resp = await client.post(
            "/income",
            json={"source": "Sales", "amount": "100", "date": "2026-07-01"},
            headers=_headers(token),
        )
        income_id = create_resp.json()["id"]

        response = await client.delete(f"/income/{income_id}", headers=_headers(token))
        expected = 204 if role in DELETE_ALLOWED else 403
        assert response.status_code == expected, f"income delete for {role} expected {expected}"


async def test_balance_sheet_and_trial_balance_restricted(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    for role in ALL_ROLES:
        token = await _create_user_and_login(
            client, db_session, role=role, email=f"{role.value}-{unique_email}"
        )
        expected = 200 if role in SENSITIVE_REPORTS_ALLOWED else 403

        bs = await client.get(
            "/reports/balance-sheet?date_from=2026-07-01&date_to=2026-07-31", headers=_headers(token)
        )
        assert bs.status_code == expected, f"balance-sheet for {role} expected {expected}"

        tb = await client.get(
            "/reports/trial-balance?date_from=2026-07-01&date_to=2026-07-31", headers=_headers(token)
        )
        assert tb.status_code == expected, f"trial-balance for {role} expected {expected}"


async def test_profit_and_loss_allowed_for_every_role(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    for role in ALL_ROLES:
        token = await _create_user_and_login(
            client, db_session, role=role, email=f"{role.value}-{unique_email}"
        )
        response = await client.get(
            "/reports/profit-and-loss?date_from=2026-07-01&date_to=2026-07-31", headers=_headers(token)
        )
        assert response.status_code == 200, f"profit-and-loss for {role} expected 200"


async def test_audit_log_restricted_to_owner_and_accountant(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    for role in ALL_ROLES:
        token = await _create_user_and_login(
            client, db_session, role=role, email=f"{role.value}-{unique_email}"
        )
        expected = 200 if role in AUDIT_LOG_ALLOWED else 403
        response = await client.get("/audit-logs", headers=_headers(token))
        assert response.status_code == expected, f"audit-logs for {role} expected {expected}"
