import uuid
from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.models.expense import CreatedVia


class IncomeCreate(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    date: date_
    description: str | None = None


class IncomeUpdate(BaseModel):
    source: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0)
    date: date_ | None = None
    description: str | None = None


class Income(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    amount: Decimal
    date: date_
    description: str | None
    created_by: uuid.UUID
    created_via: CreatedVia
    created_at: datetime
    updated_at: datetime


class IncomePage(BaseModel):
    items: list[Income]
    total: int
    page: int
    page_size: int
