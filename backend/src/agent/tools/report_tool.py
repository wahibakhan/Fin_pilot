"""Wraps ReportService so AI-requested reports use the exact same figures as
the REST endpoints (FR-024) — never a separately-computed number."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.report_service import ReportService

_EXPLAINERS = {
    "profit-and-loss": lambda r: (
        f"Total income was {r['total_income']} and total expenses were "
        f"{r['total_expenses']}, for a net profit of {r['net_profit']}."
    ),
    "balance-sheet": lambda r: (
        f"As of {r['as_of']}, cash on hand is {r['cash']}, which equals total "
        f"assets. Retained earnings (income minus expenses to date) is "
        f"{r['retained_earnings']}, matching total equity — the books balance."
    ),
    "trial-balance": lambda r: (
        f"Total debits ({r['total_debits']}) equal total credits "
        f"({r['total_credits']}) across {len(r['accounts'])} accounts, as they "
        "must in a balanced ledger."
    ),
    "cash-flow": lambda r: (
        f"Cash in was {r['cash_in']} and cash out was {r['cash_out']}, for a "
        f"net cash flow of {r['net_cash_flow']}."
    ),
    "monthly-expenses": lambda r: (
        f"Total expenses across the period were {r['total_expenses']}, broken "
        f"down over {len(r['months'])} month(s)."
    ),
    "income": lambda r: (
        f"Total income across the period was {r['total_income']}, broken down "
        f"over {len(r['months'])} month(s)."
    ),
    "category-expenses": lambda r: (
        f"Total expenses across the period were {r['total_expenses']}, spread "
        f"across {len(r['categories'])} categor{'y' if len(r['categories']) == 1 else 'ies'}."
    ),
}

_METHOD_BY_TYPE = {
    "profit-and-loss": "profit_and_loss",
    "balance-sheet": "balance_sheet",
    "trial-balance": "trial_balance",
    "cash-flow": "cash_flow_summary",
    "monthly-expenses": "monthly_expense_report",
    "income": "income_report",
    "category-expenses": "category_wise_expense_report",
}


async def generate_report(
    db: AsyncSession, *, report_type: str, date_from: date, date_to: date
) -> dict:
    method_name = _METHOD_BY_TYPE.get(report_type)
    if method_name is None:
        raise ValueError(f"Unknown report type: {report_type}")

    method = getattr(ReportService(db), method_name)
    report = await method(date_from=date_from, date_to=date_to)
    explanation = _EXPLAINERS[report_type](report)
    return {"report": report, "explanation": explanation}
