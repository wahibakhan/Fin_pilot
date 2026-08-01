import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ai_interaction import AIInteraction, AIInteractionStatus


class AIInteractionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, interaction_id: uuid.UUID) -> AIInteraction | None:
        return await self._db.get(AIInteraction, interaction_id)

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_message: str,
        interpreted_intent: dict | None,
        proposed_action: dict | None,
        status: AIInteractionStatus,
        response_message: str | None,
    ) -> AIInteraction:
        interaction = AIInteraction(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            interpreted_intent=interpreted_intent,
            proposed_action=proposed_action,
            status=status,
            response_message=response_message,
        )
        self._db.add(interaction)
        await self._db.flush()
        return interaction

    async def update_status(
        self, interaction: AIInteraction, *, status: AIInteractionStatus, response_message: str | None
    ) -> AIInteraction:
        interaction.status = status
        interaction.response_message = response_message
        await self._db.flush()
        return interaction
