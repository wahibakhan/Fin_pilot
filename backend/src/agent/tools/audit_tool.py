"""Duplicate-transaction and unusually-large-expense detection (FR-030,
FR-031). Never auto-deletes or auto-modifies anything — it only flags, for
both the explicit "run monthly audit" command (T081) and the passive
inline flag on create (T082)."""

from statistics import mean, pstdev

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.tools import sql_query_tool
from src.models.category import Category
from src.models.expense import Expense

_DUPLICATE_WINDOW_DAYS = 3
_MIN_HISTORY_FOR_STATS = 3
_Z_THRESHOLD = 2.0


def _large_expense_threshold(history: list) -> float | None:
    amounts = [float(a) for a in history]
    if len(amounts) < _MIN_HISTORY_FOR_STATS:
        return None
    avg = mean(amounts)
    std = pstdev(amounts)
    return avg + _Z_THRESHOLD * std if std > 0 else avg * 3


async def find_duplicate_expenses(
    db: AsyncSession, *, date_from, date_to
) -> list[dict]:
    stmt = select(Expense).where(
        Expense.deleted_at.is_(None), Expense.date >= date_from, Expense.date <= date_to
    ).order_by(Expense.date)
    expenses = list((await db.execute(stmt)).scalars().all())

    duplicates = []
    seen_pairs: set[tuple[str, str]] = set()
    for i, a in enumerate(expenses):
        for b in expenses[i + 1 :]:
            if a.category_id != b.category_id or a.amount != b.amount:
                continue
            if abs((a.date - b.date).days) > _DUPLICATE_WINDOW_DAYS:
                continue
            pair_key = tuple(sorted([str(a.id), str(b.id)]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            duplicates.append(
                {
                    "expense_ids": [str(a.id), str(b.id)],
                    "title": a.title,
                    "amount": str(a.amount),
                    "dates": [a.date.isoformat(), b.date.isoformat()],
                }
            )
    return duplicates


async def find_large_expenses(db: AsyncSession, *, date_from, date_to) -> list[dict]:
    stmt = select(Expense).where(
        Expense.deleted_at.is_(None), Expense.date >= date_from, Expense.date <= date_to
    )
    expenses = list((await db.execute(stmt)).scalars().all())

    flagged = []
    for expense in expenses:
        history = await sql_query_tool.category_expense_history(
            db, category_id=expense.category_id, exclude_expense_id=expense.id
        )
        threshold = _large_expense_threshold(history)
        if threshold is not None and float(expense.amount) > threshold:
            flagged.append(
                {
                    "expense_id": str(expense.id),
                    "title": expense.title,
                    "amount": str(expense.amount),
                    "category_average": round(mean(float(a) for a in history), 2),
                }
            )
    return flagged


async def run_audit(db: AsyncSession, *, date_from, date_to) -> dict:
    duplicates = await find_duplicate_expenses(db, date_from=date_from, date_to=date_to)
    large_expenses = await find_large_expenses(db, date_from=date_from, date_to=date_to)
    return {"duplicates": duplicates, "large_expenses": large_expenses}


async def check_expense_for_flags(db: AsyncSession, expense: Expense) -> list[dict]:
    """Passive check run right after any create (manual or AI) — never blocks
    the create, just returns flags to surface alongside it."""
    flags: list[dict] = []

    duplicate_stmt = select(Expense).where(
        Expense.deleted_at.is_(None),
        Expense.id != expense.id,
        Expense.category_id == expense.category_id,
        Expense.amount == expense.amount,
    )
    candidates = (await db.execute(duplicate_stmt)).scalars().all()
    near_duplicate = next(
        (c for c in candidates if abs((c.date - expense.date).days) <= _DUPLICATE_WINDOW_DAYS),
        None,
    )
    if near_duplicate is not None:
        flags.append(
            {
                "type": "duplicate",
                "message": (
                    f"This looks like a possible duplicate of '{near_duplicate.title}' "
                    f"on {near_duplicate.date} for the same amount."
                ),
            }
        )

    history = await sql_query_tool.category_expense_history(
        db, category_id=expense.category_id, exclude_expense_id=expense.id
    )
    threshold = _large_expense_threshold(history)
    if threshold is not None and float(expense.amount) > threshold:
        category = await db.get(Category, expense.category_id)
        category_name = category.name if category else "this category"
        avg = round(mean(float(a) for a in history), 2)
        flags.append(
            {
                "type": "large_expense",
                "message": (
                    f"This is unusually large for '{category_name}' "
                    f"(category average: {avg})."
                ),
            }
        )

    return flags
