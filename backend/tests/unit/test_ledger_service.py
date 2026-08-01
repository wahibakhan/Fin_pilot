"""LedgerService integration tests. Require a reachable Postgres; skip automatically without one."""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category, CategoryType
from src.models.expense import Expense
from src.models.income import Income
from src.models.user import User, UserRole
from src.repositories.expense_repository import ExpenseRepository
from src.services.ledger_service import LedgerService


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(full_name="Test User", email=email, password_hash="x", role=UserRole.BUSINESS_OWNER)
    db.add(user)
    await db.flush()
    return user


async def _make_category(db: AsyncSession, *, name: str) -> Category:
    category = Category(name=name, type=CategoryType.EXPENSE)
    db.add(category)
    await db.flush()
    return category


async def _seed_mixed(db: AsyncSession, user: User, category: Category) -> None:
    db.add_all(
        [
            Expense(
                title="Office Rent",
                amount=Decimal(1000),
                category_id=category.id,
                date=date(2026, 7, 1),
                created_by=user.id,
            ),
            Expense(
                title="Electricity Bill",
                amount=Decimal(200),
                category_id=category.id,
                date=date(2026, 7, 5),
                created_by=user.id,
            ),
            Income(
                source="Consulting Fee",
                amount=Decimal(5000),
                date=date(2026, 7, 3),
                created_by=user.id,
            ),
        ]
    )
    await db.commit()


async def test_ledger_unions_expenses_and_income(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    items, total = await LedgerService(db_session).list_ledger()

    assert total == 3
    types = {item.type for item in items}
    assert types == {"expense", "income"}


async def test_ledger_default_sort_is_by_date_desc(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    items, _ = await LedgerService(db_session).list_ledger()

    dates = [item.date for item in items]
    assert dates == sorted(dates, reverse=True)


async def test_ledger_sort_by_amount_ascending(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    items, _ = await LedgerService(db_session).list_ledger(sort_by="amount", sort_dir="asc")

    amounts = [item.amount for item in items]
    assert amounts == sorted(amounts)


async def test_ledger_filters_by_category_excludes_income(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    items, total = await LedgerService(db_session).list_ledger(category_id=category.id)

    assert total == 2
    assert all(item.type == "expense" for item in items)


async def test_ledger_filters_by_date_range(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    items, total = await LedgerService(db_session).list_ledger(
        date_from=date(2026, 7, 2), date_to=date(2026, 7, 4)
    )

    assert total == 1
    assert items[0].label == "Consulting Fee"


async def test_ledger_keyword_search_matches_both_types(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    items, total = await LedgerService(db_session).list_ledger(q="rent")

    assert total == 1
    assert items[0].label == "Office Rent"


async def test_ledger_pagination(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    page1, total = await LedgerService(db_session).list_ledger(page=1, page_size=2)
    page2, _ = await LedgerService(db_session).list_ledger(page=2, page_size=2)

    assert total == 3
    assert len(page1) == 2
    assert len(page2) == 1
    assert {item.id for item in page1}.isdisjoint({item.id for item in page2})


async def test_ledger_excludes_soft_deleted_rows(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await _seed_mixed(db_session, user, category)

    repo = ExpenseRepository(db_session)
    items, _ = await LedgerService(db_session).list_ledger(q="rent")
    expense = await repo.get_active(items[0].id)
    assert expense is not None
    await repo.soft_delete(expense)
    await db_session.commit()

    items_after, total_after = await LedgerService(db_session).list_ledger(q="rent")
    assert total_after == 0
    assert items_after == []
