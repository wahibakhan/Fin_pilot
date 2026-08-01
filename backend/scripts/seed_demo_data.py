"""Create one demo user per role, idempotently.

Usage: uv run python -m scripts.seed_demo_data
Requires DATABASE_URL to point at a reachable, migrated Postgres database.
"""
import asyncio

from src.core.db import AsyncSessionLocal
from src.core.security import hash_password
from src.models.category import CategoryType
from src.models.user import UserRole
from src.repositories.category_repository import CategoryRepository
from src.repositories.user_repository import UserRepository

DEMO_USERS = [
    ("Olivia Owner", "owner@finpilot.demo", "DemoPass123!", UserRole.BUSINESS_OWNER),
    ("Amara Accountant", "accountant@finpilot.demo", "DemoPass123!", UserRole.ACCOUNTANT),
    ("Omar Admin", "admin@finpilot.demo", "DemoPass123!", UserRole.OFFICE_ADMINISTRATOR),
]

DEMO_CATEGORIES = [
    ("Rent", CategoryType.EXPENSE),
    ("Utilities", CategoryType.EXPENSE),
    ("Salaries", CategoryType.EXPENSE),
    ("Office Supplies", CategoryType.EXPENSE),
    ("Travel", CategoryType.EXPENSE),
    ("Marketing", CategoryType.EXPENSE),
    ("Software & Subscriptions", CategoryType.EXPENSE),
    ("Client Services", CategoryType.INCOME),
    ("Product Sales", CategoryType.INCOME),
    ("Consulting", CategoryType.INCOME),
    ("Other", CategoryType.BOTH),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        users = UserRepository(db)
        for full_name, email, password, role in DEMO_USERS:
            existing = await users.get_by_email(email)
            if existing is not None:
                print(f"skip (exists): {email}")
                continue
            await users.create(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            print(f"created: {email} / {password} ({role.value})")
        await db.commit()

        categories = CategoryRepository(db)
        for name, category_type in DEMO_CATEGORIES:
            existing = await categories.get_by_name(name)
            if existing is not None:
                print(f"skip (exists): category '{name}'")
                continue
            await categories.create(name=name, type=category_type)
            print(f"created category: {name} ({category_type.value})")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
