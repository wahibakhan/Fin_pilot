import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.models.category import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType = CategoryType.EXPENSE


class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: CategoryType
    is_archived: bool
