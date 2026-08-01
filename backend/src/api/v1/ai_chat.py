import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db
from src.models.user import User
from src.schemas.ai_chat import AIChatRequest, AIChatResponse
from src.services.ai_chat_service import AIChatService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    payload: AIChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIChatResponse:
    result = await AIChatService(db).send_message(
        actor=current_user, message=payload.message, conversation_id=payload.conversation_id
    )
    return AIChatResponse.model_validate(result)


@router.post("/interactions/{interaction_id}/confirm", response_model=AIChatResponse)
async def confirm_interaction(
    interaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIChatResponse:
    result = await AIChatService(db).confirm(actor=current_user, interaction_id=interaction_id)
    return AIChatResponse.model_validate(result)


@router.post("/interactions/{interaction_id}/reject", response_model=AIChatResponse)
async def reject_interaction(
    interaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIChatResponse:
    result = await AIChatService(db).reject(actor=current_user, interaction_id=interaction_id)
    return AIChatResponse.model_validate(result)
