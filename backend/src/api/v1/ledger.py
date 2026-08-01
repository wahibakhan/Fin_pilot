import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db
from src.models.user import User
from src.schemas.ledger import LedgerEntry, LedgerPage
from src.services.ledger_service import LedgerService

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("", response_model=LedgerPage)
async def list_ledger(
    q: str | None = None,
    category_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: Literal["date", "amount"] = "date",
    sort_dir: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> LedgerPage:
    rows, total = await LedgerService(db).list_ledger(
        q=q,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    return LedgerPage(
        items=[LedgerEntry.model_validate(row, from_attributes=True) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
