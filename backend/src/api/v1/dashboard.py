import calendar
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db
from src.models.user import User
from src.schemas.dashboard import DashboardSummary
from src.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _period_to_range(period: str | None) -> tuple[date, date]:
    if period is None:
        today = datetime.now(UTC).date()
        year, month = today.year, today.month
    else:
        year, month = (int(p) for p in period.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    period: str | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    date_from, date_to = _period_to_range(period)
    summary = await DashboardService(db).get_summary(date_from=date_from, date_to=date_to)
    return DashboardSummary.model_validate(summary)
