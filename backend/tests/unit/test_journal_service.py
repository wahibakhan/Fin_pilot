"""JournalService integration tests. Require a reachable Postgres; skip automatically without one."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.journal_entry import (
    JournalEntry,
    JournalEntryType,
    JournalReferenceType,
)
from src.services.journal_service import JournalService


async def _entries_for(db: AsyncSession, reference_id: uuid.UUID) -> list[JournalEntry]:
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.reference_id == reference_id)
    )
    return list(result.scalars().all())


async def test_post_expense_creates_one_debit_and_one_credit(db_session: AsyncSession):
    expense_id = uuid.uuid4()

    await JournalService(db_session).post_expense(
        expense_id=expense_id, amount=Decimal("100.00"), entry_date=date(2026, 7, 1)
    )
    await db_session.commit()

    entries = await _entries_for(db_session, expense_id)
    assert len(entries) == 2
    debit = next(e for e in entries if e.entry_type == JournalEntryType.DEBIT)
    credit = next(e for e in entries if e.entry_type == JournalEntryType.CREDIT)
    assert debit.account == "Expenses"
    assert credit.account == "Cash"
    assert debit.amount == credit.amount == Decimal("100.00")
    assert debit.reference_type == JournalReferenceType.EXPENSE


async def test_reverse_expense_swaps_debit_and_credit_accounts(db_session: AsyncSession):
    expense_id = uuid.uuid4()

    await JournalService(db_session).post_expense(
        expense_id=expense_id, amount=Decimal("50.00"), entry_date=date(2026, 7, 1), direction="reverse"
    )
    await db_session.commit()

    entries = await _entries_for(db_session, expense_id)
    debit = next(e for e in entries if e.entry_type == JournalEntryType.DEBIT)
    credit = next(e for e in entries if e.entry_type == JournalEntryType.CREDIT)
    assert debit.account == "Cash"
    assert credit.account == "Expenses"


async def test_post_income_creates_debit_cash_credit_revenue(db_session: AsyncSession):
    income_id = uuid.uuid4()

    await JournalService(db_session).post_income(
        income_id=income_id, amount=Decimal("500.00"), entry_date=date(2026, 7, 1)
    )
    await db_session.commit()

    entries = await _entries_for(db_session, income_id)
    debit = next(e for e in entries if e.entry_type == JournalEntryType.DEBIT)
    credit = next(e for e in entries if e.entry_type == JournalEntryType.CREDIT)
    assert debit.account == "Cash"
    assert credit.account == "Revenue"
    assert debit.reference_type == JournalReferenceType.INCOME
