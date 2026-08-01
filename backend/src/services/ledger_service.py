import uuid
from datetime import date

from sqlalchemy import String, cast, func, literal, or_, select, union_all
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category
from src.models.expense import Expense
from src.models.income import Income

_SORTABLE_COLUMNS = {"date", "amount"}


def _ledger_subquery():
    expense_rows = (
        select(
            Expense.id.label("id"),
            literal("expense").label("type"),
            Expense.title.label("label"),
            Expense.amount.label("amount"),
            Category.name.label("category"),
            Expense.category_id.label("category_id"),
            Expense.date.label("date"),
            Expense.description.label("description"),
            Expense.created_via.label("created_via"),
            Expense.created_at.label("created_at"),
        )
        .join(Category, Category.id == Expense.category_id)
        .where(Expense.deleted_at.is_(None))
    )
    income_rows = (
        select(
            Income.id.label("id"),
            literal("income").label("type"),
            Income.source.label("label"),
            Income.amount.label("amount"),
            cast(literal(None), String).label("category"),
            cast(literal(None), PgUUID(as_uuid=True)).label("category_id"),
            Income.date.label("date"),
            Income.description.label("description"),
            Income.created_via.label("created_via"),
            Income.created_at.label("created_at"),
        )
        .where(Income.deleted_at.is_(None))
    )
    return union_all(expense_rows, income_rows).subquery("ledger")


class LedgerService:
    """Read model over active expenses+income (FR-017, FR-018). No physical
    table — see data-model.md's rationale for why `ledger` is a view, not a
    second source of truth."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_ledger(
        self,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: str = "date",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list, int]:
        ledger = _ledger_subquery()
        stmt = select(ledger)

        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(ledger.c.label.ilike(like), ledger.c.description.ilike(like)))
        if category_id is not None:
            stmt = stmt.where(ledger.c.category_id == category_id)
        if date_from is not None:
            stmt = stmt.where(ledger.c.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(ledger.c.date <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar_one()

        sort_column = ledger.c[sort_by if sort_by in _SORTABLE_COLUMNS else "date"]
        order = sort_column.asc() if sort_dir == "asc" else sort_column.desc()
        stmt = stmt.order_by(order).offset((page - 1) * page_size).limit(page_size)

        result = await self._db.execute(stmt)
        return list(result.all()), total
