"""Seed 60+ mixed expense/income rows across varied dates/categories/amounts,
for exercising ledger pagination/sort/filter (Phase 5, quickstart.md §6).

Usage: uv run python -m scripts.seed_bulk_ledger
Requires DATABASE_URL to point at a reachable, migrated Postgres database,
and at least one user to already exist (run seed_demo_data first).
"""
import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from src.core.db import AsyncSessionLocal
from src.models.category import Category, CategoryType
from src.models.expense import CreatedVia, Expense
from src.models.income import Income
from src.models.user import User

EXPENSE_CATEGORY_NAMES = ["Rent", "Utilities", "Payroll", "Software", "Travel", "Office Supplies"]
INCOME_SOURCES = ["Client Invoice", "Product Sales", "Consulting Fee", "Interest Income"]

EXPENSE_ROW_COUNT = 45
INCOME_ROW_COUNT = 20


async def _get_or_create_categories(db) -> list[Category]:
    result = await db.execute(select(Category).where(Category.name.in_(EXPENSE_CATEGORY_NAMES)))
    existing = {c.name: c for c in result.scalars().all()}

    categories = []
    for name in EXPENSE_CATEGORY_NAMES:
        category = existing.get(name)
        if category is None:
            category = Category(name=name, type=CategoryType.EXPENSE)
            db.add(category)
            await db.flush()
        categories.append(category)
    return categories


async def _get_any_user(db) -> User:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        raise RuntimeError("No users found — run `uv run python -m scripts.seed_demo_data` first.")
    return user


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        user = await _get_any_user(db)
        categories = await _get_or_create_categories(db)
        today = date.today()  # noqa: DTZ011 - calendar date for demo data, no timezone semantics apply

        for i in range(EXPENSE_ROW_COUNT):
            category = random.choice(categories)
            db.add(
                Expense(
                    title=f"{category.name} expense #{i + 1}",
                    amount=Decimal(random.randrange(500, 500000)) / 100,
                    category_id=category.id,
                    date=today - timedelta(days=random.randint(0, 180)),
                    description=None,
                    created_by=user.id,
                    created_via=CreatedVia.MANUAL,
                )
            )

        for i in range(INCOME_ROW_COUNT):
            db.add(
                Income(
                    source=f"{random.choice(INCOME_SOURCES)} #{i + 1}",
                    amount=Decimal(random.randrange(10000, 2000000)) / 100,
                    date=today - timedelta(days=random.randint(0, 180)),
                    description=None,
                    created_by=user.id,
                    created_via=CreatedVia.MANUAL,
                )
            )

        await db.commit()
        print(f"Seeded {EXPENSE_ROW_COUNT} expenses + {INCOME_ROW_COUNT} income rows "
              f"({EXPENSE_ROW_COUNT + INCOME_ROW_COUNT} total ledger entries).")


if __name__ == "__main__":
    asyncio.run(seed())
