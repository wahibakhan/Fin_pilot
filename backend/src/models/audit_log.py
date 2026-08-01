import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ActorType(StrEnum):
    USER = "user"
    AI = "ai"


class AuditEntityType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    CATEGORY = "category"
    USER = "user"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"
    __table_args__ = (
        Index("ix_audit_log_entries_entity_type_entity_id", "entity_type", "entity_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_type: Mapped[ActorType] = mapped_column(
        PgEnum(
            ActorType,
            name="actor_type",
            create_type=True,
            inherit_schema=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    entity_type: Mapped[AuditEntityType] = mapped_column(
        PgEnum(
            AuditEntityType,
            name="audit_entity_type",
            create_type=True,
            inherit_schema=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    action: Mapped[AuditAction] = mapped_column(
        PgEnum(
            AuditAction,
            name="audit_action",
            create_type=True,
            inherit_schema=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    before_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
