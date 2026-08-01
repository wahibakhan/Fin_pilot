import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditEntityType, AuditLogEntry


class AuditLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        *,
        entity_type: AuditEntityType | None = None,
        entity_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[AuditLogEntry], int]:
        stmt = select(AuditLogEntry)
        if entity_type is not None:
            stmt = stmt.where(AuditLogEntry.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditLogEntry.entity_id == entity_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(AuditLogEntry.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all()), total
