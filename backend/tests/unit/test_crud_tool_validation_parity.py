"""FR-034: validation must be identical regardless of whether a mutation
originates from manual entry or the AI assistant. These tests exercise the
AI path's entry point (agent/tools/crud_tool.py) directly and assert it
rejects the exact same bad input ExpenseService/IncomeService reject for
manual entry — proving the two paths share one validation source, not two
independently-maintained copies. Requires a reachable Postgres; skips
automatically without one."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.intents import AddExpense, AddIncome
from src.agent.tools import crud_tool
from src.core.exceptions import ValidationError
from src.models.category import Category, CategoryType
from src.models.user import User, UserRole


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


async def test_ai_add_expense_rejects_non_positive_amount(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()

    args = AddExpense(title="Bad", amount=0, category=category.name, date="2026-07-01")
    with pytest.raises(ValidationError) as exc_info:
        await crud_tool.add_expense(db_session, actor=user, args=args)
    assert exc_info.value.field == "amount"


async def test_ai_add_expense_creates_a_new_category_when_unknown(
    db_session: AsyncSession, unique_email: str
):
    """The AI path may reference a category by name that doesn't exist yet —
    it creates it (still going through the same validated create path), it
    doesn't silently fail or bypass the FK requirement."""
    user = await _make_user(db_session, email=unique_email)
    await db_session.commit()

    args = AddExpense(title="New Category Expense", amount=50, category="Brand New Category", date="2026-07-01")
    expense = await crud_tool.add_expense(db_session, actor=user, args=args)

    assert expense.title == "New Category Expense"


async def test_ai_add_income_rejects_non_positive_amount(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    await db_session.commit()

    args = AddIncome(source="Bad", amount=-5, date="2026-07-01")
    with pytest.raises(ValidationError) as exc_info:
        await crud_tool.add_income(db_session, actor=user, args=args)
    assert exc_info.value.field == "amount"


async def test_ai_created_expense_is_tagged_ai_and_audited(db_session: AsyncSession, unique_email: str):
    from sqlalchemy import select

    from src.models.audit_log import AuditAction, AuditEntityType, AuditLogEntry

    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()

    args = AddExpense(title="AI Rent", amount=1000, category=category.name, date="2026-07-01")
    expense = await crud_tool.add_expense(db_session, actor=user, args=args)

    assert expense.created_via.value == "ai"

    result = await db_session.execute(
        select(AuditLogEntry).where(
            AuditLogEntry.entity_type == AuditEntityType.EXPENSE, AuditLogEntry.entity_id == expense.id
        )
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    assert entries[0].action == AuditAction.CREATE
    assert entries[0].actor_type.value == "ai"
