import uuid
from datetime import date
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.journal_entry import (
    JournalEntry,
    JournalEntryType,
    JournalReferenceType,
)

Direction = Literal["post", "reverse"]

# Deliberately minimal chart of accounts (see plan.md §1.3 / research.md) — no
# per-category ledger accounts. Category-level detail is served directly from
# expenses/income (category_wise_expense_report), not from journal_entries.
_CASH = "Cash"
_EXPENSES = "Expenses"
_REVENUE = "Revenue"


class JournalService:
    """Posts/reverses the debit+credit pair backing an expense or income
    mutation (FR: Balance Sheet / Trial Balance / Cash Flow accuracy).

    Reversing rather than editing/deleting existing rows keeps journal_entries
    an append-only history, consistent with how audit_log_entries works.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def post_expense(
        self, *, expense_id: uuid.UUID, amount, entry_date: date, direction: Direction = "post"
    ) -> None:
        debit_account, credit_account = _EXPENSES, _CASH
        if direction == "reverse":
            debit_account, credit_account = credit_account, debit_account
        await self._post_pair(
            reference_type=JournalReferenceType.EXPENSE,
            reference_id=expense_id,
            debit_account=debit_account,
            credit_account=credit_account,
            amount=amount,
            entry_date=entry_date,
        )

    async def post_income(
        self, *, income_id: uuid.UUID, amount, entry_date: date, direction: Direction = "post"
    ) -> None:
        debit_account, credit_account = _CASH, _REVENUE
        if direction == "reverse":
            debit_account, credit_account = credit_account, debit_account
        await self._post_pair(
            reference_type=JournalReferenceType.INCOME,
            reference_id=income_id,
            debit_account=debit_account,
            credit_account=credit_account,
            amount=amount,
            entry_date=entry_date,
        )

    async def _post_pair(
        self,
        *,
        reference_type: JournalReferenceType,
        reference_id: uuid.UUID,
        debit_account: str,
        credit_account: str,
        amount,
        entry_date: date,
    ) -> None:
        self._db.add(
            JournalEntry(
                reference_type=reference_type,
                reference_id=reference_id,
                entry_type=JournalEntryType.DEBIT,
                account=debit_account,
                amount=amount,
                entry_date=entry_date,
            )
        )
        self._db.add(
            JournalEntry(
                reference_type=reference_type,
                reference_id=reference_id,
                entry_type=JournalEntryType.CREDIT,
                account=credit_account,
                amount=amount,
                entry_date=entry_date,
            )
        )
        await self._db.flush()
