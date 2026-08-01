import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.expense import CreatedVia
from src.models.income import Income


class IncomeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        *,
        q: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Income], int]:
        stmt = select(Income).where(Income.deleted_at.is_(None))

        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Income.source.ilike(like), Income.description.ilike(like)))
        if date_from is not None:
            stmt = stmt.where(Income.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Income.date <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Income.date.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_active(self, income_id: uuid.UUID) -> Income | None:
        income = await self._db.get(Income, income_id)
        if income is None or income.deleted_at is not None:
            return None
        return income

    async def create(
        self,
        *,
        source: str,
        amount,
        date: date,
        description: str | None,
        created_by: uuid.UUID,
        created_via: CreatedVia = CreatedVia.MANUAL,
    ) -> Income:
        income = Income(
            source=source,
            amount=amount,
            date=date,
            description=description,
            created_by=created_by,
            created_via=created_via,
        )
        self._db.add(income)
        await self._db.flush()
        return income

    async def update(self, income: Income, **fields) -> Income:
        for key, value in fields.items():
            setattr(income, key, value)
        await self._db.flush()
        return income

    async def soft_delete(self, income: Income) -> None:
        income.deleted_at = datetime.now(UTC)
        await self._db.flush()
