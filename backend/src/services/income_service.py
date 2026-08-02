import uuid
from datetime import date as date_
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from src.core.money import parse_amount
from src.models.audit_log import ActorType, AuditAction, AuditEntityType
from src.models.expense import CreatedVia
from src.models.income import Income
from src.models.user import User, UserRole
from src.repositories.income_repository import IncomeRepository
from src.services.audit_service import AuditService
from src.services.journal_service import JournalService

_ROLES_THAT_CAN_DELETE = {UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT}


def _serialize(income: Income) -> dict:
    return {
        "id": str(income.id),
        "source": income.source,
        "amount": str(income.amount),
        "date": income.date.isoformat(),
        "description": income.description,
    }


class IncomeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._income = IncomeRepository(db)
        self._audit = AuditService(db)
        self._journal = JournalService(db)

    async def list_income(
        self,
        *,
        q: str | None = None,
        date_from: date_ | None = None,
        date_to: date_ | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Income], int]:
        return await self._income.list(
            q=q, date_from=date_from, date_to=date_to, page=page, page_size=page_size
        )

    async def get_income(self, income_id: uuid.UUID) -> Income:
        income = await self._income.get_active(income_id)
        if income is None:
            raise NotFoundError("Income entry not found")
        return income

    async def create_income(
        self,
        *,
        actor: User,
        source: str,
        amount,
        date: date_,
        description: str | None = None,
        created_via: CreatedVia = CreatedVia.MANUAL,
    ) -> Income:
        amount = parse_amount(amount)
        await self._validate_source(source)

        income = await self._income.create(
            source=source,
            amount=amount,
            date=date,
            description=description,
            created_by=actor.id,
            created_via=created_via,
        )

        await self._audit.record(
            actor_type=ActorType.AI if created_via == CreatedVia.AI else ActorType.USER,
            actor_user_id=actor.id,
            entity_type=AuditEntityType.INCOME,
            entity_id=income.id,
            action=AuditAction.CREATE,
            before=None,
            after=_serialize(income),
        )
        await self._journal.post_income(
            income_id=income.id, amount=income.amount, entry_date=income.date, direction="post"
        )
        await self._db.commit()
        return income

    async def update_income(
        self,
        *,
        actor: User,
        income_id: uuid.UUID,
        source: str | None = None,
        amount=None,
        date: date_ | None = None,
        description: str | None = None,
    ) -> Income:
        income = await self.get_income(income_id)
        before = _serialize(income)

        fields: dict = {}
        if source is not None:
            await self._validate_source(source)
            fields["source"] = source
        if amount is not None:
            fields["amount"] = parse_amount(amount)
        if date is not None:
            fields["date"] = date
        if description is not None:
            fields["description"] = description

        income = await self._income.update(income, **fields)

        await self._audit.record(
            actor_type=ActorType.USER,
            actor_user_id=actor.id,
            entity_type=AuditEntityType.INCOME,
            entity_id=income.id,
            action=AuditAction.UPDATE,
            before=before,
            after=_serialize(income),
        )
        await self._journal.post_income(
            income_id=income.id,
            amount=Decimal(before["amount"]),
            entry_date=date_.fromisoformat(before["date"]),
            direction="reverse",
        )
        await self._journal.post_income(
            income_id=income.id, amount=income.amount, entry_date=income.date, direction="post"
        )
        await self._db.commit()
        return income

    async def delete_income(self, *, actor: User, income_id: uuid.UUID) -> None:
        if actor.role not in _ROLES_THAT_CAN_DELETE:
            raise PermissionDeniedError(
                f"Role '{actor.role.value}' is not permitted to delete income entries"
            )

        income = await self.get_income(income_id)
        before = _serialize(income)

        await self._income.soft_delete(income)

        await self._audit.record(
            actor_type=ActorType.USER,
            actor_user_id=actor.id,
            entity_type=AuditEntityType.INCOME,
            entity_id=income.id,
            action=AuditAction.DELETE,
            before=before,
            after=None,
        )
        await self._journal.post_income(
            income_id=income.id,
            amount=Decimal(before["amount"]),
            entry_date=date_.fromisoformat(before["date"]),
            direction="reverse",
        )
        await self._db.commit()

    async def _validate_source(self, source: str) -> None:
        if not source or not source.strip():
            raise ValidationError("Source is required", field="source")
