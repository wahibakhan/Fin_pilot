from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError
from src.models.category import Category
from src.models.expense import Expense
from src.models.income import Income
from src.models.journal_entry import JournalEntry, JournalEntryType

_ZERO = Decimal(0)


def _validate_range(date_from: date, date_to: date) -> None:
    if date_to < date_from:
        raise ValidationError("date_to must not be before date_from", field="date_to")


class ReportService:
    """All seven report types (FR-019). P&L / Monthly Expense / Income /
    Category-wise read directly from expenses+income (flat, period-based).
    Balance Sheet / Trial Balance / Cash Flow read from journal_entries — see
    journal_service.py for the minimal chart-of-accounts rationale."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def profit_and_loss(self, *, date_from: date, date_to: date) -> dict:
        _validate_range(date_from, date_to)

        total_expenses = await self._sum_expenses(date_from, date_to)
        total_income = await self._sum_income(date_from, date_to)

        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_profit": total_income - total_expenses,
        }

    async def balance_sheet(self, *, date_from: date, date_to: date) -> dict:
        """A snapshot AS OF `date_to` (cumulative all-time through that date),
        not a period total. `date_from` is accepted for contract uniformity
        with the other six reports but doesn't affect the figures."""
        _validate_range(date_from, date_to)

        cash = await self._account_balance("Cash", through=date_to)
        expenses = await self._account_balance("Expenses", through=date_to)
        # Revenue is a credit-normal account (its balance grows with credits,
        # e.g. the credit side of an income posting) — unlike Cash/Expenses,
        # which are debit-normal. Using the same debit-credit formula for it
        # would report earned revenue as negative.
        revenue = await self._account_balance("Revenue", through=date_to, normal_balance="credit")
        retained_earnings = revenue - expenses

        return {
            "as_of": date_to,
            "cash": cash,
            "total_assets": cash,
            "retained_earnings": retained_earnings,
            "total_equity": retained_earnings,
        }

    async def trial_balance(self, *, date_from: date, date_to: date) -> dict:
        _validate_range(date_from, date_to)

        stmt = (
            select(
                JournalEntry.account,
                JournalEntry.entry_type,
                func.coalesce(func.sum(JournalEntry.amount), _ZERO).label("total"),
            )
            .where(JournalEntry.entry_date >= date_from, JournalEntry.entry_date <= date_to)
            .group_by(JournalEntry.account, JournalEntry.entry_type)
        )
        result = await self._db.execute(stmt)

        by_account: dict[str, dict[str, Decimal]] = {}
        for account, entry_type, total in result.all():
            by_account.setdefault(account, {"debit": _ZERO, "credit": _ZERO})
            by_account[account][entry_type.value] = total

        accounts = [
            {"account": account, "total_debit": totals["debit"], "total_credit": totals["credit"]}
            for account, totals in sorted(by_account.items())
        ]
        total_debits = sum((a["total_debit"] for a in accounts), _ZERO)
        total_credits = sum((a["total_credit"] for a in accounts), _ZERO)

        return {
            "date_from": date_from,
            "date_to": date_to,
            "accounts": accounts,
            "total_debits": total_debits,
            "total_credits": total_credits,
        }

    async def cash_flow_summary(self, *, date_from: date, date_to: date) -> dict:
        _validate_range(date_from, date_to)

        cash_in = await self._sum_journal(
            account="Cash", entry_type=JournalEntryType.DEBIT, date_from=date_from, date_to=date_to
        )
        cash_out = await self._sum_journal(
            account="Cash", entry_type=JournalEntryType.CREDIT, date_from=date_from, date_to=date_to
        )

        return {
            "date_from": date_from,
            "date_to": date_to,
            "cash_in": cash_in,
            "cash_out": cash_out,
            "net_cash_flow": cash_in - cash_out,
        }

    async def monthly_expense_report(self, *, date_from: date, date_to: date) -> dict:
        _validate_range(date_from, date_to)

        month = func.to_char(Expense.date, "YYYY-MM").label("month")
        stmt = (
            select(month, func.coalesce(func.sum(Expense.amount), _ZERO).label("total"))
            .where(
                Expense.deleted_at.is_(None),
                Expense.date >= date_from,
                Expense.date <= date_to,
            )
            .group_by(month)
            .order_by(month)
        )
        result = await self._db.execute(stmt)
        months = [{"month": m, "total": total} for m, total in result.all()]

        return {
            "date_from": date_from,
            "date_to": date_to,
            "months": months,
            "total_expenses": sum((m["total"] for m in months), _ZERO),
        }

    async def income_report(self, *, date_from: date, date_to: date) -> dict:
        _validate_range(date_from, date_to)

        month = func.to_char(Income.date, "YYYY-MM").label("month")
        stmt = (
            select(month, func.coalesce(func.sum(Income.amount), _ZERO).label("total"))
            .where(
                Income.deleted_at.is_(None),
                Income.date >= date_from,
                Income.date <= date_to,
            )
            .group_by(month)
            .order_by(month)
        )
        result = await self._db.execute(stmt)
        months = [{"month": m, "total": total} for m, total in result.all()]

        return {
            "date_from": date_from,
            "date_to": date_to,
            "months": months,
            "total_income": sum((m["total"] for m in months), _ZERO),
        }

    async def category_wise_expense_report(self, *, date_from: date, date_to: date) -> dict:
        _validate_range(date_from, date_to)

        stmt = (
            select(Category.name, func.coalesce(func.sum(Expense.amount), _ZERO).label("total"))
            .join(Category, Category.id == Expense.category_id)
            .where(
                Expense.deleted_at.is_(None),
                Expense.date >= date_from,
                Expense.date <= date_to,
            )
            .group_by(Category.name)
            .order_by(Category.name)
        )
        result = await self._db.execute(stmt)
        categories = [{"category": name, "total": total} for name, total in result.all()]

        return {
            "date_from": date_from,
            "date_to": date_to,
            "categories": categories,
            "total_expenses": sum((c["total"] for c in categories), _ZERO),
        }

    async def _sum_expenses(self, date_from: date, date_to: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(Expense.amount), _ZERO)).where(
            Expense.deleted_at.is_(None), Expense.date >= date_from, Expense.date <= date_to
        )
        return (await self._db.execute(stmt)).scalar_one()

    async def _sum_income(self, date_from: date, date_to: date) -> Decimal:
        stmt = select(func.coalesce(func.sum(Income.amount), _ZERO)).where(
            Income.deleted_at.is_(None), Income.date >= date_from, Income.date <= date_to
        )
        return (await self._db.execute(stmt)).scalar_one()

    async def _sum_journal(
        self, *, account: str, entry_type: JournalEntryType, date_from: date, date_to: date
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(JournalEntry.amount), _ZERO)).where(
            JournalEntry.account == account,
            JournalEntry.entry_type == entry_type,
            JournalEntry.entry_date >= date_from,
            JournalEntry.entry_date <= date_to,
        )
        return (await self._db.execute(stmt)).scalar_one()

    async def _account_balance(
        self, account: str, *, through: date, normal_balance: str = "debit"
    ) -> Decimal:
        debit = await self._sum_journal_through(account, JournalEntryType.DEBIT, through)
        credit = await self._sum_journal_through(account, JournalEntryType.CREDIT, through)
        if normal_balance == "credit":
            return credit - debit
        return debit - credit

    async def _sum_journal_through(
        self, account: str, entry_type: JournalEntryType, through: date
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(JournalEntry.amount), _ZERO)).where(
            JournalEntry.account == account,
            JournalEntry.entry_type == entry_type,
            JournalEntry.entry_date <= through,
        )
        return (await self._db.execute(stmt)).scalar_one()
