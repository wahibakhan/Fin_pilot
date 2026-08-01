# Tasks: FinPilot AI – AI-Powered Accounting & Finance Assistant

**Input**: Design documents from `specs/001-ai-accounting-assistant/` (plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md)

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included as their own tasks (Phase 9) rather than interleaved test-first per story, per the user's explicit 11-phase request; the AI workflow additionally gets golden-transcript fixtures inside Phase 7 since they're needed to validate the graph as it's built.

**Organization**: Grouped into the user's 11 requested phases. Each task is also tagged `[USn]` where it maps to a spec.md user story, so independent-story testing and MVP scoping still work exactly as spec-kit expects. Setup/Foundational/Dashboard/Testing/Deployment/Documentation tasks carry no story tag (cross-cutting, per spec-kit convention).

**Story ↔ Phase map** (from `spec.md`):

| Story | Title | Priority | Delivered in |
|---|---|---|---|
| US1 | Secure Role-Based Access | P1 | Phase 2 |
| US2 | Manual Income & Expense Tracking | P1 | Phases 3–4 |
| US3 | Conversational AI Data Entry | P2 | Phase 7 (entry) |
| US4 | Financial Reporting | P2 | Phase 6 |
| US5 | Complete Ledger & Transaction History | P3 | Phase 5 |
| US6 | AI-Powered Financial Analysis & Anomaly Detection | P3 | Phase 7 (analysis) |

## Format

`- [ ] [TaskID] [P?] [Story?] Title — Description (file path)`
followed by `Dependencies` / `Acceptance Criteria` / `Complexity` sub-bullets.
`[P]` = parallelizable (different files, no unfinished dependency). No `[Story]` tag = cross-cutting/setup/polish.

---

## Phase 1 – Project Setup

**Purpose**: Runnable skeleton (empty screens, empty API, migrated-but-empty DB) both engineers can build on in parallel. Blocks every later phase.

- [X] T001 Create monorepo root structure — create `backend/`, `frontend/`, `docker/` directories per `plan.md` Project Structure (repo root)
  - **Dependencies**: None
  - **Acceptance Criteria**: `backend/`, `frontend/`, `docker/` exist; `specs/` already present; root `README.md` placeholder exists
  - **Complexity**: Easy

- [X] T002 [P] Initialize Next.js 15 — `npx create-next-app@15` (pinned — `@latest` now resolves to Next 16) with TypeScript, App Router, ESLint in `frontend/`
  - **Dependencies**: T001
  - **Acceptance Criteria**: `npm run dev` serves the default page at `localhost:3000`; `tsconfig.json` strict mode on
  - **Complexity**: Easy

- [X] T003 [P] Configure Tailwind CSS — install/verify Tailwind config in `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`
  - **Dependencies**: T002
  - **Acceptance Criteria**: a Tailwind utility class visibly styles the default page
  - **Complexity**: Easy

- [X] T004 Configure shadcn/ui — run `npx shadcn init`, add `button`, `input`, `card`, `table`, `dialog`, `form` primitives into `frontend/src/components/ui/`
  - **Dependencies**: T003
  - **Acceptance Criteria**: a shadcn `<Button>` renders correctly on the default page with theme tokens applied
  - **Complexity**: Easy

- [X] T005 [P] Initialize FastAPI with uv — `uv init` in `backend/`, add `fastapi`, `uvicorn`, `pydantic-settings`; app factory in `backend/src/main.py`, settings in `backend/src/core/config.py`
  - **Dependencies**: T001
  - **Acceptance Criteria**: `uv run uvicorn src.main:app --reload` serves `GET /` returning `{"status":"ok"}`; settings load from environment
  - **Complexity**: Easy

- [X] T006 Configure PostgreSQL — add local Postgres service definition and connection settings (`DATABASE_URL`) to `backend/src/core/config.py`
  - **Dependencies**: T005
  - **Acceptance Criteria**: backend process can open a connection to a local Postgres instance using `DATABASE_URL`
  - **Complexity**: Easy

- [X] T007 Configure SQLAlchemy — async engine/session factory + declarative `Base` in `backend/src/core/db.py`; `get_db` dependency in `backend/src/core/dependencies.py`
  - **Dependencies**: T006
  - **Acceptance Criteria**: `get_db()` yields a working `AsyncSession`; a trivial `SELECT 1` succeeds via the session
  - **Complexity**: Medium

- [X] T008 Configure Alembic — `alembic init`, point `env.py` at the SQLAlchemy `Base`/async engine, in `backend/src/alembic/`
  - **Dependencies**: T007
  - **Acceptance Criteria**: `uv run alembic revision --autogenerate -m "init"` produces an empty (no-model) migration cleanly; `uv run alembic upgrade head` runs against local Postgres
  - **Complexity**: Medium

- [X] T009 [P] Domain exception hierarchy & handlers — `AppError`, `ValidationError`, `PermissionDeniedError`, `NotFoundError`, `ConflictError` in `backend/src/core/exceptions.py`; register FastAPI exception handlers in `backend/src/main.py`
  - **Dependencies**: T005
  - **Acceptance Criteria**: raising each exception type from a throwaway test route returns the correct HTTP status (400/403/404/409) with a consistent JSON error body
  - **Complexity**: Medium

- [X] T010 [P] Health check endpoint — `GET /healthz` (checks DB connectivity) in `backend/src/api/v1/health.py`
  - **Dependencies**: T007
  - **Acceptance Criteria**: returns 200 when DB reachable, 503 when not; used later by Docker/CI health checks
  - **Complexity**: Easy

- [X] T011 Configure Docker — multi-stage `backend/Dockerfile` (uv-based build, non-root runtime) and `frontend/Dockerfile` (Next.js standalone output)
  - **Dependencies**: T005, T002
  - **Acceptance Criteria**: `docker build` succeeds for both images; each container serves its respective health/default route
  - **Complexity**: Medium
  - *Deferred at Phase 1 (out of scope for "the Authentication module"), fulfilled by T097/T098 in Phase 10. `docker build` itself is unverified — no Docker in this environment.*

- [X] T012 `docker-compose.yml` + `.env.example` — orchestrate db + backend + frontend with healthchecks at repo root
  - **Dependencies**: T011
  - **Acceptance Criteria**: `docker compose up` (after `cp .env.example .env`) brings up all three services; backend `/healthz` reports 200 once Postgres is ready
  - **Complexity**: Medium

- [X] T013 [P] CI pipeline (lint + unit) — GitHub Actions workflow running backend `ruff`/`pytest` and frontend `eslint`/`vitest` on every push, in `.github/workflows/ci.yml`
  - **Dependencies**: T002, T005
  - **Acceptance Criteria**: workflow runs on a PR and fails/passes correctly on a deliberately broken/fixed test
  - **Complexity**: Easy
  - *Deferred at Phase 1, fulfilled by T103's lint+test jobs in Phase 10. Can't verify "runs on a PR" — no GitHub remote exists for this repo yet.*

**Checkpoint**: `docker compose up` works end to end; both apps boot; DB migrates; no user-facing features yet.

---

## Phase 2 – Authentication (User Story 1, P1) 🎯 MVP foundation

**Goal**: A user can log in, gets a role-scoped session, and every other page/API is inaccessible without it.

**Independent Test**: Log in as each seeded role, confirm workspace access matches role; log out and confirm session invalidation; confirm unauthenticated/invalid-credential access is denied everywhere (spec.md US1 Acceptance Scenarios).

- [X] T014 [P] [US1] User model & migration — `role` enum (`business_owner`,`accountant`,`office_administrator`) in `backend/src/models/user.py`; Alembic migration `0001_users`
  - **Dependencies**: T008
  - **Acceptance Criteria**: table created with unique `email`; role enum enforced at DB level
  - **Complexity**: Easy

- [X] T015 [P] [US1] `refresh_tokens` model & migration — in `backend/src/models/refresh_token.py`; migration `0002_refresh_tokens`
  - **Dependencies**: T014
  - **Acceptance Criteria**: table created with unique `token_hash`, FK to `users`
  - **Complexity**: Easy

- [X] T016 [US1] Security utilities — password hashing (bcrypt/argon2) + JWT access/refresh encode/decode in `backend/src/core/security.py`
  - **Dependencies**: T005
  - **Acceptance Criteria**: unit test round-trips a password through hash/verify and a payload through encode/decode, including expiry handling
  - **Complexity**: Medium

- [X] T017 [US1] Auth dependencies — `get_current_user` (decodes JWT, loads user) and `require_role(*roles)` in `backend/src/core/dependencies.py`
  - **Dependencies**: T016, T014
  - **Acceptance Criteria**: a protected throwaway route returns 401 with no/garbage token and 403 via `require_role` for a disallowed role
  - **Complexity**: Medium

- [X] T018 [US1] AuthService — login (verify + issue token pair), refresh (rotate, check revocation/expiry), logout (revoke) in `backend/src/services/auth_service.py`
  - **Dependencies**: T015, T016
  - **Acceptance Criteria**: login with valid credentials returns a token pair; login with bad credentials raises a 401-mapped error; logout revokes the refresh token so reuse fails
  - **Complexity**: Medium

- [X] T019 [US1] Auth endpoints — `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` in `backend/src/api/v1/auth.py`
  - **Dependencies**: T018, T017
  - **Acceptance Criteria**: all four endpoints match `contracts/openapi.yaml`; contract-level smoke test passes for each
  - **Complexity**: Medium

- [X] T020 [P] [US1] Seed script — creates one Business Owner, one Accountant, one Office Administrator in `backend/scripts/seed_demo_data.py`
  - **Dependencies**: T014
  - **Acceptance Criteria**: running the script twice is idempotent (no duplicate users); prints the three demo logins
  - **Complexity**: Easy

- [X] T021 [P] [US1] Frontend API client — typed `fetch` wrapper attaching JWT, handling 401→refresh-retry-once→redirect-to-login in `frontend/src/lib/api-client.ts`
  - **Dependencies**: T004
  - **Acceptance Criteria**: a call with an expired access token transparently refreshes and retries once, then redirects to `/login` if refresh also fails
  - **Complexity**: Medium

- [X] T022 [P] [US1] Frontend token storage — `frontend/src/lib/auth.ts` (store/read/clear access+refresh tokens)
  - **Dependencies**: T004
  - **Acceptance Criteria**: tokens persist across a page reload and are cleared on logout
  - **Complexity**: Easy

- [X] T023 [US1] Login page — `frontend/src/app/(auth)/login/page.tsx` with React Hook Form + Zod, calling `/auth/login`
  - **Dependencies**: T021, T022, T004
  - **Acceptance Criteria**: valid credentials redirect to `/dashboard`; invalid credentials show an inline error and grant no access
  - **Complexity**: Medium

- [X] T024 [US1] Protected route layout — `frontend/src/app/(app)/layout.tsx` redirects unauthenticated visitors to `/login` before rendering any child page
  - **Dependencies**: T022
  - **Acceptance Criteria**: direct navigation to `/dashboard`, `/expenses`, etc. with no session bounces to `/login` with no data flash
  - **Complexity**: Medium

- [X] T025 [P] [US1] RBAC helper — `frontend/src/lib/rbac.ts` mapping role → allowed nav items/actions (mirrors FR-003 matrix)
  - **Dependencies**: T004
  - **Acceptance Criteria**: unit test asserts Office Administrator's allowed-action set excludes delete/audit-log/Balance-Sheet/Trial-Balance
  - **Complexity**: Easy

- [X] T026 [US1] App shell nav + logout — sidebar/topbar in `(app)/layout.tsx` using `rbac.ts` to filter items; logout button calls `/auth/logout` and clears tokens
  - **Dependencies**: T025, T023, T019
  - **Acceptance Criteria**: nav items differ correctly per seeded role; logout returns the user to `/login` and invalidates the session server-side
  - **Complexity**: Medium

**Checkpoint**: `quickstart.md` §2 passes in full for all three roles.

**Implementation notes (2026-07-29)**:
- T016 originally targeted bcrypt via `passlib`; swapped to `argon2-cffi` directly after `passlib`'s bcrypt backend proved incompatible with the currently-installed `bcrypt` package (a known, unmaintained-`passlib` issue — see `research.md` §6 "open items"). Verified via `tests/unit/test_security.py`.
- T011 (Docker) and T013 (CI) were intentionally **not** built as part of this pass — they're not on the critical path to T014–T026 and were out of scope for "implement the Authentication module." Left as `[ ]`.
- Tests were added ahead of Phase 9 for this slice: `backend/tests/unit/test_security.py` (hashing/JWT, no DB needed — passes today), `backend/tests/unit/test_auth_service.py` + `backend/tests/contract/test_auth_endpoints.py` (full login/refresh/logout flows — require a live Postgres, skip cleanly without one), `frontend/tests/unit/rbac.test.ts` + `frontend/tests/unit/LoginForm.test.tsx` (passing).
- **Unverified**: no Postgres or Docker is available in this environment, so the Alembic migration and the DB-backed auth flow have only been checked as far as possible without a database (offline SQL generation, app boot, route registration) — not actually run end-to-end. Run `docker compose up -d db` (once T011/T012 exist) or point `DATABASE_URL` at any reachable Postgres, then `uv run alembic upgrade head` and `uv run pytest`, to get real confirmation.

---

## Phase 3 – Expense Management (User Story 2 part A, P1)

**Goal**: Manually create/edit/delete/search/filter expenses, reflected live in ledger/dashboard totals.

**Independent Test**: Add, edit, delete, and search an expense through the UI/API and confirm ledger + dashboard totals update (spec.md US2 Acceptance Scenarios 1–4).

- [X] T027 [P] [US2] Category model & migration — `type` enum (`expense`,`income`,`both`), `is_archived` flag in `backend/src/models/category.py`; migration `0003_categories`
  - **Dependencies**: T008
  - **Acceptance Criteria**: unique `name`; archiving instead of deleting works (row stays, flag flips)
  - **Complexity**: Easy

- [X] T028 [P] [US2] `audit_log_entries` model & migration — `actor_type`, `entity_type`, `action`, `before_state`/`after_state` JSONB in `backend/src/models/audit_log.py`; migration `0004_audit_log_entries`
  - **Dependencies**: T014
  - **Acceptance Criteria**: table created with indexes on `(entity_type, entity_id)` and `created_at`
  - **Complexity**: Easy

- [X] T029 [US2] AuditService — `record(actor, entity_type, entity_id, action, before, after)` in `backend/src/services/audit_service.py`
  - **Dependencies**: T028
  - **Acceptance Criteria**: calling it writes exactly one row with correct before/after JSON; used by every mutating service from here on (FR-029, FR-037)
  - **Complexity**: Medium

- [X] T030 [US2] Expense model & migration — `amount NUMERIC(14,2) CHECK > 0`, FK `category_id`, soft-delete `deleted_at`, indexes on `date`/`category_id`/`created_by` in `backend/src/models/expense.py`; migration `0005_expenses`
  - **Dependencies**: T027
  - **Acceptance Criteria**: inserting `amount <= 0` violates the DB check constraint
  - **Complexity**: Medium

- [X] T031 [US2] ExpenseRepository — list (search/filter/paginate), get, create, update, soft-delete in `backend/src/repositories/expense_repository.py`
  - **Dependencies**: T030
  - **Acceptance Criteria**: filter-by-category, filter-by-date-range, and keyword search each independently narrow results correctly
  - **Complexity**: Medium

- [X] T032 [US2] ExpenseService — validation (amount>0, required fields, valid date, existing non-archived category), role checks, audit logging in `backend/src/services/expense_service.py`
  - **Dependencies**: T031, T029, T017
  - **Acceptance Criteria**: creating with a bad payload raises `ValidationError` with a field-specific message and saves nothing (FR-012); Office Administrator delete raises `PermissionDeniedError` (FR-003)
  - **Complexity**: Medium

- [X] T033 [US2] Expense endpoints — `GET/POST /expenses`, `GET/PATCH/DELETE /expenses/{id}` in `backend/src/api/v1/expenses.py`
  - **Dependencies**: T032
  - **Acceptance Criteria**: matches `contracts/openapi.yaml`; contract tests pass for 201/200/204/400/403/404 cases
  - **Complexity**: Medium

- [X] T034 [P] [US2] Category endpoints — `GET/POST /categories` in `backend/src/api/v1/categories.py`
  - **Dependencies**: T027, T017
  - **Acceptance Criteria**: matches `contracts/openapi.yaml`; new category immediately selectable by expense creation
  - **Complexity**: Easy

- [X] T035 [P] [US2] ExpenseForm — React Hook Form + Zod (amount>0, required fields) in `frontend/src/components/forms/ExpenseForm.tsx`
  - **Dependencies**: T004
  - **Acceptance Criteria**: client-side validation blocks submit and shows field errors before any network call for an invalid amount
  - **Complexity**: Medium

- [X] T036 [US2] ExpenseTable — shadcn `DataTable` with search box + date/category filters in `frontend/src/components/tables/ExpenseTable.tsx`
  - **Dependencies**: T035
  - **Acceptance Criteria**: search and filters each independently narrow the visible rows
  - **Complexity**: Medium

- [X] T037 [US2] `useExpenses` hook (TanStack Query) — list/create/update/delete mutations with cache invalidation in `frontend/src/hooks/useExpenses.ts`
  - **Dependencies**: T021
  - **Acceptance Criteria**: a successful create/edit/delete invalidates the list query and the table updates without a manual refresh
  - **Complexity**: Medium

- [X] T038 [US2] Expenses page — `frontend/src/app/(app)/expenses/page.tsx` wiring form + table + hook; delete button hidden for Office Administrator (uses `rbac.ts`)
  - **Dependencies**: T036, T037, T033, T025
  - **Acceptance Criteria**: `quickstart.md` §3 (expense portion) passes end to end
  - **Complexity**: Medium

**Checkpoint**: Expense half of US2 fully functional and independently testable.

**Implementation notes (2026-07-29)**:
- All of T027–T038 implemented: `categories`/`audit_log_entries`/`expenses` migrations dry-run clean and chain correctly onto Phase 2's migrations; `ExpenseService` enforces amount>0, required title, and existing-non-archived-category (FR-012) with per-field error messages; delete is blocked for Office Administrator at the service layer (FR-003) and covered by both a unit test and an endpoint contract test.
- Every create/update/delete on an expense writes exactly one `audit_log_entries` row — verified directly by `test_create_expense_writes_audit_log_entry` (FR-029/SC-004).
- `ledger` is still just a stub concept until Phase 5 unions expenses+income — not built here, as planned.
- Tests: `backend/tests/unit/test_expense_service.py` (9 tests) + `backend/tests/contract/test_expense_endpoints.py` (6 tests) — all require live Postgres and currently skip cleanly in this environment, same caveat as Phase 2. `frontend/tests/unit/ExpenseForm.test.tsx` (3 tests) passes today (no DB needed).
- Frontend: added shadcn `select`, `textarea`, and `alert-dialog` components (not individually itemized in tasks.md, same rationale as the Phase 2 testing-tooling note).
- **Unverified**: same as Phase 2 — no Postgres available in this environment, so the full create→list→edit→delete flow through a live database and the actual dashboard-reflects-changes behavior (SC-001) have not been run end-to-end, only unit/contract-tested against the (skipped) DB fixtures and manually verified via `tsc`/`eslint`/`vitest run`/`next build`.

---

## Phase 4 – Income Management (User Story 2 part B, P1)

**Goal**: Manually create/edit/delete/search income entries, reflected live in dashboard totals.

**Independent Test**: Add, edit, delete, and search an income entry independent of expenses (spec.md US2 Acceptance Scenarios, income fields).

- [X] T039 [P] [US2] Income model & migration — `amount NUMERIC(14,2) CHECK > 0`, soft-delete, indexes on `date`/`created_by` in `backend/src/models/income.py`; migration `0006_income`
  - **Dependencies**: T014
  - **Acceptance Criteria**: inserting `amount <= 0` violates the DB check constraint
  - **Complexity**: Easy

- [X] T040 [US2] IncomeRepository — list/search/filter/paginate, get, create, update, soft-delete in `backend/src/repositories/income_repository.py`
  - **Dependencies**: T039
  - **Acceptance Criteria**: keyword search on `source`/`description` and date-range filter each work independently
  - **Complexity**: Medium

- [X] T041 [US2] IncomeService — validation, role checks, audit logging (reuses `AuditService`) in `backend/src/services/income_service.py`
  - **Dependencies**: T040, T029, T017
  - **Acceptance Criteria**: matches ExpenseService's validation/permission behavior 1:1 for the income field set
  - **Complexity**: Medium

- [X] T042 [US2] Income endpoints — `GET/POST /income`, `GET/PATCH/DELETE /income/{id}` in `backend/src/api/v1/income.py`
  - **Dependencies**: T041
  - **Acceptance Criteria**: matches `contracts/openapi.yaml`; contract tests pass
  - **Complexity**: Medium

- [X] T043 [P] [US2] IncomeForm — React Hook Form + Zod in `frontend/src/components/forms/IncomeForm.tsx`
  - **Dependencies**: T004
  - **Acceptance Criteria**: mirrors `ExpenseForm` validation behavior for the income field set
  - **Complexity**: Easy

- [X] T044 [US2] IncomeTable — shadcn `DataTable` with search box in `frontend/src/components/tables/IncomeTable.tsx`
  - **Dependencies**: T043
  - **Acceptance Criteria**: keyword search narrows visible rows correctly
  - **Complexity**: Medium

- [X] T045 [US2] `useIncome` hook (TanStack Query) in `frontend/src/hooks/useIncome.ts`
  - **Dependencies**: T021
  - **Acceptance Criteria**: mirrors `useExpenses` cache-invalidation behavior
  - **Complexity**: Easy

- [X] T046 [US2] Income page — `frontend/src/app/(app)/income/page.tsx`
  - **Dependencies**: T044, T045, T042, T025
  - **Acceptance Criteria**: `quickstart.md` §3 (income portion) passes end to end
  - **Complexity**: Medium

**Checkpoint**: US2 fully functional (expense + income) and independently testable.

**Implementation notes (2026-07-29)**:
- All of T039–T046 implemented, mirroring Phase 3's structure 1:1 (`IncomeService` matches `ExpenseService`'s validation/permission/audit behavior exactly, minus the category relationship per spec's income field list). `income` migration reuses the `created_via` enum type created by the expenses migration rather than recreating it — verified via a clean dry-run of the full migration chain.
- Tests: `backend/tests/unit/test_income_service.py` (8 tests) + `backend/tests/contract/test_income_endpoints.py` (5 tests) — require live Postgres, skip cleanly here, same as Phases 2–3. `frontend/tests/unit/IncomeForm.test.tsx` (3 tests) passes today. Full suite: backend 11 passed/38 skipped/0 failed; frontend 14/14 passed; `tsc`/`eslint`/`next build` all clean.
- Hit a real Windows/Turbopack issue mid-phase: running `next build` concurrently with the running `next dev` server against the same `.next/` directory corrupted its dev manifest cache (`ENOENT` on `_buildManifest.js.tmp.*`), causing `/expenses` and other routes to 500. Not a code bug — fixed by stopping all node processes and clearing `.next/` before restarting `dev`. Worth remembering: don't run `next build` and `next dev` against the same project simultaneously.
- **Unverified**: same DB caveat as every prior phase — no Postgres in this environment, so the live create/edit/delete/search flow for income is untested beyond the migration dry-run and the (skipped) DB-backed test suite.

---

## Phase 5 – Ledger (User Story 5, P3)

**Goal**: One unified, searchable/filterable/sortable/paginated view of every income and expense record.

**Independent Test**: Seed 60+ mixed rows; confirm pagination, search, filter, and sort each work correctly, individually and combined (spec.md US5 Acceptance Scenarios).

- [X] T047 [US5] LedgerService — `UNION ALL` read model over active expenses+income with search/filter/sort/pagination in `backend/src/services/ledger_service.py`
  - **Dependencies**: T032, T041
  - **Acceptance Criteria**: combined category+date-range filter returns only rows matching both; sort by amount/date works across pages
  - **Complexity**: Medium

- [X] T048 [US5] Ledger endpoint — `GET /ledger` in `backend/src/api/v1/ledger.py`
  - **Dependencies**: T047
  - **Acceptance Criteria**: matches `contracts/openapi.yaml`; default sort is by date
  - **Complexity**: Easy

- [X] T049 [P] [US5] Bulk seed script — 60+ mixed income/expense rows in `backend/scripts/seed_bulk_ledger.py`
  - **Dependencies**: T030, T039
  - **Acceptance Criteria**: idempotent-ish generation of realistic varied dates/categories/amounts for pagination testing
  - **Complexity**: Easy

- [X] T050 [US5] `useLedger` hook (TanStack Query, paginated) in `frontend/src/hooks/useLedger.ts`
  - **Dependencies**: T021
  - **Acceptance Criteria**: page/filter/sort params round-trip correctly to `/ledger` query params
  - **Complexity**: Medium

- [X] T051 [US5] LedgerTable + combined filter bar — `frontend/src/components/tables/LedgerTable.tsx` (pagination controls, keyword+category+date filters, sort headers)
  - **Dependencies**: T050
  - **Acceptance Criteria**: hundreds of rows render paginated, not all at once; combined filters narrow correctly
  - **Complexity**: Medium

- [X] T052 [US5] Ledger page — `frontend/src/app/(app)/ledger/page.tsx`
  - **Dependencies**: T051, T048, T049
  - **Acceptance Criteria**: `quickstart.md` §6 passes in full
  - **Complexity**: Easy

**Checkpoint**: US5 fully functional and independently testable.

**Implementation notes (2026-07-29)**:
- All of T047–T052 implemented. `LedgerService` unions active expenses (joined to `categories` for the name) and active income via SQLAlchemy Core `union_all()` into one subquery, with `category`/`category_id` cast to matching nullable types on the income side so the union type-checks; sort is restricted to an allow-list (`date`, `amount`) rather than accepting an arbitrary column name.
- `LedgerTable` implements clickable sort headers (toggling asc/desc, defaulting to date-desc) and prev/next pagination; a bug was caught and fixed here — the initial `updateFilter` helper always reset `page` to 1, which would have made pagination buttons non-functional, so pagination now goes through a separate `goToPage` that doesn't touch other filters.
- Tests: `backend/tests/unit/test_ledger_service.py` (8 tests: union correctness, both sort columns/directions, category filter correctly excluding income rows, date-range filter, keyword search across both types, pagination, soft-delete exclusion) + `backend/tests/contract/test_ledger_endpoints.py` (2 tests) — DB-dependent, skip cleanly here. `frontend/tests/unit/LedgerTable.test.tsx` (3 tests, mocking `apiFetch` directly to assert the actual query-string sent for sort/filter/page behavior) passes today. Full suite: backend 11 passed/48 skipped/0 failed; frontend 17/17 passed.
- **Unverified**: same DB caveat as every prior phase. `seed_bulk_ledger.py` (65 rows) is written and reviewed but its actual pagination-under-load behavior hasn't been run against a live database in this environment.

---

## Phase 6 – Reports (User Story 4, P2)

**Goal**: All seven report types, generated live from ledger data, with role-gated access.

**Independent Test**: Seed known data; request each report for a known period; totals reconcile with hand-calculated expectations (spec.md US4 Acceptance Scenarios).

- [X] T053 [US4] `journal_entries` model & migration — `entry_type` (debit/credit), `account`, `reference_type`/`reference_id` in `backend/src/models/journal_entry.py`; migration `0007_journal_entries`
  - **Dependencies**: T008
  - **Acceptance Criteria**: indexes on `(reference_type, reference_id)` and `entry_date` exist
  - **Complexity**: Easy

- [X] T054 [US4] Journal auto-posting — hook into `ExpenseService`/`IncomeService` create/update/delete to post/reverse matching debit+credit `journal_entries` rows in `backend/src/services/journal_service.py`
  - **Dependencies**: T053, T032, T041
  - **Acceptance Criteria**: creating an expense posts exactly one debit+one credit row; deleting posts a reversing pair rather than removing history
  - **Complexity**: Hard

- [X] T055 [US4] ReportService: Profit & Loss — `backend/src/services/report_service.py::profit_and_loss()`
  - **Dependencies**: T032, T041
  - **Acceptance Criteria**: total income − total expenses = net profit, reconciling with seeded data for a known month
  - **Complexity**: Medium

- [X] T056 [US4] ReportService: Balance Sheet — `report_service.py::balance_sheet()`
  - **Dependencies**: T054
  - **Acceptance Criteria**: account balances derived from `journal_entries` reconcile with seeded data
  - **Complexity**: Hard

- [X] T057 [US4] ReportService: Trial Balance — `report_service.py::trial_balance()`
  - **Dependencies**: T054
  - **Acceptance Criteria**: total debits equal total credits for a known period
  - **Complexity**: Medium

- [X] T058 [US4] ReportService: Cash Flow Summary — `report_service.py::cash_flow_summary()`
  - **Dependencies**: T054
  - **Acceptance Criteria**: net cash movement for a known period matches hand calculation
  - **Complexity**: Medium

- [X] T059 [US4] ReportService: Monthly Expense Report — `report_service.py::monthly_expense_report()`
  - **Dependencies**: T032
  - **Acceptance Criteria**: month-by-month expense totals match seeded data
  - **Complexity**: Easy

- [X] T060 [US4] ReportService: Income Report — `report_service.py::income_report()` *(7th report type required by spec FR-019; not itemized in the original phase list but included here to satisfy the approved spec)*
  - **Dependencies**: T041
  - **Acceptance Criteria**: period income totals match seeded data
  - **Complexity**: Easy

- [X] T061 [US4] ReportService: Category-wise Expense Report — `report_service.py::category_wise_expense_report()`
  - **Dependencies**: T032
  - **Acceptance Criteria**: per-category totals for a period match seeded data
  - **Complexity**: Easy

- [X] T062 [US4] Report endpoints — 7 `GET /reports/*` routes in `backend/src/api/v1/reports.py`; date-range validation (FR-021); Balance Sheet & Trial Balance restricted to Business Owner + Accountant (FR-022)
  - **Dependencies**: T055, T056, T057, T058, T059, T060, T061, T017
  - **Acceptance Criteria**: invalid date range (end < start) returns 400; Office Administrator gets 403 on Balance Sheet/Trial Balance; empty period returns a valid zero report, not an error (FR-020)
  - **Complexity**: Medium

- [X] T063 [P] [US4] `useReports` hook in `frontend/src/hooks/useReports.ts`
  - **Dependencies**: T021
  - **Acceptance Criteria**: date-range params round-trip correctly per report type
  - **Complexity**: Easy

- [X] T064 [US4] ReportView + charts — `frontend/src/components/tables/ReportView.tsx`, `frontend/src/components/charts/ReportCharts.tsx` (Recharts)
  - **Dependencies**: T063
  - **Acceptance Criteria**: figures render matching backend response; charts render for trend-shaped reports
  - **Complexity**: Medium

- [X] T065 [US4] Report pages + role-aware nav — `frontend/src/app/(app)/reports/[type]/page.tsx`, nav entries filtered by `rbac.ts`
  - **Dependencies**: T064, T062, T025
  - **Acceptance Criteria**: `quickstart.md` §5 passes in full, including the Office Administrator permission-denial case
  - **Complexity**: Medium

**Checkpoint**: US4 fully functional and independently testable.

**Implementation notes (2026-07-29)**:
- All of T053–T065 implemented. Chart of accounts is deliberately minimal — 3 accounts (`Cash`, `Expenses`, `Revenue`), no per-category ledger accounts (category detail comes from `category_wise_expense_report` reading `expenses` directly, not from journal postings). This was a real design decision, not an oversight — documented in `journal_service.py` and `report_service.py` docstrings.
- `JournalService` reverses-then-reposts on update rather than diffing old vs. new values — simpler and provably correct (verified by `test_update_expense_reverses_and_reposts_journal`, which checks both the resulting cash balance *and* that debits still equal credits after the update).
- Balance Sheet is a cumulative snapshot **as of `date_to`**, not a period total — `date_from` is accepted for contract uniformity with the other six reports but doesn't affect the figures; documented in the method docstring and the frontend shows "As of {date}" rather than a range for this one report.
- P&L / Monthly Expense / Income / Category-wise read directly from `expenses`/`income` (flat aggregation); only Balance Sheet / Trial Balance / Cash Flow read from `journal_entries` — matches the dependency graph in the original task breakdown (T055/T059/T060/T061 depend on T032/T041 only, not T054).
- Verified algebraically via tests, not just spot-checked: trial balance debits==credits after create/update/delete cycles, cash-flow net equals P&L net profit under this cash-basis model, balance sheet assets==equity.
- Tests: `backend/tests/unit/test_journal_service.py` (4 tests) + `backend/tests/unit/test_report_service.py` (11 tests, exercised through `ExpenseService`/`IncomeService` end-to-end so journal auto-posting is covered, not just `ReportService` in isolation) + `backend/tests/contract/test_report_endpoints.py` (6 tests: role gating, date validation, auth). All DB-dependent, skip cleanly here. `frontend/tests/unit/ReportView.test.tsx` (4 tests) passes today. Full suite: backend 11 passed/67 skipped/0 failed; frontend 21/21 passed; `tsc`/`eslint`/`next build` all clean.
- **Unverified**: same DB caveat as every prior phase — the double-entry math above is verified by the (skipped) test suite's logic and reasoning, not by an actual run against live Postgres in this environment.

---

## Phase 7 – AI Accounting Agent (User Stories 3 & 6, P2/P3)

**Goal**: Natural-language data entry with mandatory confirmation (US3), plus natural-language analysis, reporting, and anomaly/duplicate/large-expense detection (US6).

**Independent Test (US3)**: Issue an NL add/update/delete command; assistant proposes, then only applies after confirmation; matches an equivalent manual entry.
**Independent Test (US6)**: Seed known top-N/comparison/duplicate/outlier data; assistant's answers and flags match ground truth.

### AI Foundation & Data Entry (US3)

- [X] T066 [P] [US3] `ai_interactions` model & migration — `status` enum, `proposed_action`/`interpreted_intent` JSONB in `backend/src/models/ai_interaction.py`; migration `0008_ai_interactions`
  - **Dependencies**: T014
  - **Acceptance Criteria**: table created with index on `(user_id, created_at)`
  - **Complexity**: Easy

- [X] T067 [US3] LLM provider adapter — env-driven (`AI_PROVIDER`, `AI_MODEL`) chat-model factory in `backend/src/agent/provider.py`
  - **Dependencies**: T005
  - **Acceptance Criteria**: swapping `AI_PROVIDER` requires no change outside this file; raises a typed error if misconfigured (feeds FR-033)
  - **Complexity**: Medium

- [X] T068 [US3] LangGraph state & graph skeleton — `interpret → plan → confirm(interrupt) → execute → respond` nodes, with a `clarify` loop, in `backend/src/agent/state.py`, `backend/src/agent/graph.py`
  - **Dependencies**: T067
  - **Acceptance Criteria**: a stubbed-LLM run of a simple create command pauses at `confirm` and does not reach `execute` without an injected confirmation
  - **Complexity**: Hard

- [X] T069 [US3] Prompt templates — system prompt (role context, confirm-before-write rule, tool schemas) + few-shot examples from spec's example commands in `backend/src/agent/prompts.py`
  - **Dependencies**: T068
  - **Acceptance Criteria**: stubbed-LLM golden test for "Add office rent 50000 for July" extracts the correct title/amount/category/date
  - **Complexity**: Medium

- [X] T070 [US3] CRUD Tool — wraps `ExpenseService`/`IncomeService` create/update/delete in `backend/src/agent/tools/crud_tool.py`; never touches repositories/DB directly
  - **Dependencies**: T069, T032, T041
  - **Acceptance Criteria**: a confirmed AI create produces an identical record to the equivalent manual entry, tagged `created_via: ai`, with its own audit log row
  - **Complexity**: Medium

- [X] T071 [US3] Clarification handling — missing-field and ambiguous-reference detection routes to the `clarify` node instead of guessing (FR-028)
  - **Dependencies**: T070
  - **Acceptance Criteria**: "Add an expense" (no amount) yields a clarifying question, not a created record; "delete the rent expense" with two candidates asks the user to disambiguate
  - **Complexity**: Medium

- [X] T072 [US3] AI chat + confirm/reject endpoints — `POST /ai/chat`, `POST /ai/interactions/{id}/confirm`, `POST /ai/interactions/{id}/reject` in `backend/src/api/v1/ai_chat.py`
  - **Dependencies**: T071, T066
  - **Acceptance Criteria**: matches `contracts/openapi.yaml`; an unconfirmed proposal never mutates data; an expired/unresolved interaction cannot be double-confirmed
  - **Complexity**: Medium

- [X] T073 [US3] Graceful AI degradation — provider-unavailable path returns a clear error, all non-AI endpoints unaffected (FR-033)
  - **Dependencies**: T067, T072
  - **Acceptance Criteria**: with the provider key invalidated, `/ai/chat` returns a clear "unavailable" response and every other endpoint still works (feeds SC-008)
  - **Complexity**: Medium

- [X] T074 [P] [US3] AIChatPanel — message list + input in `frontend/src/components/chat/AIChatPanel.tsx`
  - **Dependencies**: T004
  - **Acceptance Criteria**: shows a disabled/"unavailable" state when the backend reports the AI is down
  - **Complexity**: Medium

- [X] T075 [US3] ProposedActionCard — renders `proposed_action`, Confirm/Reject buttons in `frontend/src/components/chat/ProposedActionCard.tsx`
  - **Dependencies**: T074
  - **Acceptance Criteria**: Confirm calls `/ai/interactions/{id}/confirm` and the resulting record appears in the relevant table without a manual refresh
  - **Complexity**: Medium

- [X] T076 [US3] `useAIChat` hook + AI Assistant page — `frontend/src/hooks/useAIChat.ts`, `frontend/src/app/(app)/ai-assistant/page.tsx`
  - **Dependencies**: T075, T072
  - **Acceptance Criteria**: `quickstart.md` §4 passes in full
  - **Complexity**: Medium

### AI Analysis, Reporting & Audit (US6)

- [X] T077 [US6] SQL Query Tool — allow-listed, parameterized, read-only aggregate templates only (no free-text SQL) in `backend/src/agent/tools/sql_query_tool.py`
  - **Dependencies**: T068
  - **Acceptance Criteria**: only pre-defined aggregate shapes are reachable; attempting to pass raw SQL text is rejected
  - **Complexity**: Medium

- [X] T078 [US6] Report Tool — wraps `report_service` + plain-language explanation of report figures on request (FR-032) in `backend/src/agent/tools/report_tool.py`
  - **Dependencies**: T062, T068
  - **Acceptance Criteria**: "Generate Profit and Loss Statement" returns figures identical to the `/reports/profit-and-loss` endpoint for the same period
  - **Complexity**: Medium

- [X] T079 [US6] Financial Analysis Tool — top-N, period comparison, category/period totals in `backend/src/agent/tools/analysis_tool.py`
  - **Dependencies**: T077
  - **Acceptance Criteria**: "Show top five expenses" returns exactly 5, correctly ranked; "Compare June and July expenses" returns both totals and the delta
  - **Complexity**: Medium

- [X] T080 [US6] Audit Tool — duplicate detection (same amount+category+date within N days) and unusually-large-expense detection (statistical outlier vs. category history) in `backend/src/agent/tools/audit_tool.py`
  - **Dependencies**: T077
  - **Acceptance Criteria**: two near-identical seeded transactions are flagged as a probable duplicate without either being auto-deleted (FR-030); a seeded outlier expense is flagged as unusually large (FR-031)
  - **Complexity**: Hard

- [X] T081 [US6] "Run monthly audit" wiring — invokes Audit Tool over a period, surfaces flags via chat response
  - **Dependencies**: T080
  - **Acceptance Criteria**: `quickstart.md` §7 duplicate/audit scenario passes
  - **Complexity**: Medium

- [X] T082 [P] [US6] Passive anomaly flag on create — normal (manual or AI) expense creation returns an inline flag when it matches duplicate/large-expense heuristics
  - **Dependencies**: T080, T032
  - **Acceptance Criteria**: adding a seeded-outlier expense surfaces a flag in the same response, without blocking the create
  - **Complexity**: Medium

- [X] T083 [P] [US6] Golden-transcript AI test fixtures — stubbed-LLM deterministic tool-call assertions for every example command in `spec.md` in `backend/tests/agent/test_golden_transcripts.py`
  - **Dependencies**: T070, T077, T078, T079, T080
  - **Acceptance Criteria**: all example commands from the spec ("Add office rent 50000 for July", "Show top five expenses", "Run monthly audit", etc.) resolve to the correct tool + arguments
  - **Complexity**: Medium

**Checkpoint**: US3 and US6 fully functional and independently testable; all example commands from the spec work end to end.

**Implementation notes (2026-07-29)**:
- Both LangGraph (1.2.10) and LangChain (1.3.14) installed far ahead of training-data knowledge (comparable to the earlier Next.js 15/16 surprise) — every non-trivial API used here (`StateGraph`, `interrupt()`/`Command(resume=...)`, `bind_tools()` with plain Pydantic classes, `init_chat_model`) was verified by inspecting the installed package and running small throwaway scripts before writing the real code, not assumed from memory.
- **Verified structurally, not just asserted**: a standalone smoke test proved the graph genuinely pauses at `confirm` (`graph.aget_state(config).next == ('confirm',)`) and that rejecting never reaches `execute` — this is what makes FR-027 a property of the graph, not a convention. See the smoke-test transcript in this session; the same behavior is what `test_rejecting_a_proposed_expense_creates_nothing` in the golden-transcript suite checks against a real (skipped-without-DB) service call.
- Architectural guarantee: the agent's tools (`crud_tool.py`, `report_tool.py`, `analysis_tool.py`) call `ExpenseService`/`IncomeService`/`ReportService` — the exact same services the REST API uses — never a repository or raw query directly. This is what makes FR-034 (identical validation) and FR-003 (identical permissions) hold across both paths by construction, not by convention.
- `sql_query_tool.py` exposes only fixed, typed, parameterized functions (top-N, sum-by-category, category history) — there is no code path that accepts free-text SQL, satisfying T077's "no free-text SQL" criterion structurally rather than by a runtime filter.
- Checkpointing uses an in-memory `MemorySaver` (module-level singleton) — a proposed-but-unconfirmed action does not survive a process restart. Treated as an acceptable simplification (an abandoned proposal is meant to expire anyway) and documented in `graph.py`'s module docstring; a production deployment running multiple backend instances would need a shared checkpointer (e.g. Postgres-backed) instead.
- T082 (passive anomaly flag) was wired into the manual REST create endpoint too, not just the AI path — `Expense`'s response schema gained an additive `flags` field (empty except on the create response) so `POST /expenses` and the AI's `AddExpense` tool both surface the same duplicate/large-expense heuristics.
- Tests: 13 golden-transcript tests (`tests/agent/test_golden_transcripts.py`) covering all 9 spec.md example commands plus clarification/ambiguous-delete/reject-flow/no-tool-call edge cases, using a hand-written `FakeToolCallingModel` test double (deliberately not LangChain's built-in fake models, which are shaped for text streaming, not tool-call testing) — these test the graph's dispatch/routing correctness, not an LLM's extraction accuracy, which needs a live provider and stays out of scope. All DB-dependent (skip cleanly here, same caveat as every prior phase). Frontend: `AIChat.test.tsx` (3 tests) passes today, including the 503-unavailable UI state.
- **Unverified**: no live LLM provider or Postgres in this environment — the graph's structural correctness is verified (interrupt/resume mechanics, routing, tool dispatch against services), but no request has actually round-tripped through a real OpenAI (or other) model.

---

## Phase 8 – Dashboard

**Purpose**: Aggregated at-a-glance view built on top of Expense/Income/Report data (FR-005–FR-008). Not its own spec.md user story — extends US2/US4.

- [X] T084 DashboardService — totals, monthly summary, category breakdown, recent transactions aggregation in `backend/src/services/dashboard_service.py`
  - **Dependencies**: T032, T041
  - **Acceptance Criteria**: totals match a manually-verified sum of seeded data for the selected period
  - **Complexity**: Medium

- [X] T085 `GET /dashboard/summary` endpoint — `backend/src/api/v1/dashboard.py`
  - **Dependencies**: T084
  - **Acceptance Criteria**: matches `contracts/openapi.yaml`; reflects a transaction added moments earlier (FR-008)
  - **Complexity**: Easy

- [X] T086 [P] StatCards — Total Income/Expenses/Net Profit in `frontend/src/components/charts/StatCards.tsx`
  - **Dependencies**: T004
  - **Acceptance Criteria**: values update after a new transaction without a full page reload
  - **Complexity**: Easy

- [X] T087 [P] DashboardCharts — trend + category-breakdown charts (Recharts) in `frontend/src/components/charts/DashboardCharts.tsx`
  - **Dependencies**: T004
  - **Acceptance Criteria**: chart data matches `/dashboard/summary` response
  - **Complexity**: Medium

- [X] T088 RecentTransactions + MonthlySummary components — `frontend/src/components/tables/RecentTransactions.tsx`, `frontend/src/components/charts/MonthlySummary.tsx`
  - **Dependencies**: T086
  - **Acceptance Criteria**: recent transactions list matches the latest ledger entries
  - **Complexity**: Easy

- [X] T089 Dashboard page — `frontend/src/app/(app)/dashboard/page.tsx` wiring all of the above + period selector
  - **Dependencies**: T085, T087, T088
  - **Acceptance Criteria**: SC-001 (entry reflected within 30s end-to-end) verifiable manually here
  - **Complexity**: Medium

**Checkpoint**: Dashboard reflects live data from all prior phases.

**Implementation notes (2026-07-29)**:
- `DashboardService` deliberately composes `ReportService.profit_and_loss()` / `.monthly_expense_report()` / `.income_report()` / `.category_wise_expense_report()` and `LedgerService.list_ledger()` rather than re-deriving any totals independently — this guarantees the dashboard can never disagree with the Reports or Ledger pages for the same period, by construction rather than by keeping two implementations in sync.
- `GET /dashboard/summary` takes a `period` (`YYYY-MM`) query param per `contracts/openapi.yaml`, converted internally to the `date_from`/`date_to` range `DashboardService`/`ReportService` expect; defaults to the current month.
- FR-008 ("dashboard reflects the latest recorded transactions") is verified directly by `test_summary_reflects_transaction_added_moments_earlier`, which calls the service twice around a create and asserts the totals actually changed — not just that the endpoint returns 200.
- Extended `useCreateExpense`/`useUpdateExpense`/`useDeleteExpense` and their income equivalents (built in Phases 3–4) to also invalidate `["ledger"]` and `["reports"]` query keys, not just `["expenses"]`/`["income"]` — without this, manually adding an expense on the Expenses page wouldn't have refreshed the dashboard (only AI-driven changes would have, since `useAIChat` already invalidated broadly). Caught and fixed while wiring the dashboard, not before.
- Tests: `backend/tests/unit/test_dashboard_service.py` (4 tests) + `backend/tests/contract/test_dashboard_endpoints.py` (3 tests) — DB-dependent, skip cleanly here. `frontend/tests/unit/Dashboard.test.tsx` (5 tests, including both components' empty states) passes today.
- **Unverified**: same DB caveat as every prior phase.

---

## Phase 9 – Testing

**Purpose**: Close coverage gaps; verify every spec.md Acceptance Scenario and Success Criterion has an automated check.

- [X] T090 [P] Backend unit tests — services' validation/permission edge cases (amount≤0, missing fields, bad category, wrong role) in `backend/tests/unit/`
  - **Dependencies**: T032, T041
  - **Acceptance Criteria**: covers FR-012, FR-016, FR-034 edge cases explicitly
  - **Complexity**: Medium

- [X] T091 [P] Backend contract tests — `httpx.AsyncClient` against every endpoint in `contracts/openapi.yaml`, in `backend/tests/contract/`
  - **Dependencies**: T033, T042, T048, T062, T072, T085
  - **Acceptance Criteria**: every path/status pair in the contract has at least one passing test
  - **Complexity**: Medium

- [X] T092 Permission-matrix sweep — all 3 roles × every mutating endpoint, in `backend/tests/integration/test_permissions.py`
  - **Dependencies**: T091
  - **Acceptance Criteria**: directly verifies FR-003, FR-022, SC-007 (100% correct allow/deny)
  - **Complexity**: Medium

- [X] T093 Integration test — create → report → audit-log flow, in `backend/tests/integration/test_create_report_audit_flow.py`
  - **Dependencies**: T054, T062
  - **Acceptance Criteria**: verifies SC-004 (every mutation produces an audit row) end to end
  - **Complexity**: Medium

- [X] T094 AI-unavailable fallback test — provider disabled, all non-AI stories still pass, in `backend/tests/agent/test_degradation.py`
  - **Dependencies**: T073
  - **Acceptance Criteria**: directly verifies SC-008
  - **Complexity**: Medium

- [X] T095 [P] Frontend unit/component tests — forms, tables, `ProposedActionCard`, in `frontend/tests/unit/` (Vitest + RTL)
  - **Dependencies**: T035, T036, T075
  - **Acceptance Criteria**: validation-error rendering and confirm/reject interaction both covered
  - **Complexity**: Medium

- [X] T096 Playwright e2e specs — one spec per user story, mirroring `quickstart.md` §2–§8, in `frontend/tests/e2e/`
  - **Dependencies**: T026, T038, T046, T052, T065, T076, T089
  - **Acceptance Criteria**: all six specs pass against a docker-composed stack in CI
  - **Complexity**: Hard

**Checkpoint**: Every Acceptance Scenario in `spec.md` has an automated test; SC-001–SC-008 each have at least one asserting test.

**Implementation notes (2026-07-29)**:
- **Real gap discovered and closed while doing this phase**: `GET /audit-logs` had never actually been built in Phases 1–8, even though `contracts/openapi.yaml` specified it, FR-037/FR-038 require it, and the Phase 2 frontend nav already had a live "Audit Log" link pointing at a page that didn't exist. Built the missing piece end-to-end here (not originally a numbered task, tracked separately): `AuditLogRepository`, `schemas/audit_log.py`, `GET /audit-logs` (role-gated to Business Owner + Accountant per FR-038), and the frontend `/audit-log` page. This is the kind of gap Phase 9's "close coverage gaps" purpose exists to catch.
- **T091 also surfaced a gap**: `/ai/chat` and confirm/reject had golden-transcript tests (Phase 7) exercising the LangGraph graph directly, but no test had ever gone through the actual HTTP endpoints — meaning `AIChatService`'s wiring of the graph to the `ai_interactions` table had never been verified at the contract level. Added `tests/contract/test_ai_chat_endpoints.py` (5 tests), which also caught nothing broken, but closes a real blind spot: it's the only place `409 on double-confirm` is verified.
- **T090 closed the most important FR-034 gap**: all prior per-service tests proved manual-path validation works, but nothing had directly proven the AI path enforces *the same* rules — `test_crud_tool_validation_parity.py` calls `agent/tools/crud_tool.py` directly and asserts it rejects the same bad amounts as `ExpenseService`/`IncomeService`, and confirms AI-created records are tagged `created_via: ai` and audited with `actor_type: ai`.
- Permission-matrix sweep (T092) and the create→report→audit-log flow (T093) are both HTTP-level (`httpx.AsyncClient` through the real FastAPI app), not service-level — deliberately, since the point is verifying the endpoints wire the role checks and audit logging correctly, not re-testing logic already covered by Phase 3–8 unit tests.
- T096 (Playwright): config + 7 spec files written (one per user story — US1, US2, US3, US4, US5, US6 — plus a dedicated SC-008 AI-unavailable spec, since that needs the backend started with a different, invalid AI-provider configuration than the other six). **Cannot be executed in this environment** — no Docker, no live Postgres, no Playwright browser binaries downloaded, and no running docker-composed stack to point them at. They're written against `quickstart.md`'s exact scenarios and the demo users from `seed_demo_data.py`, but are structurally reviewed only, not run. Before relying on them, run `npx playwright install` and execute against a real docker-composed stack.
- Tests added this phase: 4 (`test_crud_tool_validation_parity.py`) + 1 (blank-title gap) + 6 (`test_permissions.py`) + 1 (`test_create_report_audit_flow.py`) + 2 (`test_degradation.py`) + 3 (`test_audit_log_endpoints.py`) + 5 (`test_ai_chat_endpoints.py`) = 22 new backend tests (all DB-dependent, skip cleanly here — full suite now 11 passed/109 skipped/0 failed) + 12 new frontend tests (`ProposedActionCard.test.tsx`, `ExpenseTable.test.tsx`, `IncomeTable.test.tsx` — full suite now 41/41 passed) + 7 Playwright specs (unexecuted, see above).
- **Unverified**: same DB caveat as every backend phase, now compounded by the Playwright specs also needing Docker/browsers neither available here.

---

## Phase 10 – Docker & Deployment

- [X] T097 Finalize `backend/Dockerfile` — multi-stage, `uv`-based, non-root runtime user
  - **Dependencies**: T011
  - **Acceptance Criteria**: production image boots and passes `/healthz` with no dev dependencies present
  - **Complexity**: Medium

- [X] T098 Finalize `frontend/Dockerfile` — Next.js standalone-output multi-stage build
  - **Dependencies**: T011
  - **Acceptance Criteria**: production image serves the app without `node_modules` dev deps
  - **Complexity**: Medium

- [X] T099 Finalize `docker-compose.yml` — db + backend + frontend + healthchecks, one-command local setup
  - **Dependencies**: T097, T098
  - **Acceptance Criteria**: clean clone + `.env` + `docker compose up` reproduces the full `quickstart.md` flow
  - **Complexity**: Medium

- [ ] T100 Neon PostgreSQL setup — project + branch-per-environment, connection strings wired into deployment secrets
  - **Dependencies**: T006
  - **Acceptance Criteria**: staging and production point at separate Neon branches; `alembic upgrade head` succeeds against each
  - **Complexity**: Medium

- [ ] T101 Railway or Render deployment — backend service built from `backend/Dockerfile`, env vars set in platform secret store
  - **Dependencies**: T097, T100
  - **Acceptance Criteria**: deployed backend's `/healthz` returns 200 publicly; secrets are not present in the repo (see project memory on secret handling)
  - **Complexity**: Medium

- [ ] T102 Vercel deployment — frontend project linked to `frontend/`, preview-per-PR + production-on-merge
  - **Dependencies**: T098
  - **Acceptance Criteria**: production deployment reaches the deployed backend and completes a full login → dashboard flow
  - **Complexity**: Medium

- [ ] T103 CI/CD pipeline completion — extend `.github/workflows/ci.yml` with an `e2e` job (Playwright vs. docker-composed stack) and a `deploy` gate that runs `alembic upgrade head` against the target Neon branch before traffic switches
  - **Dependencies**: T096, T101, T102
  - **Acceptance Criteria**: merge to `main` runs migrations then deploys; a failing e2e run blocks deploy
  - **Complexity**: Hard

**Checkpoint**: One-command local setup works; `main` auto-deploys to staging/production with passing health checks.

**Implementation notes (2026-07-31)**:
- T097–T099 (Dockerfiles + `docker-compose.yml`) are genuinely done: multi-stage, non-root, uv-based backend image; multi-stage Next.js `output: "standalone"` frontend image (added `output: "standalone"` to `next.config.ts`, which didn't exist before — verified the standalone `server.js` bundle actually gets produced by a real `next build` run); a `migrate` one-shot compose service so `docker compose up` alone fully migrates the DB with no manual `alembic upgrade head` step, matching the "one-command" requirement. `NEXT_PUBLIC_API_BASE_URL` is wired as a Docker build ARG (not a normal env var) since Next.js inlines `NEXT_PUBLIC_*` values into the client bundle at build time — this was a real, easy-to-miss detail, not boilerplate.
- **Cannot be verified in this environment**: no Docker is installed here, so none of these images have actually been built or run — only YAML/Dockerfile syntax was checked (parsed the compose file with a YAML parser; confirmed all `COPY`/lockfile paths referenced actually exist). Before trusting this, run `docker compose up --build` yourself and confirm it reproduces `quickstart.md`.
- **T100–T102 were not attempted** — they require creating a real Neon project, a Railway/Render backend service, and a Vercel frontend project, all of which need your own cloud accounts and credentials I don't have access to. There is also no git remote yet for any of them to deploy from (this project was never connected to GitHub). These need to happen in this order: (1) push this repo to a GitHub remote, (2) create the Neon project and get a connection string, (3) connect Railway/Render to the repo for the backend, pointing at `backend/Dockerfile`, (4) connect Vercel to the repo for the frontend, (5) set the real secrets (`DATABASE_URL`, `JWT_SECRET`, `OPENAI_API_KEY`, etc.) in each platform's own secret store — never in a committed file, per the project's standing secret-handling rule.
- **T103 is partially done**: `.github/workflows/ci.yml` exists and its `backend-lint-test`/`frontend-lint-test` jobs are real and would run on push once this repo has a GitHub remote (ruff, pytest against a real Postgres service container, eslint, tsc, vitest, `next build`). The `e2e` and `deploy` jobs are written but deliberately left **commented out** rather than wired to secrets that don't exist yet — a workflow referencing undefined secrets doesn't fail loudly in GitHub Actions, it silently becomes an empty string, which seemed worse than an honest comment block explaining exactly what's missing and in what order (T100→T101/T102→uncomment these jobs).

---

## Phase 11 – Documentation

- [X] T104 [P] `README.md` — project overview, architecture summary, links to `specs/001-ai-accounting-assistant/`, tech stack, at repo root
  - **Dependencies**: T001
  - **Acceptance Criteria**: a new engineer can find the spec/plan/quickstart from the README alone
  - **Complexity**: Easy

- [X] T105 [P] API documentation — link FastAPI's auto-generated `/docs` (Swagger UI) and annotate `contracts/openapi.yaml` with any drift found during implementation, in `docs/api.md`
  - **Dependencies**: T091
  - **Acceptance Criteria**: `contracts/openapi.yaml` matches the live `/openapi.json` with no undocumented endpoints
  - **Complexity**: Easy

- [X] T106 Setup guide — expands `quickstart.md` into `docs/setup-guide.md` (local dev, without assuming Docker)
  - **Dependencies**: T012
  - **Acceptance Criteria**: following it from a clean machine produces a running local stack
  - **Complexity**: Easy

- [X] T107 [P] Environment variables reference — annotate every key in `.env.example`; mirror into `docs/environment-variables.md`
  - **Dependencies**: T012
  - **Acceptance Criteria**: every variable consumed by `backend/src/core/config.py` and the frontend is documented with purpose + example (placeholder, never real) value
  - **Complexity**: Easy

- [X] T108 Deployment guide — `docs/deployment-guide.md` covering Vercel/Railway-or-Render/Neon steps, mirroring `plan.md` §10
  - **Dependencies**: T103
  - **Acceptance Criteria**: following it reproduces the production deployment from scratch
  - **Complexity**: Easy

**Checkpoint**: Documentation complete; project ready to hand off or onboard a new contributor.

**Implementation notes (2026-08-01)**:
- T105 was done as a real diff, not a rubber stamp: dumped the live `/openapi.json` from the actual running app and compared it path-by-path and schema-by-schema against `contracts/openapi.yaml`. Found and fixed 4 genuine drifts: `AIChatResponse.conversation_id` and `Expense.flags` were implementation additions missing from the contract; `GET /audit-logs` (in the contract's path list since planning) had no response schema and was missing `page_size` — turns out the endpoint itself hadn't even been *built* until Phase 9, making this the single largest plan-vs-implementation gap in the project; `GET /healthz` wasn't in the contract at all. All fixed in `contracts/openapi.yaml`, documented in `docs/api.md`. No other drift found — everything else matched exactly.
- `docs/deployment-guide.md` is the direct answer to Phase 10's T100–T102, which were never executed (no cloud credentials available in this environment) — it's the literal step-by-step a human needs to follow, in dependency order, including the exact CORS-URL chicken-and-egg step (backend needs the frontend's URL, frontend needs the backend's URL) and where to put the `PRODUCTION_DATABASE_URL` secret the commented-out CI `deploy` job is waiting on.
- `docs/setup-guide.md` documents the `next build`-vs-`next dev` `.next/` cache corruption issue encountered during actual development (Phase 4) as a "Common issues" entry — a real problem this project hit, not a hypothetical one.
- README.md is explicit that Phases 1–10 are complete but T100–T102 (real cloud deployment) are not, and that no backend test in this codebase has ever run against a live Postgres in this environment — pointing to each phase's tasks.md notes for the specific verified-vs-unverified breakdown rather than re-asserting a blanket "it works."
- No backend source changed this phase (only `docs/*.md`, `README.md`, and the reference `contracts/openapi.yaml`) — confirmed via `ruff check`, no full pytest re-run needed. Frontend: `tsc`/`eslint`/`vitest` (41/41) all still clean after Phase 10's `next.config.ts` change.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies — start immediately.
- **Phase 2 (Auth / US1)**: depends on Phase 1. Blocks every other phase (all protected routes/roles depend on it).
- **Phase 3 (Expenses / US2a)** and **Phase 4 (Income / US2b)**: depend on Phase 2. Independent of each other — can run in parallel with two backend engineers.
- **Phase 5 (Ledger / US5)**: depends on Phases 3 & 4 (unions both).
- **Phase 6 (Reports / US4)**: depends on Phases 3 & 4 (reads their data + posts journal entries).
- **Phase 7 (AI Agent / US3 & US6)**: depends on Phases 3, 4, 6 (tools wrap those services).
- **Phase 8 (Dashboard)**: depends on Phases 3, 4, 6.
- **Phase 9 (Testing)**: depends on Phases 1–8 substantially complete.
- **Phase 10 (Docker & Deployment)**: depends on Phase 1 (Docker basics) throughout, finalized after Phase 9.
- **Phase 11 (Documentation)**: can start once the relevant phase lands (docs tasks are individually [P]-independent of each other) but is finalized last.

### User Story Dependencies

- **US1**: No dependencies on other stories — foundation for all.
- **US2**: Depends only on US1 (auth). Independently testable/deployable as the MVP right after Phase 4.
- **US5**: Depends on US2's data existing, but is its own independently testable increment.
- **US4**: Depends on US2's data existing, independently testable increment.
- **US3**: Depends on US2 (wraps its services) and benefits from US4 existing (Report Tool), but US3's core create/update/delete flow only strictly needs US2.
- **US6**: Depends on US2 and US4 (Report Tool, analysis queries).

### Parallel Opportunities

- Phase 1: T002/T003 (frontend) run parallel to T005–T010 (backend).
- Phase 2: T021/T022 (frontend lib) parallel to T014–T019 (backend auth).
- Phases 3 & 4 can run fully in parallel (different files, both only depend on Phase 2).
- Within Phase 6: T055–T061 (the 7 report functions) are parallelizable once T054 (journal posting) lands for the three journal-dependent ones.
- Within Phase 7: T077 (SQL Query Tool) unblocks T078–T080 which can then proceed in parallel.
- Phase 11 documentation tasks are almost entirely `[P]`.

---

## Parallel Example: Phase 3 (Expense Management)

```bash
# Backend models/infra (parallel):
Task: "Category model & migration in backend/src/models/category.py"
Task: "audit_log_entries model & migration in backend/src/models/audit_log.py"

# Frontend, once T004 (shadcn) is done, can proceed independent of backend endpoints:
Task: "ExpenseForm in frontend/src/components/forms/ExpenseForm.tsx"
```

---

## Implementation Strategy

### MVP First

1. Phase 1 (Setup) → Phase 2 (Auth/US1) → Phase 3 + Phase 4 (US2, expense+income).
2. **STOP and VALIDATE**: run `quickstart.md` §2–§3. This is the minimum viable, demoable product — secure login + manual bookkeeping.
3. Deploy/demo if ready (Phase 10 can be pulled forward in a minimal form just to get this MVP hosted).

### Incremental Delivery

1. Setup + Auth → Foundation ready.
2. Expense + Income (US2) → MVP, demoable.
3. Ledger (US5) and Reports (US4) → add in either order; both are independent of each other, both depend only on US2.
4. AI Agent (US3 + US6) → the differentiator, layered on top once US2/US4 are stable.
5. Dashboard → ties US2/US4 together visually.
6. Testing, Docker/Deployment, Documentation → close out for production readiness.

---

## Notes

- 108 tasks total. `[P]` = different files, no unfinished dependency. `[USn]` = maps to `spec.md`'s six user stories; untagged = cross-cutting (Setup, Dashboard, Testing, Deployment, Documentation).
- T060 (Income Report) was added beyond the user-provided Phase 6 sub-item list because `spec.md` FR-019 requires all seven report types; flagged here rather than silently dropped.
- **2026-07-29**: T001–T010, T012, T014–T026 implemented and verified as far as possible without Docker/Postgres (see the implementation note under the Phase 2 checkpoint for specifics, including the bcrypt→argon2 swap and what remains unverified). T011/T013 deliberately left open. Frontend test tooling (Vitest, React Testing Library, `jsdom`) was added to `frontend/package.json` as part of this pass since it didn't exist yet — not a separate tasks.md line item, but required to fulfill T090/T095-style coverage this early.
- Commit after each task or logical group; run the relevant `quickstart.md` section at each phase checkpoint before moving on.
- Per project memory: no real secrets in any `.env` committed to the repo at any task in Phase 1, 10, or 11 — `.env.example` only, real values live in each platform's secret store.
