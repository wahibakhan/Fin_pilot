"""Read-only, parameterized aggregate query templates for the AI assistant's
analytical questions. Deliberately NOT a general query interface — there is
no code path here that accepts free-text SQL; only these fixed, typed
functions exist, each mapping to exactly one aggregate shape."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.models.expense import Expense
from src.models.income import Income

_ZERO = Decimal(0)


async def top_n_expenses(
    db: AsyncSession, *, n: int, date_from: date, date_to: date
) -> list[Expense]:
    stmt = (
        select(Expense)
        .where(
            Expense.deleted_at.is_(None), Expense.date >= date_from, Expense.date <= date_to
        )
        .order_by(Expense.amount.desc())
        .limit(n)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def sum_expenses(db: AsyncSession, *, date_from: date, date_to: date) -> Decimal:
    stmt = select(func.coalesce(func.sum(Expense.amount), _ZERO)).where(
        Expense.deleted_at.is_(None), Expense.date >= date_from, Expense.date <= date_to
    )
    return (await db.execute(stmt)).scalar_one()


async def sum_income(db: AsyncSession, *, date_from: date, date_to: date) -> Decimal:
    stmt = select(func.coalesce(func.sum(Income.amount), _ZERO)).where(
        Income.deleted_at.is_(None), Income.date >= date_from, Income.date <= date_to
    )
    return (await db.execute(stmt)).scalar_one()


async def sum_expenses_by_category_name(
    db: AsyncSession, *, category_name: str, date_from: date, date_to: date
) -> Decimal:
    stmt = (
        select(func.coalesce(func.sum(Expense.amount), _ZERO))
        .join(Category, Category.id == Expense.category_id)
        .where(
            Category.name.ilike(category_name),
            Expense.deleted_at.is_(None),
            Expense.date >= date_from,
            Expense.date <= date_to,
        )
    )
    return (await db.execute(stmt)).scalar_one()


async def category_expense_history(
    db: AsyncSession, *, category_id, exclude_expense_id=None
) -> list[Decimal]:
    """All historical active expense amounts in a category, for outlier
    detection (audit_tool.py). Excludes one expense id (the candidate being
    evaluated) so it doesn't skew its own baseline."""
    stmt = select(Expense.amount).where(
        Expense.category_id == category_id, Expense.deleted_at.is_(None)
    )
    if exclude_expense_id is not None:
        stmt = stmt.where(Expense.id != exclude_expense_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
