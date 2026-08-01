import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import ActorType, AuditAction, AuditEntityType, AuditLogEntry


class AuditService:
    """Writes the audit trail (FR-029, FR-037). Called by every mutating service —
    manual (REST) and AI paths alike — so no create/update/delete can skip it."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record(
        self,
        *,
        actor_type: ActorType,
        actor_user_id: uuid.UUID,
        entity_type: AuditEntityType,
        entity_id: uuid.UUID,
        action: AuditAction,
        before: dict | None = None,
        after: dict | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_state=before,
            after_state=after,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry
