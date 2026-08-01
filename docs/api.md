# API Documentation

The authoritative, always-current API reference is FastAPI's auto-generated
interactive docs, served by the running backend itself:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Raw OpenAPI JSON**: `http://localhost:8000/openapi.json`

This file is a pointer plus a record of drift found between the
design-time contract and what actually got built — read
[`specs/001-ai-accounting-assistant/contracts/openapi.yaml`](../specs/001-ai-accounting-assistant/contracts/openapi.yaml)
for the full hand-written contract (kept in sync as of this phase; see below).

## Endpoint groups

| Group | Prefix | Notes |
|---|---|---|
| Auth | `/api/v1/auth` | JWT access + refresh tokens (Phase 2) |
| Categories | `/api/v1/categories` | Shared by expenses; any authenticated role may create |
| Expenses | `/api/v1/expenses` | Delete restricted to Business Owner + Accountant (Phase 3) |
| Income | `/api/v1/income` | Same delete restriction (Phase 4) |
| Ledger | `/api/v1/ledger` | Read-only union of expenses + income (Phase 5) |
| Reports | `/api/v1/reports/*` | 7 report types; Balance Sheet + Trial Balance restricted (Phase 6) |
| AI Assistant | `/api/v1/ai/*` | Chat + confirm/reject (Phase 7) |
| Dashboard | `/api/v1/dashboard/summary` | Composes Reports + Ledger (Phase 8) |
| Audit Log | `/api/v1/audit-logs` | Business Owner + Accountant only (built in Phase 9, see below) |
| Health | `/healthz` | No auth; used by Docker/CI/uptime checks |

## Drift found between the contract and the implementation (Phase 9/11)

The hand-written contract was written during planning (`/speckit-plan`),
before any code existed. Diffing it against the live `/openapi.json` at the
end of Phase 9 surfaced a few real differences, now fixed in
`contracts/openapi.yaml`:

1. **`AIChatResponse.conversation_id`** was missing from the contract. The
   real implementation needs it: it's the LangGraph `thread_id` backing an
   exchange, and the frontend must echo it back on the next `/ai/chat` call
   in the same conversation for multi-turn clarification and the
   confirm-node interrupt/resume to target the right graph checkpoint.
2. **`Expense.flags`** was missing. Added in Phase 7/T082 (passive
   duplicate/unusually-large-expense detection) — always an empty array
   except on the `POST /expenses` create response.
3. **`GET /audit-logs`** was in the contract's path list from planning, but
   had no response schema and was missing the `page_size` query param that
   every other paginated list endpoint has. The endpoint itself hadn't
   actually been built until Phase 9 (see `tasks.md`'s Phase 9 notes) — this
   was the single largest gap between the plan and the implementation across
   the whole project.
4. **`GET /healthz`** was never in the contract at all (it's infra-level,
   not a feature endpoint) — added for completeness.

No other drift was found: all other endpoints, request schemas, and role
restrictions in `contracts/openapi.yaml` matched the live implementation
exactly at the time of this check.
