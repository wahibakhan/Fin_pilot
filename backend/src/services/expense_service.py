import uuid
from datetime import date as date_
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.models.audit_log import ActorType, AuditAction, AuditEntityType
from src.models.expense import CreatedVia, Expense
from src.models.user import User, UserRole
from src.repositories.category_repository import CategoryRepository
from src.repositories.expense_repository import ExpenseRepository
from src.services.audit_service import AuditService
from src.services.journal_service import JournalService

_ROLES_THAT_CAN_DELETE = {UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT}


def _serialize(expense: Expense) -> dict:
    return {
        "id": str(expense.id),
        "title": expense.title,
        "amount": str(expense.amount),
        "category_id": str(expense.category_id),
        "date": expense.date.isoformat(),
        "description": expense.description,
    }


class ExpenseService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._expenses = ExpenseRepository(db)
        self._categories = CategoryRepository(db)
        self._audit = AuditService(db)
        self._journal = JournalService(db)

    async def list_expenses(
        self,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        date_from: date_ | None = None,
        date_to: date_ | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Expense], int]:
        return await self._expenses.list(
            q=q,
            category_id=category_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )

    async def get_expense(self, expense_id: uuid.UUID) -> Expense:
        expense = await self._expenses.get_active(expense_id)
        if expense is None:
            raise NotFoundError("Expense not found")
        return expense

    async def create_expense(
        self,
        *,
        actor: User,
        title: str,
        amount,
        category_id: uuid.UUID,
        date: date_,
        description: str | None = None,
        created_via: CreatedVia = CreatedVia.MANUAL,
    ) -> Expense:
        await self._validate_amount(amount)
        await self._validate_title(title)
        await self._validate_category(category_id)

        expense = await self._expenses.create(
            title=title,
            amount=amount,
            category_id=category_id,
            date=date,
            description=description,
            created_by=actor.id,
            created_via=created_via,
        )

        await self._audit.record(
            actor_type=ActorType.AI if created_via == CreatedVia.AI else ActorType.USER,
            actor_user_id=actor.id,
            entity_type=AuditEntityType.EXPENSE,
            entity_id=expense.id,
            action=AuditAction.CREATE,
            before=None,
            after=_serialize(expense),
        )
        await self._journal.post_expense(
            expense_id=expense.id, amount=expense.amount, entry_date=expense.date, direction="post"
        )
        await self._db.commit()
        return expense

    async def update_expense(
        self,
        *,
        actor: User,
        expense_id: uuid.UUID,
        title: str | None = None,
        amount=None,
        category_id: uuid.UUID | None = None,
        date: date_ | None = None,
        description: str | None = None,
    ) -> Expense:
        expense = await self.get_expense(expense_id)
        before = _serialize(expense)

        fields: dict = {}
        if title is not None:
            await self._validate_title(title)
            fields["title"] = title
        if amount is not None:
            await self._validate_amount(amount)
            fields["amount"] = amount
        if category_id is not None:
            await self._validate_category(category_id)
            fields["category_id"] = category_id
        if date is not None:
            fields["date"] = date
        if description is not None:
            fields["description"] = description

        expense = await self._expenses.update(expense, **fields)

        await self._audit.record(
            actor_type=ActorType.USER,
            actor_user_id=actor.id,
            entity_type=AuditEntityType.EXPENSE,
            entity_id=expense.id,
            action=AuditAction.UPDATE,
            before=before,
            after=_serialize(expense),
        )
        # Reverse the original posting, then post fresh — simplest way to stay
        # correct across amount/date changes without conditional journal logic.
        await self._journal.post_expense(
            expense_id=expense.id,
            amount=Decimal(before["amount"]),
            entry_date=date_.fromisoformat(before["date"]),
            direction="reverse",
        )
        await self._journal.post_expense(
            expense_id=expense.id, amount=expense.amount, entry_date=expense.date, direction="post"
        )
        await self._db.commit()
        return expense

    async def delete_expense(self, *, actor: User, expense_id: uuid.UUID) -> None:
        if actor.role not in _ROLES_THAT_CAN_DELETE:
            raise PermissionDeniedError(
                f"Role '{actor.role.value}' is not permitted to delete expenses"
            )

        expense = await self.get_expense(expense_id)
        before = _serialize(expense)

        await self._expenses.soft_delete(expense)

        await self._audit.record(
            actor_type=ActorType.USER,
            actor_user_id=actor.id,
            entity_type=AuditEntityType.EXPENSE,
            entity_id=expense.id,
            action=AuditAction.DELETE,
            before=before,
            after=None,
        )
        await self._journal.post_expense(
            expense_id=expense.id,
            amount=Decimal(before["amount"]),
            entry_date=date_.fromisoformat(before["date"]),
            direction="reverse",
        )
        await self._db.commit()

    async def _validate_amount(self, amount) -> None:
        if amount is None or amount <= 0:
            raise ValidationError("Amount must be greater than 0", field="amount")

    async def _validate_title(self, title: str) -> None:
        if not title or not title.strip():
            raise ValidationError("Title is required", field="title")

    async def _validate_category(self, category_id: uuid.UUID) -> None:
        category = await self._categories.get_by_id(category_id)
        if category is None:
            raise ValidationError("Category does not exist", field="category_id")
        if category.is_archived:
            raise ValidationError("Category is archived and cannot be used", field="category_id")
