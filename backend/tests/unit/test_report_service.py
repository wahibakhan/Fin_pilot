"""ReportService integration tests, exercised through ExpenseService/IncomeService
so journal auto-posting is covered end to end. Require a reachable Postgres;
skip automatically without one."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError
from src.models.category import Category, CategoryType
from src.models.user import User, UserRole
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService
from src.services.report_service import ReportService


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


async def test_profit_and_loss_reconciles(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()

    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Consulting", amount="5000", date=date(2026, 7, 2)
    )

    report = await ReportService(db_session).profit_and_loss(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    assert report["total_income"] == Decimal("5000.00")
    assert report["total_expenses"] == Decimal("1000.00")
    assert report["net_profit"] == Decimal("4000.00")


async def test_profit_and_loss_empty_period_is_zero_not_error(db_session: AsyncSession):
    report = await ReportService(db_session).profit_and_loss(
        date_from=date(2020, 1, 1), date_to=date(2020, 1, 31)
    )

    assert report["total_income"] == Decimal(0)
    assert report["total_expenses"] == Decimal(0)
    assert report["net_profit"] == Decimal(0)


async def test_invalid_date_range_raises_validation_error(db_session: AsyncSession):
    with pytest.raises(ValidationError):
        await ReportService(db_session).profit_and_loss(
            date_from=date(2026, 7, 31), date_to=date(2026, 7, 1)
        )


async def test_balance_sheet_balances_and_matches_cash(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()

    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Consulting", amount="5000", date=date(2026, 7, 2)
    )

    report = await ReportService(db_session).balance_sheet(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    assert report["cash"] == Decimal("4000.00")
    assert report["total_assets"] == report["total_equity"]


async def test_trial_balance_debits_equal_credits(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()

    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Consulting", amount="5000", date=date(2026, 7, 2)
    )

    report = await ReportService(db_session).trial_balance(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    assert report["total_debits"] == report["total_credits"]
    assert report["total_debits"] == Decimal("6000.00")


async def test_update_expense_reverses_and_reposts_journal(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    expense_service = ExpenseService(db_session)
    expense = await expense_service.create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )

    await expense_service.update_expense(actor=user, expense_id=expense.id, amount="1500")

    report = await ReportService(db_session).balance_sheet(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )
    assert report["cash"] == Decimal("-1500.00")

    trial_balance = await ReportService(db_session).trial_balance(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )
    assert trial_balance["total_debits"] == trial_balance["total_credits"]


async def test_delete_expense_reverses_journal_to_zero(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    expense_service = ExpenseService(db_session)
    expense = await expense_service.create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )

    await expense_service.delete_expense(actor=user, expense_id=expense.id)

    report = await ReportService(db_session).balance_sheet(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )
    assert report["cash"] == Decimal("0.00")


async def test_cash_flow_matches_net_profit_under_cash_basis(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()

    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Consulting", amount="5000", date=date(2026, 7, 2)
    )

    cash_flow = await ReportService(db_session).cash_flow_summary(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )
    pnl = await ReportService(db_session).profit_and_loss(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    assert cash_flow["net_cash_flow"] == pnl["net_profit"]


async def test_monthly_expense_report_buckets_by_month(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    expense_service = ExpenseService(db_session)
    await expense_service.create_expense(
        actor=user, title="June Rent", amount="1000", category_id=category.id, date=date(2026, 6, 15)
    )
    await expense_service.create_expense(
        actor=user, title="July Rent", amount="1200", category_id=category.id, date=date(2026, 7, 15)
    )

    report = await ReportService(db_session).monthly_expense_report(
        date_from=date(2026, 6, 1), date_to=date(2026, 7, 31)
    )

    months = {m["month"]: m["total"] for m in report["months"]}
    assert months["2026-06"] == Decimal("1000.00")
    assert months["2026-07"] == Decimal("1200.00")
    assert report["total_expenses"] == Decimal("2200.00")


async def test_category_wise_expense_report_groups_correctly(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    rent = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    utilities = await _make_category(db_session, name=f"Utilities-{unique_email[:6]}")
    await db_session.commit()
    expense_service = ExpenseService(db_session)
    await expense_service.create_expense(
        actor=user, title="Rent", amount="1000", category_id=rent.id, date=date(2026, 7, 1)
    )
    await expense_service.create_expense(
        actor=user, title="Electricity", amount="200", category_id=utilities.id, date=date(2026, 7, 5)
    )

    report = await ReportService(db_session).category_wise_expense_report(
        date_from=date(2026, 7, 1), date_to=date(2026, 7, 31)
    )

    totals = {c["category"]: c["total"] for c in report["categories"]}
    assert totals[rent.name] == Decimal("1000.00")
    assert totals[utilities.name] == Decimal("200.00")
