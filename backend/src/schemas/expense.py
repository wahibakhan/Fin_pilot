import uuid
from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.models.expense import CreatedVia


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    category_id: uuid.UUID
    date: date_
    description: str | None = None


class ExpenseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    category_id: uuid.UUID | None = None
    date: date_ | None = None
    description: str | None = None


class ExpenseFlag(BaseModel):
    type: str
    message: str


class Expense(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    amount: Decimal
    category_id: uuid.UUID
    date: date_
    description: str | None
    created_by: uuid.UUID
    created_via: CreatedVia
    created_at: datetime
    updated_at: datetime
    flags: list[ExpenseFlag] = []
    """Populated only on the create response (FR-030/FR-031 passive check);
    empty on list/get/update — see api/v1/expenses.py."""


class ExpensePage(BaseModel):
    items: list[Expense]
    total: int
    page: int
    page_size: int
