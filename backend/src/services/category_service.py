from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, ValidationError
from src.models.category import Category, CategoryType
from src.repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._categories = CategoryRepository(db)

    async def list_categories(self, *, include_archived: bool = False) -> list[Category]:
        return await self._categories.list(include_archived=include_archived)

    async def create_category(
        self, *, name: str, type: CategoryType = CategoryType.EXPENSE
    ) -> Category:
        if not name or not name.strip():
            raise ValidationError("Name is required", field="name")

        existing = await self._categories.get_by_name(name)
        if existing is not None:
            raise ConflictError(f"Category '{name}' already exists")

        category = await self._categories.create(name=name, type=type)
        await self._db.commit()
        return category
