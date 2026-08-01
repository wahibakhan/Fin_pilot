# Implementation Plan: FinPilot AI – AI-Powered Accounting & Finance Assistant

**Branch**: `001-ai-accounting-assistant` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-ai-accounting-assistant/spec.md`

## Summary

FinPilot AI is a single-organization accounting web application for a Business Owner, an Accountant, and an Office Administrator to record income/expenses, browse a unified ledger, generate seven standard financial reports, and — via a LangGraph-orchestrated AI assistant — do all of the above through natural language, plus get proactive duplicate/anomaly/large-expense detection. The technical approach is a two-project web application (FastAPI backend, Next.js frontend) sharing a single REST contract (`contracts/openapi.yaml`) as the integration boundary, with a strict rule (see Research §8) that the AI assistant calls the exact same service-layer functions as the REST API — never its own data path — so validation, authorization, and audit logging (FR-003, FR-034, FR-037) can never drift between the manual and AI paths.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript / Node.js 20+ (frontend)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, LangGraph, `passlib`/`python-jose` (JWT); Next.js 15 (App Router), Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form + Zod, Recharts

**Storage**: PostgreSQL (Neon-hosted in staging/production, Dockerized Postgres locally)

**Testing**: `pytest` + `httpx.AsyncClient` (backend unit/API/contract), stubbed-LLM golden-transcript tests (AI workflow), Vitest + React Testing Library (frontend unit), Playwright (frontend e2e)

**Target Platform**: Containerized Linux services (Docker) for the backend; Vercel (Node/edge) for the frontend

**Project Type**: Web application — two deployable projects (`backend/`, `frontend/`) integrated via REST + JWT

**Performance Goals**: Report generation < 5s for a typical monthly dataset (SC-003); dashboard reflects a new transaction within the same page load (FR-008); manual entry-to-dashboard round trip < 30s end-to-end (SC-001)

**Constraints**: Every AI create/update/delete requires explicit user confirmation before commit (FR-027); AI and manual paths must enforce identical validation/authorization (FR-034, FR-003); system must remain fully usable for all non-AI user stories when the AI provider is unavailable (FR-033, SC-008)

**Scale/Scope**: Single organization per deployment, 3 roles, 7 report types, 6 user stories, 38 functional requirements — SMB/accounting-firm-internal scale (tens of concurrent users, tens of thousands of ledger rows/year), not multi-tenant SaaS scale

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` is still the unedited template (no principles ratified yet for this project) — there is nothing concrete to gate against, so this check passes vacuously. **Recommendation**: run `/speckit-constitution` before `/speckit-tasks` to ratify at least the principles implied by this plan's own decisions (repository/service layering is mandatory; AI tools may never bypass the service layer; every mutation must produce an audit log row; TDD for the service layer), so this and future features get checked against a real gate instead of an empty one.

No violations to record. Re-checked after Phase 1 design (data model, contracts) below — still passes vacuously.

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-accounting-assistant/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   └── openapi.yaml       # Phase 1 output
└── tasks.md              # Phase 2 output (/speckit-tasks — not created by this command)
```

### Source Code (repository root)

**Structure Decision**: Option 2 — Web application (frontend + backend detected), matching the requirement for independently deployed frontend (Vercel) and backend (Railway/Render) services sharing the OpenAPI contract as their integration point.

```text
backend/
├── src/
│   ├── main.py                    # FastAPI app factory, router registration
│   ├── core/
│   │   ├── config.py               # env-driven settings (pydantic-settings)
│   │   ├── security.py             # password hashing, JWT encode/decode
│   │   └── dependencies.py         # get_db, get_current_user, require_role()
│   ├── models/                    # SQLAlchemy 2.0 declarative models (data-model.md)
│   ├── schemas/                   # Pydantic v2 request/response schemas (mirrors contracts/openapi.yaml)
│   ├── repositories/              # one per entity: expense_repo.py, income_repo.py, ...
│   ├── services/                  # business rules + audit logging; shared by API and AI tools
│   │   ├── auth_service.py
│   │   ├── expense_service.py
│   │   ├── income_service.py
│   │   ├── category_service.py
│   │   ├── ledger_service.py
│   │   ├── report_service.py
│   │   └── audit_service.py
│   ├── api/v1/                    # thin FastAPI routers, one per contracts/openapi.yaml tag
│   │   ├── auth.py, expenses.py, income.py, ledger.py, reports.py,
│   │   ├── dashboard.py, ai_chat.py, audit_logs.py
│   ├── agent/                     # LangGraph agent (plan §6)
│   │   ├── graph.py                # StateGraph definition + interrupt/confirm node
│   │   ├── state.py
│   │   ├── prompts.py
│   │   └── tools/
│   │       ├── crud_tool.py         # wraps expense_service/income_service
│   │       ├── report_tool.py       # wraps report_service
│   │       ├── analysis_tool.py     # top-N, comparisons, category totals
│   │       ├── audit_tool.py        # duplicate/anomaly/large-expense detection
│   │       └── sql_query_tool.py    # narrow, read-only, parameterized aggregate queries only
│   └── alembic/
│       ├── env.py
│       └── versions/
├── tests/
│   ├── unit/                      # services/repositories, transactional test DB
│   ├── contract/                  # httpx tests validated against openapi.yaml
│   ├── integration/                # multi-step flows (create → report → audit log)
│   └── agent/                     # stubbed-LLM golden-transcript tests
├── scripts/
│   ├── seed_demo_data.py
│   └── seed_bulk_ledger.py
├── pyproject.toml                 # uv-managed
└── Dockerfile

frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/login/
│   │   ├── (app)/dashboard/
│   │   ├── (app)/expenses/
│   │   ├── (app)/income/
│   │   ├── (app)/ledger/
│   │   ├── (app)/reports/
│   │   ├── (app)/ai-assistant/
│   │   └── (app)/audit-log/          # Owner + Accountant only
│   ├── components/
│   │   ├── ui/                       # shadcn/ui primitives
│   │   ├── forms/                    # ExpenseForm, IncomeForm (RHF + Zod)
│   │   ├── tables/                   # LedgerTable, ExpenseTable, IncomeTable
│   │   ├── charts/                   # DashboardCharts (Recharts)
│   │   └── chat/                     # AIChatPanel, ProposedActionCard
│   ├── lib/
│   │   ├── api-client.ts             # typed fetch wrapper generated/aligned to openapi.yaml
│   │   ├── auth.ts                   # token storage/refresh
│   │   └── rbac.ts                   # role → allowed-actions helper mirroring FR-003
│   ├── hooks/                        # useExpenses, useIncome, useLedger, useReports, useAIChat (TanStack Query)
│   └── stores/                       # ai-chat session UI state only
├── tests/
│   ├── unit/                         # Vitest + RTL
│   └── e2e/                          # Playwright, one spec per user story
├── package.json
└── Dockerfile

docker/
docker-compose.yml
.env.example
README.md
```

## Complexity Tracking

*No constitution gate violations to justify (constitution unratified — see Constitution Check above).* One deliberate complexity is flagged proactively even though not a formal gate violation:

| Decision | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Repository + Service layering (instead of routers talking to SQLAlchemy directly) | FR-034 and FR-003 require identical validation/authorization whether a mutation comes from the REST API or the AI assistant | Direct DB access from routers would need the same logic duplicated inside the AI tools, guaranteeing drift over time (see Research §8, §11) |
| `journal_entries` as a real table in addition to `expenses`/`income` | Balance Sheet and Trial Balance (FR-019) require a double-entry debit/credit representation that a flat transaction list cannot produce | Deriving balance-sheet figures on the fly from expenses/income alone was rejected — it cannot represent account balances (e.g., cumulative Cash position) correctly |

---

# Appendix: Detailed Delivery Plan

*(Beyond the core `/speckit-plan` template — included because the user requested full architecture, roadmap, and milestone detail in this same document. `/speckit-tasks` will still be the source of the granular, dependency-ordered task list; this section is the milestone-level plan that `/speckit-tasks` expands from.)*

## 1. Project Architecture

### 1.1 Frontend Architecture

Next.js 15 App Router, TypeScript, Tailwind + shadcn/ui. Server components fetch dashboard/report/ledger data directly from the backend on the server (using the caller's forwarded JWT) for fast first paint; client components handle forms, the AI chat panel, and anything with local interaction state. `lib/api-client.ts` is the single point of contact with the backend, kept in sync with `contracts/openapi.yaml`. `lib/rbac.ts` hides/disables UI affordances per role (delete buttons, Balance Sheet/Trial Balance nav items, audit log nav item) as a UX convenience — the real enforcement is always server-side (FR-003).

### 1.2 Backend Architecture

FastAPI, layered: `api` (routing + request/response schema binding only) → `services` (business rules, permission checks via `require_role()`, audit logging, transaction boundary) → `repositories` (SQLAlchemy 2.0 queries) → `models`. Both REST routers and LangGraph tools call `services` — this is the architectural guarantee behind FR-003/FR-034 (see Research §8, §11).

### 1.3 Database Architecture

PostgreSQL. Physical tables: `users`, `categories`, `expenses`, `income`, `journal_entries`, `audit_log_entries`, `ai_interactions`, `refresh_tokens` (see `data-model.md`). `ledger` and all seven reports are read models (parameterized queries/views), not physical tables, to avoid a second source of truth. Alembic manages all schema change as versioned, reviewable migrations.

### 1.4 AI Architecture

LangGraph `StateGraph` with nodes: `interpret` (parse user message → structured intent) → `plan` (select tool(s): CRUD / Report / Analysis / Audit) → `confirm` (interrupt node — required for any create/update/delete, per FR-027) → `execute` (call the service-layer tool) → `respond`. The confirm node is what makes "propose, don't commit" a structural property of the graph rather than a convention. LLM provider is injected via a `AI_PROVIDER`/`AI_MODEL` env-driven adapter, defaulting to an OpenAI GPT-5-class model, so swapping providers doesn't touch graph/tool code (Research §7).

### 1.5 Deployment Architecture

Frontend → Vercel (Next.js native). Backend → Railway or Render, deployed from the same Docker image used in local `docker-compose.yml`. Database → Neon (managed Postgres). All three configured purely via environment variables (`.env.example` documents every key); no environment-specific code branches.

## 2. Development Roadmap (10 Phases / Milestones)

Each milestone lists Goal, Tasks, Dependencies, Estimated Effort, and Completion Criteria. Effort is in ideal engineer-days for a small team (1 backend + 1 frontend, working in parallel where noted); use as relative sizing, not a committed schedule.

### Phase 1 — Project Setup

- **Goal**: A running skeleton (empty screens, empty API, migrated empty DB) that both backend and frontend engineers can build on in parallel.
- **Tasks**: Scaffold `backend/` (uv project, FastAPI app factory, config/settings, Alembic init) and `frontend/` (Next.js 15 + TS + Tailwind + shadcn/ui init); write `docker-compose.yml` (db + backend + frontend) and `.env.example`; set up `users` + `categories` tables/migration; wire CI to run lint + unit tests on push.
- **Dependencies**: None (first milestone).
- **Estimated Effort**: 2–3 days.
- **Completion Criteria**: `docker compose up` brings up all three services; `GET /api/v1/auth/me` returns 401 unauthenticated; frontend renders an empty login page against the live backend.

### Phase 2 — Authentication

- **Goal**: User Story 1 fully working (FR-001–FR-004).
- **Tasks**: `users`/`refresh_tokens` migrations; password hashing + JWT issue/verify; `/auth/login`, `/auth/logout`, `/auth/refresh`, `/auth/me`; `require_role()` dependency; frontend login page, token storage/refresh interceptor, protected-route wrapper, role-aware nav (`lib/rbac.ts`).
- **Dependencies**: Phase 1.
- **Estimated Effort**: 3–4 days.
- **Completion Criteria**: Quickstart §2 passes end-to-end for all three seeded roles.

### Phase 3 — Expense Management

- **Goal**: User Story 2 (expense half) — FR-009–FR-012.
- **Tasks**: `expenses` migration + model; `expense_repo`, `expense_service` (validation, audit logging); `/expenses` CRUD + search/filter routes; `ExpenseForm` (RHF + Zod), `ExpenseTable`, expenses page.
- **Dependencies**: Phase 2 (needs auth + roles).
- **Estimated Effort**: 3 days.
- **Completion Criteria**: Quickstart §3 (expense portion) passes; FR-012 validation errors verified per field.

### Phase 4 — Income Management

- **Goal**: User Story 2 (income half) — FR-013–FR-016.
- **Tasks**: Mirrors Phase 3 for `income` (no category FK per spec's field list).
- **Dependencies**: Phase 2. (Can run in parallel with Phase 3 if two backend engineers are available; otherwise sequential.)
- **Estimated Effort**: 2 days (smaller than expenses — no category relationship).
- **Completion Criteria**: Quickstart §3 (income portion) passes.

### Phase 5 — Ledger

- **Goal**: User Story 5 — FR-017, FR-018.
- **Tasks**: `ledger_service` union query (expenses ∪ income) with search/filter/sort/pagination; `/ledger` route; `LedgerTable` with pagination controls, combined filter bar.
- **Dependencies**: Phases 3 & 4 (needs both record types to union).
- **Estimated Effort**: 2 days.
- **Completion Criteria**: Quickstart §6 passes against a 60+ row seeded dataset.

### Phase 6 — Reports

- **Goal**: User Story 4 — FR-019–FR-022.
- **Tasks**: `journal_entries` migration + auto-posting hook (fires from `expense_service`/`income_service` on create/update/delete); `report_service` with one function per report type; 7 report routes with role gating (Balance Sheet/Trial Balance → Owner/Accountant only); report pages/components with date-range picker and charts.
- **Dependencies**: Phases 3 & 4 (reports read from expense/income data and their journal postings).
- **Estimated Effort**: 5 days (7 report types, plus journal-posting logic).
- **Completion Criteria**: Quickstart §5 passes; all 7 reports reconcile against hand-calculated totals on seeded data (mirrors SC-003's dataset).

### Phase 7 — AI Accounting Agent

- **Goal**: User Stories 3 & 6 — FR-023–FR-033.
- **Tasks**: LangGraph graph + state (§1.4); provider adapter; `crud_tool`/`report_tool`/`analysis_tool`/`audit_tool`/`sql_query_tool`; `/ai/chat`, `/ai/interactions/{id}/confirm`, `/ai/interactions/{id}/reject` routes; `ai_interactions` migration; duplicate/anomaly/large-expense detection logic in `audit_tool`; graceful-degradation path when the provider is unreachable (FR-033); frontend `AIChatPanel` + `ProposedActionCard` (confirm/reject UI).
- **Dependencies**: Phases 3, 4, 6 (the agent's tools wrap the expense/income/report services built there).
- **Estimated Effort**: 6–8 days (the largest milestone — confirmation flow, 5 tool types, prompt iteration).
- **Completion Criteria**: Quickstart §4, §7, §8 all pass; golden-transcript tests (Research §12) pass for every example command listed in the spec.

### Phase 8 — Dashboard

- **Goal**: FR-005–FR-008 (can be built once expense/income/report data exists to aggregate).
- **Tasks**: `dashboard_service` aggregation query; `/dashboard/summary` route; dashboard page with totals, monthly summary, category breakdown, recent transactions, and Recharts visualizations.
- **Dependencies**: Phases 3, 4, 6.
- **Estimated Effort**: 2–3 days.
- **Completion Criteria**: Dashboard figures match a manually-verified sum of seeded data; updates reflect new transactions per FR-008.

### Phase 9 — Testing

- **Goal**: Close coverage gaps left by per-phase tests; add integration and e2e suites; verify all Success Criteria.
- **Tasks**: Backend integration tests spanning create → report → audit-log; Playwright e2e specs, one per user story, driven by `quickstart.md`; frontend component tests for forms/tables/charts/chat; permission-matrix test sweep (every role × every mutating endpoint) proving FR-003/FR-022/SC-007; AI-unavailable fallback test proving SC-008.
- **Dependencies**: Phases 1–8 substantially complete.
- **Estimated Effort**: 4–5 days.
- **Completion Criteria**: All Acceptance Scenarios in `spec.md` have an automated test; SC-001–SC-008 each have at least one test asserting the measurable threshold.

### Phase 10 — Docker & Deployment

- **Goal**: One-command local setup; reproducible cloud deployment.
- **Tasks**: Finalize multi-stage `backend/Dockerfile` and `frontend/Dockerfile`; finalize `docker-compose.yml` (db + backend + frontend + healthchecks); Vercel project config for `frontend/`; Railway/Render service config for `backend/` (same Dockerfile); Neon project + connection string wiring; CI/CD pipeline (lint → test → build → deploy on merge to main); document all env vars in `.env.example` + README.
- **Dependencies**: Phases 1–9.
- **Estimated Effort**: 2–3 days.
- **Completion Criteria**: `docker compose up` (from a clean clone + `.env`) reproduces the full quickstart; a merge to `main` deploys frontend + backend automatically with passing health checks.

**Total estimated effort**: ~31–41 ideal engineer-days across the two-person team, with Phases 3/4 and portions of frontend/backend work parallelizable within a phase.

## 3. Database Implementation

Full column-level design is in `data-model.md`. Summary of the Alembic migration plan (one migration per phase, forward-only, reviewed like code):

1. `0001_users_categories` — `users`, `categories`, enum types for role/category-type (Phase 1).
2. `0002_refresh_tokens` — `refresh_tokens` (Phase 2).
3. `0003_expenses` — `expenses` + indexes + amount-positive check constraint (Phase 3).
4. `0004_income` — `income` + indexes + check constraint (Phase 4).
5. `0005_journal_entries` — `journal_entries` + indexes (Phase 6, ahead of report logic).
6. `0006_audit_log_entries` — `audit_log_entries` + indexes (Phase 6/7, needed by both manual and AI mutations).
7. `0007_ai_interactions` — `ai_interactions` (Phase 7).

Each model gets a corresponding SQLAlchemy 2.0 declarative class in `backend/src/models/`, using `Mapped[...]`/`mapped_column(...)` typed style, with relationships declared both directions where used by repositories (e.g., `Category.expenses`, `User.expenses`).

## 4. Backend Implementation

- **FastAPI**: one `APIRouter` per resource under `api/v1/`, registered in `main.py`; all routers depend on `get_current_user` (and `require_role(...)` where restricted); global exception handlers translate service-layer exceptions (`ValidationError`, `PermissionDeniedError`, `NotFoundError`, `ConflictError`) into the correct HTTP status codes (400/403/404/409) with a consistent error body shape.
- **Pydantic Models**: request/response schemas in `schemas/`, one module per resource, mirroring `contracts/openapi.yaml` field-for-field; validators for amount > 0 and date sanity live here; category-existence and permission checks live in the service layer (need DB access).
- **Services**: one per resource (`expense_service.py`, etc.); each exposes plain async functions (`create_expense(db, current_user, payload) -> Expense`) called identically by routers and AI tools; every mutating function writes an `audit_log_entries` row before returning (FR-029, FR-037).
- **Repository Pattern**: one repository class per entity encapsulating SQLAlchemy query construction (`ExpenseRepository.list(filters, page)`, `.get(id)`, `.create(...)`, `.soft_delete(...)`); services depend on repositories via constructor injection, never on the `Session` directly, so services are unit-testable with an in-memory fake repository if desired.
- **API Endpoints**: full list in `contracts/openapi.yaml`; implementation order in §7 below.
- **Dependency Injection**: FastAPI `Depends()` chain — `get_db` (session) → `get_current_user` (decodes JWT) → `require_role(*roles)` (raises 403) → resource-specific service factory.
- **Authentication**: JWT access/refresh per Research §6; `core/security.py` centralizes hashing + token encode/decode; refresh rotation checked against `refresh_tokens.revoked_at`/`expires_at`.
- **Exception Handling**: a small domain exception hierarchy (`AppError` → `ValidationError`, `PermissionDeniedError`, `NotFoundError`, `ConflictError`) raised in services, caught once by FastAPI exception handlers in `main.py`, guaranteeing manual and AI paths surface errors identically (the AI's `respond` node just relays the same message).

## 5. Frontend Implementation

- **Next.js App Router**: route groups `(auth)` (public) and `(app)` (protected, wrapped in a layout that checks auth and renders role-aware nav).
- **Layout**: root layout sets up Tailwind/theme; `(app)/layout.tsx` renders sidebar nav (items filtered by `lib/rbac.ts`) + top bar (user menu, logout).
- **Pages**: `login`, `dashboard`, `expenses`, `income`, `ledger`, `reports/[type]`, `ai-assistant`, `audit-log` (Owner/Accountant only, else redirected).
- **Components**: shadcn/ui primitives in `components/ui`; domain components (`ExpenseForm`, `IncomeForm`, `LedgerTable`, `ReportView`, `DashboardCharts`, `AIChatPanel`, `ProposedActionCard`) built on top.
- **Forms**: React Hook Form + Zod schemas (mirroring backend Pydantic rules) for expense/income create/edit; inline field errors; optimistic-free (wait for server response, since financial writes shouldn't optimistically render before validation).
- **Tables**: shadcn `DataTable` pattern (TanStack Table under the hood) for expenses/income/ledger — search box, filter controls, column sort, pagination footer wired to the corresponding list endpoint's query params.
- **Charts**: Recharts via shadcn chart components — income/expense/profit trend line, category breakdown pie/bar.
- **AI Chat Interface**: `AIChatPanel` (message list + input) + `ProposedActionCard` (renders `proposed_action` from `AIChatResponse` with Confirm/Reject buttons calling `/ai/interactions/{id}/confirm|reject`); shows a disabled/"unavailable" state when the backend reports the AI provider is down.
- **State Management**: TanStack Query for all server data (queries + mutations, cache invalidation on mutation success); no global client store for server data — only a small store for AI chat session UI state (current conversation id, panel open/closed).
- **API Integration**: `lib/api-client.ts` wraps `fetch`, attaches the JWT, handles 401 → refresh-token retry-once → redirect-to-login on failure; typed request/response shapes kept aligned with `contracts/openapi.yaml`.

## 6. AI Agent Implementation (LangGraph)

- **Agent Nodes**: `interpret` → `plan` → `confirm` (interrupt, skipped for pure reads) → `execute` → `respond`. `interpret` and `plan` may loop back to a `clarify` node when required info is missing (FR-028) or a reference is ambiguous (Edge Cases).
- **Tool Calling**: each tool is a typed function the graph can call — `crud_tool` (create/update/delete expense or income, delegates to `expense_service`/`income_service`), `report_tool` (delegates to `report_service`), `analysis_tool` (top-N, period comparison, category totals — read-only aggregate queries), `audit_tool` (duplicate/anomaly/large-expense detection, used by both the explicit "run monthly audit" command and automatically after every create), `sql_query_tool` (a narrow, parameterized, read-only aggregate query escape hatch for analytical questions that don't fit a canned tool — never used for writes).
- **Memory**: short-term conversation memory scoped to a `conversation_id` (kept in `ai_interactions`/graph checkpointer) so multi-turn clarification ("which rent expense?" → user answers → agent continues) works; no long-term cross-session memory in v1 (out of scope per Assumptions).
- **Prompt Strategy**: a system prompt encodes the confirm-before-write rule, the current user's role (so the model doesn't even propose actions it knows will be rejected), and the available tool schemas; few-shot examples drawn directly from the spec's example commands to anchor interpretation (amount/date/category extraction).
- **Report Generation**: `report_tool` calls `report_service`, then a summarization step turns the structured report into a natural-language explanation on request (FR-032).
- **SQL Query Tool**: allow-listed, parameterized, read-only aggregate templates only (e.g., "sum by category/date-range") — the model fills parameters, never raw SQL text, closing the injection/scope-creep risk of a free-text SQL tool.
- **CRUD Tool**: always routes through the `confirm` node before `execute` (FR-027); `execute` calls the identical service function a REST call would use.
- **Audit Tool**: duplicate detection (same amount+category+date within N days), large-expense detection (> k standard deviations from the category's historical mean), surfaced both on-demand ("run monthly audit") and as a passive flag returned alongside normal create responses.
- **Financial Analysis Tool**: top-N, period-over-period comparison, category/period totals — all backed by the same aggregate queries `report_service`/`dashboard_service` use, so AI-reported numbers can never diverge from what the UI shows.

## 7. API Implementation Order

Endpoints implemented in dependency order (matches the roadmap phases):

1. `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` (Phase 2 — everything else needs auth)
2. `GET/POST /categories` (Phase 2/3 — expenses depend on categories existing)
3. `GET/POST /expenses`, `GET/PATCH/DELETE /expenses/{id}` (Phase 3)
4. `GET/POST /income`, `GET/PATCH/DELETE /income/{id}` (Phase 4)
5. `GET /ledger` (Phase 5 — depends on 3 & 4)
6. `GET /reports/*` (7 endpoints) (Phase 6 — depends on 3 & 4, plus `journal_entries` posting)
7. `POST /ai/chat`, `POST /ai/interactions/{id}/confirm`, `POST /ai/interactions/{id}/reject` (Phase 7 — depends on 3, 4, 6 via tool wrapping)
8. `GET /dashboard/summary` (Phase 8 — depends on 3, 4, 6)
9. `GET /audit-logs` (Phase 6/7 — depends on audit logging being wired into every mutation from Phase 3 onward, but only needs its own route once there's data worth viewing)

## 8. Testing Plan

- **Unit Tests** (backend): repositories against a transactional test DB; services with permission/validation edge cases (amount ≤ 0, missing fields, non-existent category, wrong role) per FR-012/FR-016/FR-034.
- **API Tests**: `httpx.AsyncClient` against the FastAPI app for every endpoint in `contracts/openapi.yaml`, asserting status codes and response shapes; a permission-matrix sweep (3 roles × every mutating endpoint) directly verifying FR-003/FR-022/SC-007.
- **Frontend Tests**: Vitest + RTL for forms (validation messages), tables (sort/filter/pagination logic), and the `ProposedActionCard` confirm/reject interaction; Playwright e2e specs mirroring `quickstart.md` §2–§8 one-to-one, run against a docker-composed stack in CI.
- **AI Workflow Tests**: stubbed-LLM golden-transcript tests for every example command in the spec (deterministic tool-call assertions, no live API call); a small opt-in suite of live-model smoke tests (real `AI_PROVIDER` call) gated behind a CI flag to avoid cost/flakiness on every push; an explicit test that disables the AI provider and asserts SC-008 (all non-AI stories still pass).

## 9. Git Strategy

- **Branch structure**: `main` (always deployable) ← short-lived feature branches named `<phase-number>-<short-description>` (e.g., `03-expense-management`), one per roadmap phase or sub-slice of a phase; no long-lived `develop` branch — trunk-based, small PRs.
- **Pull Request workflow**: every PR targets `main`; requires passing CI (lint, unit, API/contract tests) and one review; PRs should map to a single phase/milestone or a clearly-scoped slice of one; squash-merge to keep `main` history one-commit-per-change.
- **Commit message convention**: Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`), optionally scoped (`feat(expenses): add category filter`), so a changelog can be generated automatically and it's clear which roadmap phase a commit belongs to.

## 10. Deployment Plan

- **Frontend**: Vercel project linked to `frontend/`; preview deployment per PR, production deployment on merge to `main`; env vars (`NEXT_PUBLIC_API_BASE_URL`, etc.) set per Vercel environment (Preview/Production).
- **Backend**: Railway or Render service built from `backend/Dockerfile`; one service per environment (staging/production); env vars (`DATABASE_URL`, `JWT_SECRET`, `AI_PROVIDER`, `AI_MODEL`, `OPENAI_API_KEY`, `CORS_ORIGINS`) set in the platform's secret store — never committed (see project memory on secret handling).
- **Database**: Neon project with a branch per environment (mirrors Vercel preview branching); `alembic upgrade head` run as a release-step/init-container on deploy, never manually against production.
- **Docker**: multi-stage `backend/Dockerfile` (builder installs via `uv`, runtime stage copies venv + app, non-root user); `frontend/Dockerfile` (standard Next.js standalone-output multi-stage build) — used for local compose and as the Railway/Render build source, so local and hosted behavior match.
- **Environment Variables**: single `.env.example` at repo root enumerating every variable both services need, with placeholder (never real) values; `README.md` documents what each one is for.
- **Health Checks**: `GET /healthz` on the backend (checks DB connectivity) used by Docker Compose `healthcheck:`, Railway/Render health checks, and CI smoke tests; frontend relies on Vercel's built-in deployment health checks.
- **CI/CD recommendations**: GitHub Actions — `lint-and-test` on every PR (backend `uv run pytest` + `ruff`, frontend `npm run lint` + `vitest`); `e2e` job runs Playwright against a docker-composed stack; `deploy` job (on merge to `main`) triggers Vercel + Railway/Render deploys (both platforms support git-push-to-deploy natively, so this job may just be a required-status-check gate rather than an explicit deploy step) and runs `alembic upgrade head` against the target Neon branch before traffic switches over.
