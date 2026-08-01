"""ExpenseService integration tests. Require a reachable Postgres; skip automatically without one."""

import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.models.audit_log import AuditAction, AuditEntityType, AuditLogEntry
from src.models.category import Category, CategoryType
from src.models.user import User, UserRole
from src.services.expense_service import ExpenseService


async def _make_user(db: AsyncSession, *, role: UserRole, email: str) -> User:
    user = User(full_name="Test User", email=email, password_hash="x", role=role)
    db.add(user)
    await db.flush()
    return user


async def _make_category(db: AsyncSession, *, name: str, archived: bool = False) -> Category:
    category = Category(name=name, type=CategoryType.EXPENSE, is_archived=archived)
    db.add(category)
    await db.flush()
    return category


async def test_create_expense_success(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{uuid.uuid4().hex[:6]}")
    await db_session.commit()

    expense = await ExpenseService(db_session).create_expense(
        actor=owner,
        title="Office Rent",
        amount="50000",
        category_id=category.id,
        date=date(2026, 7, 1),
        description="July rent",
    )

    assert expense.title == "Office Rent"
    assert str(expense.amount) == "50000.00"
    assert expense.created_by == owner.id


async def test_create_expense_rejects_non_positive_amount(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    category = await _make_category(db_session, name=f"Utilities-{uuid.uuid4().hex[:6]}")
    await db_session.commit()

    with pytest.raises(ValidationError) as exc_info:
        await ExpenseService(db_session).create_expense(
            actor=owner, title="Bad", amount="0", category_id=category.id, date=date(2026, 7, 1)
        )
    assert exc_info.value.field == "amount"


async def test_create_expense_rejects_missing_category(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    await db_session.commit()

    with pytest.raises(ValidationError) as exc_info:
        await ExpenseService(db_session).create_expense(
            actor=owner,
            title="Ghost category",
            amount="10",
            category_id=uuid.uuid4(),
            date=date(2026, 7, 1),
        )
    assert exc_info.value.field == "category_id"


async def test_create_expense_rejects_blank_title(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{uuid.uuid4().hex[:6]}")
    await db_session.commit()

    with pytest.raises(ValidationError) as exc_info:
        await ExpenseService(db_session).create_expense(
            actor=owner, title="   ", amount="10", category_id=category.id, date=date(2026, 7, 1)
        )
    assert exc_info.value.field == "title"


async def test_create_expense_rejects_archived_category(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    category = await _make_category(
        db_session, name=f"Archived-{uuid.uuid4().hex[:6]}", archived=True
    )
    await db_session.commit()

    with pytest.raises(ValidationError) as exc_info:
        await ExpenseService(db_session).create_expense(
            actor=owner,
            title="Uses archived category",
            amount="10",
            category_id=category.id,
            date=date(2026, 7, 1),
        )
    assert exc_info.value.field == "category_id"


async def test_update_expense_changes_persist(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{uuid.uuid4().hex[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    expense = await service.create_expense(
        actor=owner, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )

    updated = await service.update_expense(actor=owner, expense_id=expense.id, amount="1200")

    assert str(updated.amount) == "1200.00"
    assert updated.title == "Rent"


async def test_delete_expense_forbidden_for_office_administrator(
    db_session: AsyncSession, unique_email: str
):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=f"owner-{unique_email}")
    admin = await _make_user(
        db_session, role=UserRole.OFFICE_ADMINISTRATOR, email=f"admin-{unique_email}"
    )
    category = await _make_category(db_session, name=f"Rent-{uuid.uuid4().hex[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    expense = await service.create_expense(
        actor=owner, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )

    with pytest.raises(PermissionDeniedError):
        await service.delete_expense(actor=admin, expense_id=expense.id)


async def test_delete_expense_allowed_for_accountant_and_hides_it(
    db_session: AsyncSession, unique_email: str
):
    accountant = await _make_user(db_session, role=UserRole.ACCOUNTANT, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{uuid.uuid4().hex[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    expense = await service.create_expense(
        actor=accountant,
        title="Rent",
        amount="1000",
        category_id=category.id,
        date=date(2026, 7, 1),
    )

    await service.delete_expense(actor=accountant, expense_id=expense.id)

    with pytest.raises(NotFoundError):
        await service.get_expense(expense.id)


async def test_list_expenses_filters_by_category_and_keyword(
    db_session: AsyncSession, unique_email: str
):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    rent_category = await _make_category(db_session, name=f"Rent-{uuid.uuid4().hex[:6]}")
    utilities_category = await _make_category(db_session, name=f"Utilities-{uuid.uuid4().hex[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    await service.create_expense(
        actor=owner, title="Office Rent", amount="1000", category_id=rent_category.id, date=date(2026, 7, 1)
    )
    await service.create_expense(
        actor=owner,
        title="Electricity Bill",
        amount="200",
        category_id=utilities_category.id,
        date=date(2026, 7, 2),
    )

    items, total = await service.list_expenses(category_id=rent_category.id)
    assert total == 1
    assert items[0].title == "Office Rent"

    items, total = await service.list_expenses(q="electricity")
    assert total == 1
    assert items[0].title == "Electricity Bill"


async def test_create_expense_writes_audit_log_entry(db_session: AsyncSession, unique_email: str):
    owner = await _make_user(db_session, role=UserRole.BUSINESS_OWNER, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{uuid.uuid4().hex[:6]}")
    await db_session.commit()

    expense = await ExpenseService(db_session).create_expense(
        actor=owner, title="Rent", amount="500", category_id=category.id, date=date(2026, 7, 1)
    )

    result = await db_session.execute(
        select(AuditLogEntry).where(
            AuditLogEntry.entity_type == AuditEntityType.EXPENSE,
            AuditLogEntry.entity_id == expense.id,
        )
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    assert entries[0].action == AuditAction.CREATE
    assert entries[0].actor_user_id == owner.id
    assert entries[0].after_state["title"] == "Rent"
