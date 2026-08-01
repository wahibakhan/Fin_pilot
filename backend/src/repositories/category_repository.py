import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category, CategoryType


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self, *, include_archived: bool = False) -> list[Category]:
        stmt = select(Category).order_by(Category.name)
        if not include_archived:
            stmt = stmt.where(Category.is_archived.is_(False))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        return await self._db.get(Category, category_id)

    async def get_by_name(self, name: str) -> Category | None:
        result = await self._db.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def create(self, *, name: str, type: CategoryType = CategoryType.EXPENSE) -> Category:
        category = Category(name=name, type=type)
        self._db.add(category)
        await self._db.flush()
        return category
