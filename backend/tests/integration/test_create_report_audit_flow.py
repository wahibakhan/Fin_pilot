"""End-to-end, HTTP-level: create expense+income -> confirm the report
reflects them -> confirm the ledger reflects them -> confirm each mutation
produced an audit log row (SC-004). Requires a reachable Postgres; skips
automatically without one."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.user import User, UserRole


async def _create_user_and_login(client: AsyncClient, db: AsyncSession, *, email: str) -> str:
    db.add(
        User(
            full_name="Test User",
            email=email,
            password_hash=hash_password("correct-password"),
            role=UserRole.BUSINESS_OWNER,
        )
    )
    await db.commit()
    response = await client.post("/auth/login", json={"email": email, "password": "correct-password"})
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_create_flows_through_to_report_ledger_and_audit_log(
    client: AsyncClient, db_session: AsyncSession, unique_email: str
):
    token = await _create_user_and_login(client, db_session, email=unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    category_resp = await client.post(
        "/categories", json={"name": f"Rent-{unique_email[:6]}"}, headers=headers
    )
    assert category_resp.status_code == 201
    category_id = category_resp.json()["id"]

    expense_resp = await client.post(
        "/expenses",
        json={"title": "Office Rent", "amount": "1000", "category_id": category_id, "date": "2026-07-01"},
        headers=headers,
    )
    assert expense_resp.status_code == 201
    expense_id = expense_resp.json()["id"]

    income_resp = await client.post(
        "/income",
        json={"source": "Consulting", "amount": "5000", "date": "2026-07-02"},
        headers=headers,
    )
    assert income_resp.status_code == 201
    income_id = income_resp.json()["id"]

    # Report reflects both.
    pnl_resp = await client.get(
        "/reports/profit-and-loss?date_from=2026-07-01&date_to=2026-07-31", headers=headers
    )
    assert pnl_resp.status_code == 200
    pnl = pnl_resp.json()
    assert pnl["total_income"] == "5000.00"
    assert pnl["total_expenses"] == "1000.00"
    assert pnl["net_profit"] == "4000.00"

    # Ledger reflects both.
    ledger_resp = await client.get("/ledger", headers=headers)
    assert ledger_resp.status_code == 200
    ledger_ids = {item["id"] for item in ledger_resp.json()["items"]}
    assert expense_id in ledger_ids
    assert income_id in ledger_ids

    # Every mutation produced exactly one audit log row (SC-004).
    expense_audit = await client.get(
        f"/audit-logs?entity_type=expense&entity_id={expense_id}", headers=headers
    )
    assert expense_audit.status_code == 200
    assert expense_audit.json()["total"] == 1
    assert expense_audit.json()["items"][0]["action"] == "create"

    income_audit = await client.get(
        f"/audit-logs?entity_type=income&entity_id={income_id}", headers=headers
    )
    assert income_audit.status_code == 200
    assert income_audit.json()["total"] == 1
    assert income_audit.json()["items"][0]["action"] == "create"

    # Deleting also produces its own audit row.
    delete_resp = await client.delete(f"/expenses/{expense_id}", headers=headers)
    assert delete_resp.status_code == 204

    expense_audit_after_delete = await client.get(
        f"/audit-logs?entity_type=expense&entity_id={expense_id}", headers=headers
    )
    actions = {item["action"] for item in expense_audit_after_delete.json()["items"]}
    assert actions == {"create", "delete"}
