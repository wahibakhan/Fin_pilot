from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ledger_service import LedgerService
from src.services.report_service import ReportService

_ZERO = Decimal(0)


class DashboardService:
    """Composes existing report/ledger queries into one summary payload
    (FR-005–FR-008) — deliberately reuses ReportService/LedgerService rather
    than re-deriving totals, so the dashboard can never disagree with the
    Reports or Ledger pages for the same period."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._reports = ReportService(db)
        self._ledger = LedgerService(db)

    async def get_summary(
        self, *, date_from: date, date_to: date, recent_limit: int = 10
    ) -> dict:
        pnl = await self._reports.profit_and_loss(date_from=date_from, date_to=date_to)
        monthly_expenses = await self._reports.monthly_expense_report(
            date_from=date_from, date_to=date_to
        )
        monthly_income = await self._reports.income_report(date_from=date_from, date_to=date_to)
        category_breakdown = await self._reports.category_wise_expense_report(
            date_from=date_from, date_to=date_to
        )
        recent_items, _ = await self._ledger.list_ledger(
            sort_by="date", sort_dir="desc", page=1, page_size=recent_limit
        )

        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_income": pnl["total_income"],
            "total_expenses": pnl["total_expenses"],
            "net_profit": pnl["net_profit"],
            "monthly_summary": _combine_monthly(monthly_income["months"], monthly_expenses["months"]),
            "expense_categories": category_breakdown["categories"],
            "recent_transactions": [
                {
                    "id": row.id,
                    "type": row.type,
                    "label": row.label,
                    "amount": row.amount,
                    "category": row.category,
                    "date": row.date,
                }
                for row in recent_items
            ],
        }


def _combine_monthly(income_months: list[dict], expense_months: list[dict]) -> list[dict]:
    by_month: dict[str, dict] = {}
    for m in income_months:
        by_month.setdefault(m["month"], {"month": m["month"], "income": _ZERO, "expenses": _ZERO})
        by_month[m["month"]]["income"] = m["total"]
    for m in expense_months:
        by_month.setdefault(m["month"], {"month": m["month"], "income": _ZERO, "expenses": _ZERO})
        by_month[m["month"]]["expenses"] = m["total"]
    return [by_month[month] for month in sorted(by_month)]
