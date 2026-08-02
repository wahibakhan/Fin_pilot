"""The agent's StateGraph: interpret -> plan -> confirm(interrupt) -> execute
-> respond, with a clarify escape hatch from either interpret or plan.

`confirm` is a real LangGraph `interrupt()` — the graph genuinely pauses
there and returns control to the caller; nothing after it runs until a
second invocation supplies `Command(resume=...)` with the same thread_id.
That structural pause is what makes FR-027 ("propose, don't commit") a
property of the graph rather than a convention callers might skip.
"""

import uuid
from datetime import UTC, date, datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent import intents
from src.agent.prompts import build_system_prompt
from src.agent.state import AgentState
from src.agent.tools import analysis_tool, audit_tool, crud_tool, report_tool
from src.models.user import User

# Module-level singleton: an unconfirmed proposal must still be resumable by
# a *second*, separate HTTP request (POST /ai/interactions/{id}/confirm).
# In-memory means this doesn't survive a process restart — acceptable, since
# an interrupted-and-abandoned proposal is meant to expire anyway.
_checkpointer = MemorySaver()


def build_agent_graph(*, chat_model: BaseChatModel, db: AsyncSession, actor: User):
    model_with_tools = chat_model.bind_tools(intents.ALL_INTENT_TYPES)

    async def interpret(state: AgentState) -> dict:
        system = SystemMessage(
            build_system_prompt(
                role=actor.role.value, today=datetime.now(UTC).date().isoformat()
            )
        )
        # state["messages"] already includes the current turn's HumanMessage
        # (merged in by the add_messages reducer from the ainvoke() input)
        # plus every prior turn in this conversation/thread_id.
        history = state.get("messages", [])
        response = await model_with_tools.ainvoke([system, *history])

        # interpret() is the entry point for every new turn (a resumed
        # interrupt re-enters at confirm(), never here). AgentState's scalar
        # fields have no reducer, so without an explicit reset, a completed
        # or aborted previous turn's leftover status/tool_name/etc. survive
        # in the checkpoint and can silently override this turn's routing —
        # e.g. a stale "clarification_requested" status persisting even
        # after this turn resolves to a real tool call.
        reset: dict = {
            "interpreted_intent": None,
            "tool_name": None,
            "tool_args": None,
            "action_kind": None,
            "proposed_action": None,
            "confirmed": None,
            "status": None,
            "response_message": None,
            "response_data": None,
        }

        if not response.tool_calls:
            content = response.content or "Could you clarify what you'd like me to do?"
            return {
                **reset,
                "status": "clarification_requested",
                "response_message": content,
                "messages": [AIMessage(content=content)],
            }

        call = response.tool_calls[0]
        return {
            **reset,
            "interpreted_intent": {"name": call["name"], "args": call["args"]},
            "tool_name": call["name"],
            "tool_args": call["args"],
        }

    def route_after_interpret(state: AgentState) -> str:
        if state.get("status") == "clarification_requested":
            return "clarify"
        if state.get("tool_name") == "AskClarification":
            return "clarify"
        return "plan"

    async def clarify(state: AgentState) -> dict:
        if state.get("tool_name") == "AskClarification":
            question = (state.get("tool_args") or {}).get(
                "question", "Could you clarify what you'd like me to do?"
            )
            return {
                "status": "clarification_requested",
                "response_message": question,
                "messages": [AIMessage(content=question)],
            }
        # interpret() already appended its own clarifying message when it
        # returned with no tool call.
        return {"status": "clarification_requested"}

    async def plan(state: AgentState) -> dict:
        name = state["tool_name"]
        args = state["tool_args"] or {}

        if name not in intents.WRITE_INTENTS:
            return {"action_kind": "read"}

        if name == "DeleteExpense":
            try:
                expense = await crud_tool.resolve_expense_by_description(db, args["search_text"])
            except crud_tool.AmbiguousMatchError as exc:
                return {"status": "clarification_requested", "response_message": exc.question}
            except crud_tool.NoMatchError as exc:
                return {"status": "clarification_requested", "response_message": str(exc)}
            proposed = {
                "action": "delete_expense",
                "expense_id": str(expense.id),
                "title": expense.title,
                "amount": str(expense.amount),
                "date": expense.date.isoformat(),
            }
        elif name == "AddExpense":
            proposed = {"action": "add_expense", **args}
        elif name == "AddIncome":
            proposed = {"action": "add_income", **args}
        else:
            proposed = {"action": name, **args}

        return {"action_kind": "write", "proposed_action": proposed}

    def route_after_plan(state: AgentState) -> str:
        if state.get("status") == "clarification_requested":
            return "clarify"
        return "confirm" if state.get("action_kind") == "write" else "execute"

    async def confirm(state: AgentState) -> dict:
        decision = interrupt(
            {"proposed_action": state.get("proposed_action"), "tool_name": state.get("tool_name")}
        )
        if not decision:
            return {
                "confirmed": False,
                "status": "rejected",
                "response_message": "Okay, I won't make that change.",
            }
        return {"confirmed": True}

    def route_after_confirm(state: AgentState) -> str:
        return "execute" if state.get("confirmed") else "respond"

    async def execute(state: AgentState) -> dict:
        name = state["tool_name"]
        args = state["tool_args"] or {}

        try:
            data, message = await _dispatch(
                db=db, actor=actor, name=name, args=args, proposed_action=state.get("proposed_action")
            )
            status = "confirmed" if name in intents.WRITE_INTENTS else "answered"
        except Exception as exc:
            data, message, status = None, f"Sorry, something went wrong: {exc}", "answered"

        return {"response_data": data, "response_message": message, "status": status}

    async def respond(state: AgentState) -> dict:
        message = state.get("response_message") or "Done."
        return {"response_message": message, "messages": [AIMessage(content=message)]}

    graph = StateGraph(AgentState)
    graph.add_node("interpret", interpret)
    graph.add_node("clarify", clarify)
    graph.add_node("plan", plan)
    graph.add_node("confirm", confirm)
    graph.add_node("execute", execute)
    graph.add_node("respond", respond)

    graph.add_edge(START, "interpret")
    graph.add_conditional_edges("interpret", route_after_interpret, ["clarify", "plan"])
    graph.add_conditional_edges("plan", route_after_plan, ["clarify", "confirm", "execute"])
    graph.add_conditional_edges("confirm", route_after_confirm, ["execute", "respond"])
    graph.add_edge("clarify", END)
    graph.add_edge("execute", "respond")
    graph.add_edge("respond", END)

    return graph.compile(checkpointer=_checkpointer)


async def _dispatch(
    *, db: AsyncSession, actor: User, name: str, args: dict, proposed_action: dict | None
) -> tuple[dict | None, str]:
    if name == "AddExpense":
        expense = await crud_tool.add_expense(db, actor=actor, args=intents.AddExpense(**args))
        flags = await audit_tool.check_expense_for_flags(db, expense)
        message = f"Added expense '{expense.title}' for {expense.amount} on {expense.date}."
        if flags:
            message += " " + " ".join(f["message"] for f in flags)
        return (
            {
                "id": str(expense.id),
                "title": expense.title,
                "amount": str(expense.amount),
                "date": expense.date.isoformat(),
                "flags": flags,
            },
            message,
        )

    if name == "AddIncome":
        income = await crud_tool.add_income(db, actor=actor, args=intents.AddIncome(**args))
        return (
            {"id": str(income.id), "source": income.source, "amount": str(income.amount)},
            f"Added income '{income.source}' for {income.amount} on {income.date}.",
        )

    if name == "DeleteExpense":
        expense_id = uuid.UUID((proposed_action or {})["expense_id"])
        expense = await crud_tool.delete_expense(db, actor=actor, expense_id=expense_id)
        return {"deleted_expense_id": str(expense.id)}, f"Deleted expense '{expense.title}'."

    if name == "GenerateReport":
        result = await report_tool.generate_report(
            db,
            report_type=args["report_type"],
            date_from=date.fromisoformat(args["date_from"]),
            date_to=date.fromisoformat(args["date_to"]),
        )
        return result["report"], result["explanation"]

    if name == "TopExpenses":
        result = await analysis_tool.top_expenses(
            db,
            n=args.get("n", 5),
            date_from=date.fromisoformat(args["date_from"]),
            date_to=date.fromisoformat(args["date_to"]),
        )
        items_desc = "; ".join(f"{i['title']} ({i['amount']})" for i in result["items"])
        return result, f"Top {result['count']} expenses: {items_desc}"

    if name == "ComparePeriods":
        result = await analysis_tool.compare_periods(
            db,
            period_a_from=date.fromisoformat(args["period_a_from"]),
            period_a_to=date.fromisoformat(args["period_a_to"]),
            period_b_from=date.fromisoformat(args["period_b_from"]),
            period_b_to=date.fromisoformat(args["period_b_to"]),
        )
        message = (
            f"Period A total: {result['period_a']['total']}, "
            f"Period B total: {result['period_b']['total']}, change: {result['delta']}."
        )
        return result, message

    if name == "CategoryTotal":
        result = await analysis_tool.category_total(
            db,
            category=args["category"],
            date_from=date.fromisoformat(args["date_from"]),
            date_to=date.fromisoformat(args["date_to"]),
        )
        return result, f"You spent {result['total']} on {result['category']} in that period."

    if name == "NetProfitQuery":
        result = await analysis_tool.net_profit(
            db,
            date_from=date.fromisoformat(args["date_from"]),
            date_to=date.fromisoformat(args["date_to"]),
        )
        return result, f"Net profit was {result['net_profit']}."

    if name == "RunAudit":
        result = await audit_tool.run_audit(
            db,
            date_from=date.fromisoformat(args["date_from"]),
            date_to=date.fromisoformat(args["date_to"]),
        )
        n_dup, n_large = len(result["duplicates"]), len(result["large_expenses"])
        message = (
            f"Audit complete: {n_dup} possible duplicate(s), {n_large} unusually large "
            "expense(s) found."
            if (n_dup or n_large)
            else "Audit complete: no anomalies found."
        )
        return result, message

    return None, "I'm not able to help with that yet."


def new_conversation_id() -> uuid.UUID:
    return uuid.uuid4()


def utcnow() -> datetime:
    return datetime.now(UTC)
