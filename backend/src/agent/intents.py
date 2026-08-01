"""Pydantic tool schemas the LLM chooses from via `bind_tools()`. Each one is a
structured "intent" — the model never free-forms a database action, it can
only pick one of these named, typed shapes."""

from pydantic import BaseModel, Field

REPORT_TYPES = (
    "profit-and-loss",
    "balance-sheet",
    "trial-balance",
    "cash-flow",
    "monthly-expenses",
    "income",
    "category-expenses",
)


class AddExpense(BaseModel):
    """Create a new expense record."""

    title: str = Field(description="Short title for the expense, e.g. 'Office Rent'")
    amount: float = Field(description="Amount as a positive number")
    category: str = Field(description="Expense category name, e.g. 'Rent', 'Utilities'")
    date: str = Field(description="ISO date (YYYY-MM-DD) the expense occurred")
    description: str | None = Field(default=None)


class AddIncome(BaseModel):
    """Create a new income record."""

    source: str = Field(description="Where the income came from, e.g. 'Consulting Fee'")
    amount: float = Field(description="Amount as a positive number")
    date: str = Field(description="ISO date (YYYY-MM-DD) the income was received")
    description: str | None = Field(default=None)


class DeleteExpense(BaseModel):
    """Delete an existing expense identified by a text description of it."""

    search_text: str = Field(description="Words identifying which expense, e.g. 'the rent expense'")


class GenerateReport(BaseModel):
    """Generate one of the standard financial reports for a period."""

    report_type: str = Field(description=f"One of: {', '.join(REPORT_TYPES)}")
    date_from: str = Field(description="ISO date (YYYY-MM-DD)")
    date_to: str = Field(description="ISO date (YYYY-MM-DD)")


class TopExpenses(BaseModel):
    """Show the N largest expenses in a period."""

    n: int = Field(default=5)
    date_from: str
    date_to: str


class ComparePeriods(BaseModel):
    """Compare total expenses between two periods."""

    period_a_from: str
    period_a_to: str
    period_b_from: str
    period_b_to: str


class CategoryTotal(BaseModel):
    """Answer 'how much did we spend on <category> in <period>'."""

    category: str
    date_from: str
    date_to: str


class NetProfitQuery(BaseModel):
    """Answer 'what was our net profit for <period>'."""

    date_from: str
    date_to: str


class RunAudit(BaseModel):
    """Run a duplicate/anomaly/large-expense audit over a period."""

    date_from: str
    date_to: str


class AskClarification(BaseModel):
    """Choose this when the request is missing information needed to act, or
    is ambiguous — ask a specific, short follow-up question instead of
    guessing."""

    question: str


WRITE_INTENTS = {"AddExpense", "AddIncome", "DeleteExpense"}
READ_INTENTS = {
    "GenerateReport",
    "TopExpenses",
    "ComparePeriods",
    "CategoryTotal",
    "NetProfitQuery",
    "RunAudit",
}

ALL_INTENT_TYPES: list[type[BaseModel]] = [
    AddExpense,
    AddIncome,
    DeleteExpense,
    GenerateReport,
    TopExpenses,
    ComparePeriods,
    CategoryTotal,
    NetProfitQuery,
    RunAudit,
    AskClarification,
]
