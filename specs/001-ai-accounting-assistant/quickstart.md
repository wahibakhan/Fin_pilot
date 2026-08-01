# Quickstart: FinPilot AI – AI-Powered Accounting & Finance Assistant

Validates that the feature works end-to-end. Run this after Phase 3+ of the roadmap in `plan.md` produces a runnable stack. Full endpoint shapes are in `contracts/openapi.yaml`; full schema is in `data-model.md`.

## Prerequisites

- Docker + Docker Compose
- Node.js 20+ (frontend)
- `uv` (backend) — https://docs.astral.sh/uv/
- An LLM API key for the configured `AI_PROVIDER` (e.g. `OPENAI_API_KEY`) — the app runs without it, but User Stories 3 and 6 (AI features) will report "AI assistant unavailable" per FR-033

## 1. Local setup

```bash
cp .env.example .env
# fill in DATABASE_URL (or leave default for docker-compose's Postgres),
# JWT_SECRET, AI_PROVIDER, AI_MODEL, OPENAI_API_KEY

docker compose up -d db

cd backend
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed_demo_data   # creates one Owner, one Accountant, one Office Admin, and sample categories
uv run uvicorn src.main:app --reload --port 8000

# in a second terminal
cd frontend
npm install
npm run dev
```

Or, once `docker/` is complete (Phase 10 of the roadmap): `docker compose up` starts db + backend + frontend together.

## 2. Validate User Story 1 — Secure Role-Based Access

1. Open `http://localhost:3000`, confirm you're redirected to `/login` (unauthenticated access denied — FR-004).
2. Log in as the seeded Office Administrator. Confirm you can reach the dashboard but cannot see a "Delete" action on any expense/income row, and cannot open Balance Sheet/Trial Balance or the audit log.
3. Log out. Confirm a direct navigation to `/dashboard` bounces back to `/login`.

## 3. Validate User Story 2 — Manual Income & Expense Tracking

1. Log in as the seeded Accountant.
2. Add an expense: title "Office Rent", amount 50000, category "Rent", date this month. Confirm it appears in the ledger and the dashboard's "Total Expenses" increases by 50000 within the same page load.
3. Edit the amount to 52000. Confirm the dashboard and ledger both reflect 52000.
4. Attempt to submit an expense with amount `0`. Confirm a field-level validation error and that nothing is saved (FR-012).
5. Delete the expense. Confirm it disappears from the ledger and dashboard totals drop back down.

## 4. Validate User Story 3 — Conversational AI Data Entry

1. Open the AI Assistant panel.
2. Type: `Add office rent 50000 for July`. Confirm the assistant shows a proposed expense (title, amount, category, date) and does **not** create it until you click Confirm (FR-027).
3. Click Confirm. Confirm the same expense now appears in the ledger, tagged `created_via: ai`.
4. Type: `Add an expense` (no amount). Confirm the assistant asks a clarifying question instead of creating anything (FR-028).

## 5. Validate User Story 4 — Financial Reporting

1. As Accountant, request the Profit & Loss Statement for the current month. Confirm total income, total expenses, and net profit reconcile with the entries added above.
2. Request a report for a month with no data. Confirm a clean zero-value report, not an error (FR-020).
3. Log in as Office Administrator and attempt to open Balance Sheet. Confirm a permission error (FR-022).

## 6. Validate User Story 5 — Complete Ledger & Transaction History

1. Seed ≥60 mixed income/expense rows (`uv run python -m scripts.seed_bulk_ledger`).
2. Open the ledger. Confirm results are paginated (not all 60+ rows on one page).
3. Filter by category and a date range simultaneously; confirm only matching rows remain.
4. Sort by amount descending; confirm order is correct across pages.

## 7. Validate User Story 6 — AI Analysis & Anomaly Detection

1. Ask the assistant: `Show top five expenses`. Confirm exactly 5 results, descending by amount.
2. Ask: `Compare June and July expenses`. Confirm totals for both months plus the delta.
3. Add two near-identical expenses (same amount/category/date). Ask: `Run monthly audit`. Confirm the duplicate is flagged (FR-030) and neither record is auto-deleted.
4. Add an expense far above the historical average for its category. Confirm it's flagged as unusually large (FR-031).

## 8. Validate degrade-gracefully behavior (FR-033, SC-008)

1. Unset/invalidate the AI provider API key and restart the backend.
2. Confirm the AI Assistant panel shows a clear "AI assistant unavailable — use manual entry" message.
3. Repeat steps 3–6 above (everything except the AI story) and confirm all pass unaffected.

## Expected result

All checks above pass ⇒ the implementation satisfies `spec.md`'s acceptance scenarios and Success Criteria SC-001 through SC-008.
