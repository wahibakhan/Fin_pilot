from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ProfitAndLossReport(BaseModel):
    date_from: date
    date_to: date
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal


class BalanceSheetReport(BaseModel):
    as_of: date
    cash: Decimal
    total_assets: Decimal
    retained_earnings: Decimal
    total_equity: Decimal


class TrialBalanceAccount(BaseModel):
    account: str
    total_debit: Decimal
    total_credit: Decimal


class TrialBalanceReport(BaseModel):
    date_from: date
    date_to: date
    accounts: list[TrialBalanceAccount]
    total_debits: Decimal
    total_credits: Decimal


class CashFlowReport(BaseModel):
    date_from: date
    date_to: date
    cash_in: Decimal
    cash_out: Decimal
    net_cash_flow: Decimal


class MonthlyTotal(BaseModel):
    month: str
    total: Decimal


class MonthlyExpenseReport(BaseModel):
    date_from: date
    date_to: date
    months: list[MonthlyTotal]
    total_expenses: Decimal


class IncomeReport(BaseModel):
    date_from: date
    date_to: date
    months: list[MonthlyTotal]
    total_income: Decimal


class CategoryTotal(BaseModel):
    category: str
    total: Decimal


class CategoryWiseExpenseReport(BaseModel):
    date_from: date
    date_to: date
    categories: list[CategoryTotal]
    total_expenses: Decimal
