import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.models.expense import CreatedVia


class LedgerEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: Literal["expense", "income"]
    label: str
    amount: Decimal
    category: str | None
    date: date
    description: str | None
    created_via: CreatedVia


class LedgerPage(BaseModel):
    items: list[LedgerEntry]
    total: int
    page: int
    page_size: int
