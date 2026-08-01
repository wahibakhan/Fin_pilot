import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.models.audit_log import ActorType, AuditAction, AuditEntityType


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_type: ActorType
    actor_user_id: uuid.UUID
    entity_type: AuditEntityType
    entity_id: uuid.UUID
    action: AuditAction
    before_state: dict | None
    after_state: dict | None
    created_at: datetime


class AuditLogPage(BaseModel):
    items: list[AuditLogEntry]
    total: int
    page: int
    page_size: int
