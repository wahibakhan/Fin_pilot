import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.tools.audit_tool import check_expense_for_flags
from src.core.dependencies import get_current_user, get_db
from src.models.user import User
from src.schemas.expense import Expense, ExpenseCreate, ExpensePage, ExpenseUpdate
from src.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=ExpensePage)
async def list_expenses(
    q: str | None = None,
    category_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ExpensePage:
    items, total = await ExpenseService(db).list_expenses(
        q=q,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return ExpensePage(
        items=[Expense.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Expense:
    expense = await ExpenseService(db).create_expense(actor=current_user, **payload.model_dump())
    flags = await check_expense_for_flags(db, expense)
    return Expense.model_validate(expense).model_copy(update={"flags": flags})


@router.get("/{expense_id}", response_model=Expense)
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Expense:
    expense = await ExpenseService(db).get_expense(expense_id)
    return Expense.model_validate(expense)


@router.patch("/{expense_id}", response_model=Expense)
async def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Expense:
    expense = await ExpenseService(db).update_expense(
        actor=current_user, expense_id=expense_id, **payload.model_dump()
    )
    return Expense.model_validate(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await ExpenseService(db).delete_expense(actor=current_user, expense_id=expense_id)
