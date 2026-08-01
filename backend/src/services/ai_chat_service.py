import uuid

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.graph import build_agent_graph
from src.agent.provider import AIProviderError, get_chat_model
from src.core.exceptions import AIServiceUnavailableError, ConflictError, NotFoundError
from src.models.ai_interaction import AIInteractionStatus
from src.models.user import User
from src.repositories.ai_interaction_repository import AIInteractionRepository


def _describe_proposal(tool_name: str | None, proposed_action: dict | None) -> str:
    proposed_action = proposed_action or {}
    if tool_name == "AddExpense":
        return (
            f"I'll add an expense: '{proposed_action.get('title')}' for "
            f"{proposed_action.get('amount')} on {proposed_action.get('date')} "
            f"(category: {proposed_action.get('category')}). Confirm?"
        )
    if tool_name == "AddIncome":
        return (
            f"I'll add income: '{proposed_action.get('source')}' for "
            f"{proposed_action.get('amount')} on {proposed_action.get('date')}. Confirm?"
        )
    if tool_name == "DeleteExpense":
        return (
            f"I'll delete the expense '{proposed_action.get('title')}' "
            f"({proposed_action.get('amount')} on {proposed_action.get('date')}). Confirm?"
        )
    return "I have a proposed action ready. Confirm?"


class AIChatService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._interactions = AIInteractionRepository(db)

    async def send_message(
        self, *, actor: User, message: str, conversation_id: uuid.UUID | None
    ) -> dict:
        conversation_id = conversation_id or uuid.uuid4()
        graph = self._build_graph(actor)

        config = {"configurable": {"thread_id": str(conversation_id)}}
        result = await self._invoke_graph(
            graph,
            {"user_message": message, "messages": [HumanMessage(content=message)]},
            config=config,
        )

        if "__interrupt__" in result:
            status = AIInteractionStatus.PROPOSED
            proposed_action = result.get("proposed_action")
            response_message = _describe_proposal(result.get("tool_name"), proposed_action)
            data = None
        else:
            status = AIInteractionStatus(result.get("status", "answered"))
            proposed_action = None
            response_message = result.get("response_message") or "Done."
            data = result.get("response_data")

        interaction = await self._interactions.create(
            user_id=actor.id,
            conversation_id=conversation_id,
            user_message=message,
            interpreted_intent=result.get("interpreted_intent"),
            proposed_action=proposed_action,
            status=status,
            response_message=response_message,
        )
        await self._db.commit()

        return self._to_response(interaction, data=data)

    async def confirm(self, *, actor: User, interaction_id: uuid.UUID) -> dict:
        return await self._resolve(actor=actor, interaction_id=interaction_id, decision=True)

    async def reject(self, *, actor: User, interaction_id: uuid.UUID) -> dict:
        return await self._resolve(actor=actor, interaction_id=interaction_id, decision=False)

    async def _resolve(self, *, actor: User, interaction_id: uuid.UUID, decision: bool) -> dict:
        interaction = await self._interactions.get(interaction_id)
        if interaction is None:
            raise NotFoundError("AI interaction not found")
        if interaction.status != AIInteractionStatus.PROPOSED:
            raise ConflictError("This interaction has already been resolved or expired.")

        graph = self._build_graph(actor)
        config = {"configurable": {"thread_id": str(interaction.conversation_id)}}
        result = await self._invoke_graph(graph, Command(resume=decision), config=config)

        default_status = "confirmed" if decision else "rejected"
        status = AIInteractionStatus(result.get("status", default_status))
        response_message = result.get("response_message") or "Done."
        data = result.get("response_data")

        await self._interactions.update_status(
            interaction, status=status, response_message=response_message
        )
        await self._db.commit()

        return self._to_response(interaction, data=data)

    def _build_graph(self, actor: User):
        try:
            chat_model = get_chat_model()
        except AIProviderError as exc:
            raise AIServiceUnavailableError(str(exc)) from exc

        return build_agent_graph(chat_model=chat_model, db=self._db, actor=actor)

    @staticmethod
    async def _invoke_graph(graph, input_, *, config: dict) -> dict:
        """Runs the graph, degrading provider failures (rate limits, outages,
        auth errors) to AIServiceUnavailableError instead of a raw 500.
        Business-logic errors from _dispatch are already handled inside the
        execute() node itself, so anything reaching this far is either a
        provider call failure or a genuine bug — both should fail as
        "AI unavailable, use manual entry" rather than crash the request.
        """
        try:
            return await graph.ainvoke(input_, config=config)
        except Exception as exc:
            raise AIServiceUnavailableError(
                "The AI provider is temporarily unavailable. Please try again in a "
                "moment or use manual entry."
            ) from exc

    @staticmethod
    def _to_response(interaction, *, data: dict | None) -> dict:
        return {
            "interaction_id": interaction.id,
            "conversation_id": interaction.conversation_id,
            "status": interaction.status.value,
            "message": interaction.response_message or "Done.",
            "proposed_action": interaction.proposed_action,
            "data": data,
        }
