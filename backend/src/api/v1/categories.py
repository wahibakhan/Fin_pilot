from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db
from src.models.user import User
from src.schemas.category import Category, CategoryCreate
from src.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[Category])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Category]:
    categories = await CategoryService(db).list_categories()
    return [Category.model_validate(c) for c in categories]


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Category:
    category = await CategoryService(db).create_category(name=payload.name, type=payload.type)
    return Category.model_validate(category)
