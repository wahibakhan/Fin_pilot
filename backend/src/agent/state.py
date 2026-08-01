from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    # Full conversation history for this thread_id. The `add_messages`
    # reducer appends new messages across separate ainvoke() calls (each
    # /ai/chat request) instead of the checkpointer overwriting it — without
    # this, a clarification follow-up ("August 1st") has no memory of the
    # turn that prompted it ("add office rent 5000").
    messages: Annotated[list[BaseMessage], add_messages]
    user_message: str
    interpreted_intent: dict[str, Any] | None
    tool_name: str | None
    tool_args: dict[str, Any] | None
    action_kind: str | None  # "write" | "read"
    proposed_action: dict[str, Any] | None
    confirmed: bool | None
    status: str  # mirrors AIInteractionStatus values
    response_message: str | None
    response_data: dict[str, Any] | None
