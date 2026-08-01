"""DashboardService integration tests. Require a reachable Postgres; skip automatically without one."""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.category import Category, CategoryType
from src.models.user import User, UserRole
from src.services.dashboard_service import DashboardService
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService


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


async def test_summary_totals_match_seeded_data(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Consulting", amount="5000", date=date(2026, 7, 2)
    )

    summary = await DashboardService(db_session).get_summary(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    assert summary["total_income"] == Decimal("5000.00")
    assert summary["total_expenses"] == Decimal("1000.00")
    assert summary["net_profit"] == Decimal("4000.00")


async def test_summary_monthly_combines_income_and_expenses(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Consulting", amount="5000", date=date(2026, 7, 2)
    )

    summary = await DashboardService(db_session).get_summary(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    months = {m["month"]: m for m in summary["monthly_summary"]}
    assert months["2026-07"]["income"] == Decimal("5000.00")
    assert months["2026-07"]["expenses"] == Decimal("1000.00")


async def test_summary_category_breakdown_and_recent_transactions(
    db_session: AsyncSession, unique_email: str
):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    expense = await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )

    summary = await DashboardService(db_session).get_summary(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    assert any(c["category"] == category.name for c in summary["expense_categories"])
    assert any(t["id"] == expense.id for t in summary["recent_transactions"])


async def test_summary_reflects_transaction_added_moments_earlier(
    db_session: AsyncSession, unique_email: str
):
    """FR-008: dashboard figures must reflect the latest recorded transactions."""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    service = DashboardService(db_session)

    before = await service.get_summary(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    assert before["total_expenses"] == Decimal(0)

    await ExpenseService(db_session).create_expense(
        actor=user, title="Just Added", amount="250", category_id=category.id, date=date(2026, 7, 15)
    )

    after = await service.get_summary(date_from=date(2026, 7, 1), date_to=date(2026, 7, 31))
    assert after["total_expenses"] == Decimal("250.00")
