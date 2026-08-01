import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, require_role
from src.models.audit_log import AuditEntityType
from src.models.user import User, UserRole
from src.repositories.audit_log_repository import AuditLogRepository
from src.schemas.audit_log import AuditLogEntry, AuditLogPage

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

_OWNER_OR_ACCOUNTANT = require_role(UserRole.BUSINESS_OWNER, UserRole.ACCOUNTANT)


@router.get("", response_model=AuditLogPage)
async def list_audit_logs(
    entity_type: AuditEntityType | None = None,
    entity_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(_OWNER_OR_ACCOUNTANT),
) -> AuditLogPage:
    items, total = await AuditLogRepository(db).list(
        entity_type=entity_type, entity_id=entity_id, page=page, page_size=page_size
    )
    return AuditLogPage(
        items=[AuditLogEntry.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
