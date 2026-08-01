"""Contract tests for /api/v1/ai/chat and /api/v1/ai/interactions/{id}/confirm|reject,
exercised at the HTTP layer (not the graph directly, unlike the golden-transcript
suite) — this is what proves AIChatService/the ai_interactions table actually
wire the graph up correctly end to end. Requires a reachable Postgres; skips
automatically without one.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import src.services.ai_chat_service as ai_chat_service_module
from src.core.security import hash_password
from src.models.category import Category, CategoryType
from src.models.user import User, UserRole
from tests.agent.fakes import FakeToolCallingModel


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


def _patch_model(monkeypatch: pytest.MonkeyPatch, tool_call: dict) -> None:
    monkeypatch.setattr(
        ai_chat_service_module, "get_chat_model", lambda: FakeToolCallingModel(tool_call)
    )


async def test_chat_read_only_intent_answers_immediately(
    client: AsyncClient, db_session: AsyncSession, unique_email: str, monkeypatch: pytest.MonkeyPatch
):
    _patch_model(
        monkeypatch,
        {"name": "NetProfitQuery", "args": {"date_from": "2026-07-01", "date_to": "2026-07-31"}, "id": "1"},
    )
    token = await _create_user_and_login(client, db_session, email=unique_email)

    response = await client.post(
        "/ai/chat",
        json={"message": "What was our net profit?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["proposed_action"] is None
    assert "interaction_id" in body


async def test_chat_write_intent_proposes_then_confirm_applies_it(
    client: AsyncClient, db_session: AsyncSession, unique_email: str, monkeypatch: pytest.MonkeyPatch
):
    db_session.add(Category(name=f"Rent-{unique_email[:6]}", type=CategoryType.EXPENSE))
    await db_session.commit()

    _patch_model(
        monkeypatch,
        {
            "name": "AddExpense",
            "args": {
                "title": "Office Rent",
                "amount": 50000,
                "category": f"Rent-{unique_email[:6]}",
                "date": "2026-07-01",
            },
            "id": "1",
        },
    )
    token = await _create_user_and_login(client, db_session, email=unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    chat_resp = await client.post(
        "/ai/chat", json={"message": "Add office rent 50000 for July"}, headers=headers
    )
    assert chat_resp.status_code == 200
    chat_body = chat_resp.json()
    assert chat_body["status"] == "proposed"
    assert chat_body["proposed_action"]["title"] == "Office Rent"
    interaction_id = chat_body["interaction_id"]

    confirm_resp = await client.post(f"/ai/interactions/{interaction_id}/confirm", headers=headers)
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"

    expenses_resp = await client.get("/expenses", headers=headers)
    titles = [e["title"] for e in expenses_resp.json()["items"]]
    assert "Office Rent" in titles


async def test_confirming_an_already_resolved_interaction_is_409(
    client: AsyncClient, db_session: AsyncSession, unique_email: str, monkeypatch: pytest.MonkeyPatch
):
    db_session.add(Category(name=f"Rent-{unique_email[:6]}", type=CategoryType.EXPENSE))
    await db_session.commit()

    _patch_model(
        monkeypatch,
        {
            "name": "AddExpense",
            "args": {
                "title": "Office Rent",
                "amount": 50000,
                "category": f"Rent-{unique_email[:6]}",
                "date": "2026-07-01",
            },
            "id": "1",
        },
    )
    token = await _create_user_and_login(client, db_session, email=unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    chat_resp = await client.post(
        "/ai/chat", json={"message": "Add office rent 50000 for July"}, headers=headers
    )
    interaction_id = chat_resp.json()["interaction_id"]

    first_confirm = await client.post(f"/ai/interactions/{interaction_id}/confirm", headers=headers)
    assert first_confirm.status_code == 200

    second_confirm = await client.post(f"/ai/interactions/{interaction_id}/confirm", headers=headers)
    assert second_confirm.status_code == 409


async def test_rejecting_a_proposal_leaves_no_expense_created(
    client: AsyncClient, db_session: AsyncSession, unique_email: str, monkeypatch: pytest.MonkeyPatch
):
    db_session.add(Category(name=f"Rent-{unique_email[:6]}", type=CategoryType.EXPENSE))
    await db_session.commit()

    _patch_model(
        monkeypatch,
        {
            "name": "AddExpense",
            "args": {
                "title": "Should Not Exist",
                "amount": 999,
                "category": f"Rent-{unique_email[:6]}",
                "date": "2026-07-01",
            },
            "id": "1",
        },
    )
    token = await _create_user_and_login(client, db_session, email=unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    chat_resp = await client.post(
        "/ai/chat", json={"message": "Add a 999 expense"}, headers=headers
    )
    interaction_id = chat_resp.json()["interaction_id"]

    reject_resp = await client.post(f"/ai/interactions/{interaction_id}/reject", headers=headers)
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    expenses_resp = await client.get("/expenses", headers=headers)
    titles = [e["title"] for e in expenses_resp.json()["items"]]
    assert "Should Not Exist" not in titles


async def test_chat_without_auth_is_401(client: AsyncClient):
    response = await client.post("/ai/chat", json={"message": "hello"})
    assert response.status_code == 401
