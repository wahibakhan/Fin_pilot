import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import CreatedVia, Expense


class ExpenseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Expense], int]:
        stmt = select(Expense).where(Expense.deleted_at.is_(None))

        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Expense.title.ilike(like), Expense.description.ilike(like)))
        if category_id is not None:
            stmt = stmt.where(Expense.category_id == category_id)
        if date_from is not None:
            stmt = stmt.where(Expense.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Expense.date <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(Expense.date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_active(self, expense_id: uuid.UUID) -> Expense | None:
        expense = await self._db.get(Expense, expense_id)
        if expense is None or expense.deleted_at is not None:
            return None
        return expense

    async def create(
        self,
        *,
        title: str,
        amount,
        category_id: uuid.UUID,
        date: date,
        description: str | None,
        created_by: uuid.UUID,
        created_via: CreatedVia = CreatedVia.MANUAL,
    ) -> Expense:
        expense = Expense(
            title=title,
            amount=amount,
            category_id=category_id,
            date=date,
            description=description,
            created_by=created_by,
            created_via=created_via,
        )
        self._db.add(expense)
        await self._db.flush()
        return expense

    async def update(self, expense: Expense, **fields) -> Expense:
        for key, value in fields.items():
            setattr(expense, key, value)
        await self._db.flush()
        return expense

    async def soft_delete(self, expense: Expense) -> None:
        expense.deleted_at = datetime.now(UTC)
        await self._db.flush()
