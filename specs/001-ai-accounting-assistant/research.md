# Phase 0 Research: FinPilot AI – AI-Powered Accounting & Finance Assistant

All technology choices below were specified by the user as hard requirements; this document records the rationale and alternatives considered so the decisions are traceable, plus resolves the implementation-pattern questions the spec left open (marked NEEDS CLARIFICATION in early drafts of Technical Context).

## 1. Backend framework

- **Decision**: FastAPI (Python 3.13), served by Uvicorn/Gunicorn workers.
- **Rationale**: Native Pydantic v2 integration (required), first-class async support for I/O-bound AI calls, automatic OpenAPI schema generation which doubles as the contract artifact for this plan, dependency-injection system that cleanly wires DB sessions/current-user/services.
- **Alternatives considered**: Django REST Framework (heavier, sync-first, weaker native Pydantic v2 fit); Flask + extensions (no built-in async/DI/OpenAPI, more assembly required).

## 2. Package & environment management

- **Decision**: `uv` for dependency resolution, virtualenvs, and running scripts (`uv run`, `uv sync`).
- **Rationale**: Required by user; also the fastest resolver available, single lockfile (`uv.lock`), replaces pip+venv+pip-tools in one tool.
- **Alternatives considered**: Poetry (slower resolver, separate lock format); plain pip + requirements.txt (no lockfile reproducibility).

## 3. ORM & migrations

- **Decision**: SQLAlchemy 2.0 (async engine, `asyncpg` driver) + Alembic for schema migrations.
- **Rationale**: Required by user; SQLAlchemy 2.0's typed declarative models pair well with Pydantic v2 schemas; Alembic is the de facto migration tool for SQLAlchemy and supports autogeneration from model diffs.
- **Alternatives considered**: Tortoise ORM (smaller ecosystem, weaker migration tooling); raw SQL/asyncpg (loses type safety and migration tracking).

## 4. Validation layer

- **Decision**: Pydantic v2 for all request/response schemas, with validators for amount > 0, date bounds, and category existence delegated to the service layer (DB lookups can't happen in a pure Pydantic validator without a session).
- **Rationale**: Required by user; Pydantic v2's Rust core gives a meaningful performance improvement over v1 for high-frequency AI tool-call payloads.
- **Alternatives considered**: Marshmallow (no native FastAPI integration).

## 5. Database & hosting

- **Decision**: PostgreSQL, hosted on Neon for staging/production; local development uses a Dockerized PostgreSQL instance via docker-compose for parity.
- **Rationale**: Required by user; Neon's branch-per-environment model is well suited to preview deployments alongside Vercel preview URLs.
- **Alternatives considered**: Supabase Postgres (also viable, but Neon was the explicit requirement); SQLite for local dev (rejected — would create behavioral drift from production Postgres, especially around `NUMERIC` precision and JSONB columns used by audit logs).

## 6. Authentication

- **Decision**: JWT access tokens (short-lived, ~15 min) + rotating refresh tokens (long-lived, stored hashed in a `refresh_tokens` table, revocable), password hashing via `passlib[bcrypt]` (or `argon2` — final choice made at implementation time based on `uv` package availability).
- **Rationale**: Required by user (JWT); stateless access tokens fit a separately-deployed frontend (Vercel) and backend (Railway/Render) with no shared session store; refresh-token rotation + a revocation table balances statelessness with the ability to force-logout a compromised account, which the audit-heavy nature of financial data makes worth the extra table.
- **Alternatives considered**: Server-side session cookies (would require sticky sessions or a shared session store across backend instances, adding infra complexity for no benefit given the SPA/API split); long-lived single JWT with no refresh (rejected — no way to revoke a stolen token before natural expiry).

## 7. AI orchestration

- **Decision**: LangGraph for the agent graph, with a provider-agnostic chat-model adapter (LangChain's `init_chat_model`-style interface) defaulting to an OpenAI GPT-5-class model, selected via an environment variable (`AI_PROVIDER`, `AI_MODEL`) rather than hard-coded SDK calls.
- **Rationale**: Required by user (LangGraph, configurable provider). LangGraph's explicit state graph and support for interrupt/human-in-the-loop steps is what makes FR-027 (mandatory confirmation before any AI write) implementable as a first-class graph node rather than an ad-hoc check bolted onto a chat loop.
- **Alternatives considered**: A bare function-calling loop against the OpenAI SDK directly (simplest, but re-implements interrupt/confirmation/memory handling that LangGraph already provides, and hard-codes the provider); CrewAI/AutoGen (multi-agent frameworks aimed at a different problem shape than a single tool-using accounting assistant).

## 8. AI tool boundary (how the agent touches data)

- **Decision**: The LangGraph agent never issues SQL or talks to SQLAlchemy directly. It calls the same **service-layer functions** that the REST API controllers call (create_expense, update_income, generate_report, etc.), wrapped as LangGraph tools. A dedicated `AuditTool` and `FinancialAnalysisTool` wrap read-only aggregation queries.
- **Rationale**: This is the only way to satisfy FR-034 ("validate...regardless of whether it originates from manual entry or the AI assistant") and FR-003 (identical role permissions on both paths) without duplicating business logic in two places.
- **Alternatives considered**: A separate "AI data-access layer" with its own validation (rejected — guarantees the two paths drift out of sync over time); giving the agent a raw read/write SQL tool (rejected — impossible to guarantee permission/validation enforcement or produce reliable audit trail entries).

## 9. Frontend framework & UI

- **Decision**: Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui components; Recharts (via shadcn's chart primitives) for dashboard/report visualizations.
- **Rationale**: Required by user. App Router's server components suit data-heavy pages (dashboard, reports, ledger) that can fetch on the server and stream, while the AI chat interface and forms run as client components. shadcn/ui ships accessible table/dialog/form primitives that fit a finance app's density needs.
- **Alternatives considered**: Pages Router (older pattern, no server components); a component library with baked-in styling like MUI (conflicts with the explicit shadcn/ui requirement and is harder to theme with Tailwind).

## 10. Frontend state & data fetching

- **Decision**: TanStack Query for server-state caching/mutations, React Hook Form + Zod for form state/validation (Zod schemas mirrored from the backend Pydantic schemas), a small client-side store (React context or Zustand) only for cross-cutting UI state like the current AI chat session — not for server data.
- **Rationale**: TanStack Query's cache invalidation model matches the CRUD-heavy expense/income/ledger screens; React Hook Form + Zod gives client-side validation that mirrors server-side Pydantic rules (amount > 0, required fields) for immediate feedback before a round trip.
- **Alternatives considered**: Redux Toolkit (more boilerplate for what is mostly server-cache state); SWR (comparable to TanStack Query, but TanStack's mutation API is a better fit for the confirm/reject AI-action flow).

## 11. Backend architecture pattern

- **Decision**: Layered architecture — `api` (FastAPI routers, thin) → `services` (business rules, permission checks, audit logging, orchestrates repositories + commits the unit of work) → `repositories` (SQLAlchemy queries per entity) → `models`. AI tools call `services`, never `repositories` directly.
- **Rationale**: Repository pattern isolates SQLAlchemy specifics so services/tests can mock persistence; the service layer is the single place FR-034/FR-003 rules are enforced, shared by both the REST routers and the AI tools.
- **Alternatives considered**: Fat-model ActiveRecord style (rejected — harder to unit test business rules in isolation, harder to share logic between REST and AI entry points); CQRS with separate write/read models (rejected as unnecessary complexity for this scale — flagged as a possible future evolution, not needed for v1).

## 12. Testing strategy

- **Decision**:
  - Backend unit tests: `pytest` against services/repositories with a transactional test DB (Dockerized Postgres, rolled back per test).
  - Backend API/contract tests: `pytest` + `httpx.AsyncClient` against the FastAPI app, validated against the OpenAPI contract in `contracts/`.
  - AI workflow tests: the LLM call is abstracted behind the provider adapter (§7), so tests run against a stub/fake model that returns deterministic tool-call sequences for a curated set of the example commands from the spec (golden-transcript tests), plus a small number of live-model smoke tests gated behind an opt-in CI flag (real API cost).
  - Frontend unit/component tests: Vitest + React Testing Library.
  - Frontend end-to-end tests: Playwright, covering each user story's "Independent Test" from the spec.
- **Rationale**: Matches the six user stories' independent-test descriptions directly to test suites; keeps the expensive/non-deterministic live-LLM tests small and opt-in while still getting strong coverage of the agent's tool-selection logic via stubbing.
- **Alternatives considered**: Testing only against a live LLM (rejected — slow, costly, flaky/non-deterministic for CI gating).

## 13. Containerization & deployment

- **Decision**: Separate multi-stage Dockerfiles for `backend/` and `frontend/`, orchestrated locally via `docker-compose.yml` (backend, frontend, Postgres, one-command `docker compose up`). Production: frontend on Vercel (native Next.js support), backend on Railway or Render (container deploy from the same Dockerfile used locally), database on Neon.
- **Rationale**: Required by user; using the same backend Dockerfile for both local compose and the hosted platform avoids "works in Docker, breaks in prod" drift.
- **Alternatives considered**: Deploying the backend to Vercel as serverless functions (rejected — poor fit for a long-lived DB-connection-pooling FastAPI app and for LangGraph's potential streaming/long-running steps).

## Open items carried into planning (not blocking)

- Final choice between `bcrypt` and `argon2` for password hashing will be pinned when `uv add` runs against current package availability; both satisfy FR (secure hashing) equally.
- Final choice of OpenAI GPT-5-class model name will be an environment variable, not hard-coded, so it can track model availability at implementation time.
