import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db
from src.models.user import User
from src.schemas.income import Income, IncomeCreate, IncomePage, IncomeUpdate
from src.services.income_service import IncomeService

router = APIRouter(prefix="/income", tags=["income"])


@router.get("", response_model=IncomePage)
async def list_income(
    q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> IncomePage:
    items, total = await IncomeService(db).list_income(
        q=q, date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )
    return IncomePage(
        items=[Income.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=Income, status_code=status.HTTP_201_CREATED)
async def create_income(
    payload: IncomeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Income:
    income = await IncomeService(db).create_income(actor=current_user, **payload.model_dump())
    return Income.model_validate(income)


@router.get("/{income_id}", response_model=Income)
async def get_income(
    income_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Income:
    income = await IncomeService(db).get_income(income_id)
    return Income.model_validate(income)


@router.patch("/{income_id}", response_model=Income)
async def update_income(
    income_id: uuid.UUID,
    payload: IncomeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Income:
    income = await IncomeService(db).update_income(
        actor=current_user, income_id=income_id, **payload.model_dump()
    )
    return Income.model_validate(income)


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(
    income_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await IncomeService(db).delete_income(actor=current_user, income_id=income_id)
