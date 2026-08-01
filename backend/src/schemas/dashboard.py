import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class MonthlySummaryEntry(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal


class CategoryBreakdownEntry(BaseModel):
    category: str
    total: Decimal


class RecentTransaction(BaseModel):
    id: uuid.UUID
    type: str
    label: str
    amount: Decimal
    category: str | None
    date: date


class DashboardSummary(BaseModel):
    date_from: date
    date_to: date
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    monthly_summary: list[MonthlySummaryEntry]
    expense_categories: list[CategoryBreakdownEntry]
    recent_transactions: list[RecentTransaction]
