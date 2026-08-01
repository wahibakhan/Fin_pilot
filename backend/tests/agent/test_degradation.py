"""Verifies FR-033/SC-008: when the AI provider is unavailable, /ai/chat
degrades gracefully (503) and every non-AI capability keeps working. Requires
a reachable Postgres for the non-AI assertions; skips automatically without
one."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import src.services.ai_chat_service as ai_chat_service_module
from src.agent.provider import AIProviderError
from src.core.security import hash_password
from src.models.user import User, UserRole


async def _create_user(db: AsyncSession, *, email: str) -> None:
    db.add(
        User(
            full_name="Test User",
            email=email,
            password_hash=hash_password("correct-password"),
            role=UserRole.BUSINESS_OWNER,
        )
    )
    await db.commit()


async def _login(client: AsyncClient, *, email: str) -> str:
    response = await client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _simulate_provider_down(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise():
        raise AIProviderError("OPENAI_API_KEY is not set")

    monkeypatch.setattr(ai_chat_service_module, "get_chat_model", _raise)


async def test_ai_chat_returns_503_when_provider_unavailable(
    client: AsyncClient, db_session: AsyncSession, unique_email: str, monkeypatch: pytest.MonkeyPatch
):
    _simulate_provider_down(monkeypatch)
    await _create_user(db_session, email=unique_email)
    token = await _login(client, email=unique_email)

    response = await client.post(
        "/ai/chat",
        json={"message": "Add office rent 50000 for July"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503


async def test_non_ai_endpoints_unaffected_when_ai_provider_down(
    client: AsyncClient, db_session: AsyncSession, unique_email: str, monkeypatch: pytest.MonkeyPatch
):
    """SC-008: every manual bookkeeping/reporting capability keeps working."""
    _simulate_provider_down(monkeypatch)
    await _create_user(db_session, email=unique_email)
    token = await _login(client, email=unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    category_resp = await client.post(
        "/categories", json={"name": f"Rent-{unique_email[:6]}"}, headers=headers
    )
    assert category_resp.status_code == 201
    category_id = category_resp.json()["id"]

    expense_resp = await client.post(
        "/expenses",
        json={"title": "Rent", "amount": "1000", "category_id": category_id, "date": "2026-07-01"},
        headers=headers,
    )
    assert expense_resp.status_code == 201

    income_resp = await client.post(
        "/income",
        json={"source": "Sales", "amount": "500", "date": "2026-07-01"},
        headers=headers,
    )
    assert income_resp.status_code == 201

    assert (await client.get("/ledger", headers=headers)).status_code == 200
    assert (
        await client.get(
            "/reports/profit-and-loss?date_from=2026-07-01&date_to=2026-07-31", headers=headers
        )
    ).status_code == 200
    assert (await client.get("/dashboard/summary?period=2026-07", headers=headers)).status_code == 200
