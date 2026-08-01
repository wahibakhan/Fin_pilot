"""IncomeService integration tests. Require a reachable Postgres; skip automatically without one."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.models.audit_log import AuditAction, AuditEntityType, AuditLogEntry
from src.models.user import User, UserRole
from src.services.income_service import IncomeService


async def _make_user(db: AsyncSession, *, role: UserRole, email: str) -> User:
    user = User(full_name="Test User", email=email, password_hash="x", role=role)
    db.add(user)
    await db.flush()
    return user


async def test_create_income_success(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    await db_session.commit()

    income = await IncomeService(db_session).create_income(
        actor=owner, source="Client Invoice", amount="5000", date=date(2026, 7, 1)
    )

    assert income.source == "Client Invoice"
    assert str(income.amount) == "5000.00"
    assert income.created_by == owner.id


async def test_create_income_rejects_non_positive_amount(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    await db_session.commit()

    with pytest.raises(ValidationError) as exc_info:
        await IncomeService(db_session).create_income(
            actor=owner, source="Bad", amount="-5", date=date(2026, 7, 1)
        )
    assert exc_info.value.field == "amount"


async def test_create_income_rejects_blank_source(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    await db_session.commit()

    with pytest.raises(ValidationError) as exc_info:
        await IncomeService(db_session).create_income(
            actor=owner, source="   ", amount="10", date=date(2026, 7, 1)
        )
    assert exc_info.value.field == "source"


async def test_update_income_changes_persist(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    await db_session.commit()
    service = IncomeService(db_session)
    income = await service.create_income(
        actor=owner, source="Invoice", amount="1000", date=date(2026, 7, 1)
    )

    updated = await service.update_income(actor=owner, income_id=income.id, amount="1500")

    assert str(updated.amount) == "1500.00"
    assert updated.source == "Invoice"


async def test_delete_income_forbidden_for_office_administrator(
    db_session: AsyncSession, unique_email: str
):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=f"owner-{unique_email}")
    admin = await _make_user(
        db_session, role=UserRole.OFFICE_ADMINISTRATOR, email=f"admin-{unique_email}"
    )
    await db_session.commit()
    service = IncomeService(db_session)
    income = await service.create_income(
        actor=owner, source="Invoice", amount="1000", date=date(2026, 7, 1)
    )

    with pytest.raises(PermissionDeniedError):
        await service.delete_income(actor=admin, income_id=income.id)


async def test_delete_income_allowed_for_accountant_and_hides_it(
    db_session: AsyncSession, unique_email: str
):
    accountant = await _make_user(db_session, role=UserRole.ACCOUNTANT, email=unique_email)
    await db_session.commit()
    service = IncomeService(db_session)
    income = await service.create_income(
        actor=accountant, source="Invoice", amount="1000", date=date(2026, 7, 1)
    )

    await service.delete_income(actor=accountant, income_id=income.id)

    with pytest.raises(NotFoundError):
        await service.get_income(income.id)


async def test_list_income_filters_by_keyword(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    await db_session.commit()
    service = IncomeService(db_session)
    await service.create_income(
        actor=owner, source="Consulting Fee", amount="1000", date=date(2026, 7, 1)
    )
    await service.create_income(
        actor=owner, source="Product Sales", amount="2000", date=date(2026, 7, 2)
    )

    items, total = await service.list_income(q="consulting")
    assert total == 1
    assert items[0].source == "Consulting Fee"


async def test_create_income_writes_audit_log_entry(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    await db_session.commit()

    income = await IncomeService(db_session).create_income(
        actor=owner, source="Invoice", amount="500", date=date(2026, 7, 1)
    )

    result = await db_session.execute(
        select(AuditLogEntry).where(
            AuditLogEntry.entity_type == AuditEntityType.INCOME,
            AuditLogEntry.entity_id == income.id,
        )
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    assert entries[0].action == AuditAction.CREATE
    assert entries[0].after_state["source"] == "Invoice"
