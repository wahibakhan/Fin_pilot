import uuid
from typing import Any, Literal

from pydantic import BaseModel

InteractionStatus = Literal[
    "proposed", "confirmed", "rejected", "expired", "clarification_requested", "answered"
]


class AIChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None


class AIChatResponse(BaseModel):
    interaction_id: uuid.UUID
    conversation_id: uuid.UUID
    status: InteractionStatus
    message: str
    proposed_action: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
