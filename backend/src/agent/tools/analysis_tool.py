"""Top-N, period comparison, category/period totals, net-profit lookups — all
backed by sql_query_tool's aggregate templates (or ReportService for net
profit), so AI-reported numbers can never diverge from what the UI shows."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.tools import sql_query_tool
from src.services.report_service import ReportService


async def top_expenses(db: AsyncSession, *, n: int, date_from: date, date_to: date) -> dict:
    expenses = await sql_query_tool.top_n_expenses(db, n=n, date_from=date_from, date_to=date_to)
    items = [
        {"title": e.title, "amount": str(e.amount), "date": e.date.isoformat()} for e in expenses
    ]
    return {"items": items, "count": len(items)}


async def compare_periods(
    db: AsyncSession,
    *,
    period_a_from: date,
    period_a_to: date,
    period_b_from: date,
    period_b_to: date,
) -> dict:
    total_a = await sql_query_tool.sum_expenses(db, date_from=period_a_from, date_to=period_a_to)
    total_b = await sql_query_tool.sum_expenses(db, date_from=period_b_from, date_to=period_b_to)
    delta = total_b - total_a
    percent_change = float(delta / total_a * 100) if total_a else None

    return {
        "period_a": {"from": period_a_from.isoformat(), "to": period_a_to.isoformat(), "total": str(total_a)},
        "period_b": {"from": period_b_from.isoformat(), "to": period_b_to.isoformat(), "total": str(total_b)},
        "delta": str(delta),
        "percent_change": percent_change,
    }


async def category_total(
    db: AsyncSession, *, category: str, date_from: date, date_to: date
) -> dict:
    total = await sql_query_tool.sum_expenses_by_category_name(
        db, category_name=category, date_from=date_from, date_to=date_to
    )
    return {"category": category, "total": str(total)}


async def net_profit(db: AsyncSession, *, date_from: date, date_to: date) -> dict:
    report = await ReportService(db).profit_and_loss(date_from=date_from, date_to=date_to)
    return {"net_profit": str(report["net_profit"])}
