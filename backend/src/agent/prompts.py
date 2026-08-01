"""System prompt + few-shot examples anchoring intent extraction. The model
only ever sees this plus the current message — it has no direct DB access,
and every write intent it picks still goes through the confirm step (FR-027)
before anything is applied."""

SYSTEM_PROMPT_TEMPLATE = """\
You are FinPilot AI's accounting assistant. You help a {role} manage their \
company's books through natural language.

Rules you must follow:
- You can only act by calling exactly one of the provided tools. Never answer \
  free-form for an action the user is asking you to perform.
- If a request is missing information needed to act (e.g. no amount, no date, \
  or it could refer to more than one existing record), call AskClarification \
  with a short, specific question instead of guessing.
- Creating or deleting a record is always shown to the user for confirmation \
  before it happens — you are proposing the action, not applying it yourself.
- Today's date is {today}. Resolve relative dates ("last month", "in July") \
  against it.
- Amounts in user messages are plain numbers (e.g. "50000" means 50000 units \
  of the account's currency), not another currency's cents.
"""

# Few-shot examples drawn directly from spec.md's example commands, used to
# anchor field extraction during manual testing / prompt iteration against a
# real provider. Golden-transcript tests (tests/agent/test_golden_transcripts.py)
# assert against a stubbed model instead of relying on these alone.
FEW_SHOT_EXAMPLES: list[tuple[str, str, dict]] = [
    (
        "Add office rent 50000 for July.",
        "AddExpense",
        {"title": "Office Rent", "amount": 50000, "category": "Rent"},
    ),
    (
        "Add electricity bill 12000.",
        "AddExpense",
        {"title": "Electricity Bill", "amount": 12000, "category": "Utilities"},
    ),
    ("Generate Profit and Loss Statement.", "GenerateReport", {"report_type": "profit-and-loss"}),
    ("Create Balance Sheet.", "GenerateReport", {"report_type": "balance-sheet"}),
    ("Run monthly audit.", "RunAudit", {}),
    ("Show top five expenses.", "TopExpenses", {"n": 5}),
    ("Compare June and July expenses.", "ComparePeriods", {}),
    ("How much did we spend on utilities in March?", "CategoryTotal", {"category": "Utilities"}),
    ("What was our net profit last month?", "NetProfitQuery", {}),
]


def build_system_prompt(*, role: str, today: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(role=role, today=today)
