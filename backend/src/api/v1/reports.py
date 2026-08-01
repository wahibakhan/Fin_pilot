from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, require_role
from src.models.user import User, UserRole
from src.schemas.report import (
    BalanceSheetReport,
    CashFlowReport,
    CategoryWiseExpenseReport,
    IncomeReport,
    MonthlyExpenseReport,
    ProfitAndLossReport,
    TrialBalanceReport,
)
from src.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

_OWNER_OR_ACCOUNTANT = require_role(UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT)


@router.get("/profit-and-loss", response_model=ProfitAndLossReport)
async def profit_and_loss(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ProfitAndLossReport:
    result = await ReportService(db).profit_and_loss(date_from=date_from, date_to=date_to)
    return ProfitAndLossReport.model_validate(result)


@router.get("/balance-sheet", response_model=BalanceSheetReport)
async def balance_sheet(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(_OWNER_OR_ACCOUNTANT),
) -> BalanceSheetReport:
    result = await ReportService(db).balance_sheet(date_from=date_from, date_to=date_to)
    return BalanceSheetReport.model_validate(result)


@router.get("/trial-balance", response_model=TrialBalanceReport)
async def trial_balance(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(_OWNER_OR_ACCOUNTANT),
) -> TrialBalanceReport:
    result = await ReportService(db).trial_balance(date_from=date_from, date_to=date_to)
    return TrialBalanceReport.model_validate(result)


@router.get("/cash-flow", response_model=CashFlowReport)
async def cash_flow(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CashFlowReport:
    result = await ReportService(db).cash_flow_summary(date_from=date_from, date_to=date_to)
    return CashFlowReport.model_validate(result)


@router.get("/monthly-expenses", response_model=MonthlyExpenseReport)
async def monthly_expenses(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> MonthlyExpenseReport:
    result = await ReportService(db).monthly_expense_report(date_from=date_from, date_to=date_to)
    return MonthlyExpenseReport.model_validate(result)


@router.get("/income", response_model=IncomeReport)
async def income_report(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> IncomeReport:
    result = await ReportService(db).income_report(date_from=date_from, date_to=date_to)
    return IncomeReport.model_validate(result)


@router.get("/category-expenses", response_model=CategoryWiseExpenseReport)
async def category_expenses(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CategoryWiseExpenseReport:
    result = await ReportService(db).category_wise_expense_report(
        date_from=date_from, date_to=date_to
    )
    return CategoryWiseExpenseReport.model_validate(result)
