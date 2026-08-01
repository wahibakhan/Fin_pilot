"""Create/update/delete tools — the only place the agent touches financial
records, and it does so exclusively through ExpenseService/IncomeService, the
same services the REST API uses. This is what guarantees the AI path can
never bypass FR-034 validation or FR-003 permission checks (see research.md
§8)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.intents import AddExpense, AddIncome
from src.models.expense import CreatedVia, Expense
from src.models.income import Income
from src.models.user import User
from src.repositories.category_repository import CategoryRepository
from src.repositories.expense_repository import ExpenseRepository
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService


class AmbiguousMatchError(Exception):
    def __init__(self, question: str) -> None:
        super().__init__(question)
        self.question = question


class NoMatchError(Exception):
    pass


async def add_expense(db: AsyncSession, *, actor: User, args: AddExpense) -> Expense:
    categories = CategoryRepository(db)
    category = await categories.get_by_name(args.category)
    if category is None:
        category = await categories.create(name=args.category)
        # Not committed here — ExpenseService.create_expense's own commit
        # below covers both the new category and the expense atomically.

    return await ExpenseService(db).create_expense(
        actor=actor,
        title=args.title,
        amount=Decimal(str(args.amount)),
        category_id=category.id,
        date=date.fromisoformat(args.date),
        description=args.description,
        created_via=CreatedVia.AI,
    )


async def add_income(db: AsyncSession, *, actor: User, args: AddIncome) -> Income:
    return await IncomeService(db).create_income(
        actor=actor,
        source=args.source,
        amount=Decimal(str(args.amount)),
        date=date.fromisoformat(args.date),
        description=args.description,
        created_via=CreatedVia.AI,
    )


async def resolve_expense_by_description(db: AsyncSession, search_text: str) -> Expense:
    """Finds the single active expense matching free text, for AI-driven
    delete. Raises AmbiguousMatchError if more than one candidate matches
    (FR: assistant must ask the user to disambiguate rather than guess) or
    NoMatchError if none do."""
    items, total = await ExpenseRepository(db).list(q=search_text, page=1, page_size=10)
    if total == 0:
        raise NoMatchError(f"I couldn't find an expense matching '{search_text}'.")
    if total > 1:
        candidates = "; ".join(f"{e.title} ({e.date}, {e.amount})" for e in items)
        raise AmbiguousMatchError(
            f"I found {total} expenses matching '{search_text}': {candidates}. "
            "Which one did you mean?"
        )
    return items[0]


async def delete_expense(db: AsyncSession, *, actor: User, expense_id: uuid.UUID) -> Expense:
    expense = await ExpenseService(db).get_expense(expense_id)
    await ExpenseService(db).delete_expense(actor=actor, expense_id=expense_id)
    return expense
