"""Golden-transcript tests: for each example command in spec.md (plus key
edge cases), inject the tool call a correctly-functioning LLM *should*
produce, then verify the graph resolves/dispatches/executes it correctly.
These test the graph's routing and execution against ExpenseService/
IncomeService/ReportService — not an LLM's extraction accuracy, which needs
a live provider and is out of scope here. Require a reachable Postgres
(everything here ultimately touches the DB); skip automatically without one.
"""

from datetime import date
from decimal import Decimal

from langgraph.types import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.graph import build_agent_graph
from src.models.category import Category, CategoryType
from src.models.expense import Expense
from src.models.user import User, UserRole
from src.services.expense_service import ExpenseService
from src.services.income_service import IncomeService
from tests.agent.fakes import FakeNoToolCallModel, FakeToolCallingModel


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(full_name="Test User", email=email, password_hash="x", role=UserRole.BUSINESS_OWNER)
    db.add(user)
    await db.flush()
    return user


async def _make_category(db: AsyncSession, *, name: str) -> Category:
    category = Category(name=name, type=CategoryType.EXPENSE)
    db.add(category)
    await db.flush()
    return category


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


async def test_add_office_rent(db_session: AsyncSession, unique_email: str):
    """'Add office rent 50000 for July.'"""
    user = await _make_user(db_session, email=unique_email)
    await db_session.commit()

    call = {
        "name": "AddExpense",
        "args": {
            "title": "Office Rent",
            "amount": 50000,
            "category": "Rent",
            "date": "2026-07-01",
        },
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    config = _config(f"thread-{unique_email}")

    result = await graph.ainvoke({"user_message": "Add office rent 50000 for July."}, config=config)
    assert "__interrupt__" in result
    assert result["proposed_action"]["title"] == "Office Rent"

    result = await graph.ainvoke(Command(resume=True), config=config)
    assert result["status"] == "confirmed"

    created = (await db_session.execute(select(Expense).where(Expense.title == "Office Rent"))).scalar_one()
    assert created.amount == Decimal("50000.00")
    assert created.created_via.value == "ai"


async def test_add_electricity_bill(db_session: AsyncSession, unique_email: str):
    """'Add electricity bill 12000.'"""
    user = await _make_user(db_session, email=unique_email)
    await db_session.commit()

    call = {
        "name": "AddExpense",
        "args": {"title": "Electricity Bill", "amount": 12000, "category": "Utilities", "date": "2026-07-15"},
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    config = _config(f"thread-{unique_email}")

    await graph.ainvoke({"user_message": "Add electricity bill 12000."}, config=config)
    result = await graph.ainvoke(Command(resume=True), config=config)

    assert result["status"] == "confirmed"
    assert result["response_data"]["title"] == "Electricity Bill"


async def test_generate_profit_and_loss(db_session: AsyncSession, unique_email: str):
    """'Generate Profit and Loss Statement.'"""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Consulting", amount="5000", date=date(2026, 7, 2)
    )

    call = {
        "name": "GenerateReport",
        "args": {"report_type": "profit-and-loss", "date_from": "2026-07-01", "date_to": "2026-07-31"},
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "Generate Profit and Loss Statement."}, config=_config(f"thread-{unique_email}")
    )

    assert "__interrupt__" not in result
    assert result["status"] == "answered"
    assert result["response_data"]["net_profit"] == Decimal("4000.00")


async def test_create_balance_sheet(db_session: AsyncSession, unique_email: str):
    """'Create Balance Sheet.'"""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )

    call = {
        "name": "GenerateReport",
        "args": {"report_type": "balance-sheet", "date_from": "2026-07-01", "date_to": "2026-07-31"},
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "Create Balance Sheet."}, config=_config(f"thread-{unique_email}")
    )

    assert result["response_data"]["total_assets"] == result["response_data"]["total_equity"]


async def test_run_monthly_audit_flags_duplicate(db_session: AsyncSession, unique_email: str):
    """'Run monthly audit.'"""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    await service.create_expense(
        actor=user, title="Rent A", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )
    await service.create_expense(
        actor=user, title="Rent B", amount="1000", category_id=category.id, date=date(2026, 7, 2)
    )

    call = {"name": "RunAudit", "args": {"date_from": "2026-07-01", "date_to": "2026-07-31"}, "id": "1"}
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "Run monthly audit."}, config=_config(f"thread-{unique_email}")
    )

    assert len(result["response_data"]["duplicates"]) == 1


async def test_show_top_five_expenses(db_session: AsyncSession, unique_email: str):
    """'Show top five expenses.'"""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Misc-{unique_email[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    for i, amount in enumerate([100, 900, 300, 700, 500, 200], start=1):
        await service.create_expense(
            actor=user, title=f"Expense {i}", amount=str(amount), category_id=category.id, date=date(2026, 7, i)
        )

    call = {
        "name": "TopExpenses",
        "args": {"n": 5, "date_from": "2026-07-01", "date_to": "2026-07-31"},
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "Show top five expenses."}, config=_config(f"thread-{unique_email}")
    )

    amounts = [item["amount"] for item in result["response_data"]["items"]]
    assert amounts == ["900.00", "700.00", "500.00", "300.00", "200.00"]


async def test_compare_june_and_july_expenses(db_session: AsyncSession, unique_email: str):
    """'Compare June and July expenses.'"""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    await service.create_expense(
        actor=user, title="June Rent", amount="1000", category_id=category.id, date=date(2026, 6, 15)
    )
    await service.create_expense(
        actor=user, title="July Rent", amount="1500", category_id=category.id, date=date(2026, 7, 15)
    )

    call = {
        "name": "ComparePeriods",
        "args": {
            "period_a_from": "2026-06-01",
            "period_a_to": "2026-06-30",
            "period_b_from": "2026-07-01",
            "period_b_to": "2026-07-31",
        },
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "Compare June and July expenses."}, config=_config(f"thread-{unique_email}")
    )

    data = result["response_data"]
    assert data["period_a"]["total"] == "1000.00"
    assert data["period_b"]["total"] == "1500.00"
    assert data["delta"] == "500.00"


async def test_utilities_spend_in_march(db_session: AsyncSession, unique_email: str):
    """'How much did we spend on utilities in March?'"""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name="Utilities")
    await db_session.commit()
    await ExpenseService(db_session).create_expense(
        actor=user, title="Water Bill", amount="300", category_id=category.id, date=date(2026, 3, 10)
    )

    call = {
        "name": "CategoryTotal",
        "args": {"category": "Utilities", "date_from": "2026-03-01", "date_to": "2026-03-31"},
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "How much did we spend on utilities in March?"},
        config=_config(f"thread-{unique_email}"),
    )

    assert result["response_data"]["total"] == "300.00"


async def test_net_profit_last_month(db_session: AsyncSession, unique_email: str):
    """'What was our net profit last month?'"""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    await ExpenseService(db_session).create_expense(
        actor=user, title="Rent", amount="1000", category_id=category.id, date=date(2026, 6, 1)
    )
    await IncomeService(db_session).create_income(
        actor=user, source="Sales", amount="3000", date=date(2026, 6, 2)
    )

    call = {
        "name": "NetProfitQuery",
        "args": {"date_from": "2026-06-01", "date_to": "2026-06-30"},
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "What was our net profit last month?"}, config=_config(f"thread-{unique_email}")
    )

    assert result["response_data"]["net_profit"] == "2000.00"


async def test_missing_amount_triggers_clarification_not_creation(
    db_session: AsyncSession, unique_email: str
):
    """Edge case: 'Add an expense' with no amount — model should choose
    AskClarification rather than guessing (FR-028)."""
    user = await _make_user(db_session, email=unique_email)
    await db_session.commit()

    call = {"name": "AskClarification", "args": {"question": "What's the amount?"}, "id": "1"}
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "Add an expense"}, config=_config(f"thread-{unique_email}")
    )

    assert result["status"] == "clarification_requested"
    assert "__interrupt__" not in result

    count = (await db_session.execute(select(Expense))).scalars().all()
    assert count == []


async def test_ambiguous_delete_asks_to_disambiguate(db_session: AsyncSession, unique_email: str):
    """Edge case: 'delete the rent expense' with two matching expenses."""
    user = await _make_user(db_session, email=unique_email)
    category = await _make_category(db_session, name=f"Rent-{unique_email[:6]}")
    await db_session.commit()
    service = ExpenseService(db_session)
    await service.create_expense(
        actor=user, title="Rent June", amount="1000", category_id=category.id, date=date(2026, 6, 1)
    )
    await service.create_expense(
        actor=user, title="Rent July", amount="1000", category_id=category.id, date=date(2026, 7, 1)
    )

    call = {"name": "DeleteExpense", "args": {"search_text": "Rent"}, "id": "1"}
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    result = await graph.ainvoke(
        {"user_message": "delete the rent expense"}, config=_config(f"thread-{unique_email}")
    )

    assert result["status"] == "clarification_requested"
    assert "__interrupt__" not in result

    remaining = (await db_session.execute(select(Expense).where(Expense.deleted_at.is_(None)))).scalars().all()
    assert len(remaining) == 2


async def test_rejecting_a_proposed_expense_creates_nothing(db_session: AsyncSession, unique_email: str):
    user = await _make_user(db_session, email=unique_email)
    await db_session.commit()

    call = {
        "name": "AddExpense",
        "args": {"title": "Should Not Exist", "amount": 999, "category": "Misc", "date": "2026-07-01"},
        "id": "1",
    }
    graph = build_agent_graph(chat_model=FakeToolCallingModel(call), db=db_session, actor=user)
    config = _config(f"thread-{unique_email}")
    await graph.ainvoke({"user_message": "Add a misc expense 999"}, config=config)

    result = await graph.ainvoke(Command(resume=False), config=config)

    assert result["status"] == "rejected"
    found = (
        await db_session.execute(select(Expense).where(Expense.title == "Should Not Exist"))
    ).scalars().all()
    assert found == []


async def test_no_tool_call_falls_back_to_clarification(db_session: AsyncSession, unique_email: str):
    """When the model replies in plain text instead of picking a tool."""
    user = await _make_user(db_session, email=unique_email)
    await db_session.commit()

    graph = build_agent_graph(
        chat_model=FakeNoToolCallModel("I'm not sure what you mean."), db=db_session, actor=user
    )
    result = await graph.ainvoke(
        {"user_message": "asdf"}, config=_config(f"thread-{unique_email}")
    )

    assert result["status"] == "clarification_requested"
    assert result["response_message"] == "I'm not sure what you mean."
