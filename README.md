# FinPilot AI — AI-Powered Accounting & Finance Assistant

A full-stack accounting web app for a Business Owner, an Accountant, and an
Office Administrator to manage income/expenses, browse a unified ledger,
generate financial reports, and — through a LangGraph-orchestrated AI
assistant — do all of the above via natural language, with proactive
duplicate/anomaly/large-expense detection.

## Start here

- **New to this project?** [`docs/setup-guide.md`](docs/setup-guide.md) gets a local stack running.
- **Want to see the design before the code?** [`specs/001-ai-accounting-assistant/`](specs/001-ai-accounting-assistant/) has the full spec-driven development trail:
  - [`spec.md`](specs/001-ai-accounting-assistant/spec.md) — what the product does and why (business-facing, no tech stack)
  - [`plan.md`](specs/001-ai-accounting-assistant/plan.md) — architecture, roadmap, and every implementation decision's rationale
  - [`data-model.md`](specs/001-ai-accounting-assistant/data-model.md) — full database schema
  - [`contracts/openapi.yaml`](specs/001-ai-accounting-assistant/contracts/openapi.yaml) — the REST API contract
  - [`quickstart.md`](specs/001-ai-accounting-assistant/quickstart.md) — step-by-step manual validation of every user story
  - [`tasks.md`](specs/001-ai-accounting-assistant/tasks.md) — the full task breakdown, with an implementation-notes block at every phase checkpoint recording what was actually built, what deviated from plan, and what remains unverified
- **Deploying?** [`docs/deployment-guide.md`](docs/deployment-guide.md).
- **API reference**: run the backend, then open `http://localhost:8000/docs` (Swagger UI) — see [`docs/api.md`](docs/api.md).
- **Environment variables**: [`docs/environment-variables.md`](docs/environment-variables.md), template in [`.env.example`](.env.example).

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query, React Hook Form + Zod, Recharts |
| Backend | Python 3.13, FastAPI, `uv`, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | PostgreSQL (Neon in staging/production) |
| Auth | JWT (access + rotating refresh tokens) |
| AI | LangGraph + a provider-agnostic chat-model adapter (defaults to OpenAI) |
| Deployment | Vercel (frontend), Railway or Render (backend), Neon (database) |
| Containers | Docker, Docker Compose |

Full rationale for every choice above is in
[`specs/001-ai-accounting-assistant/research.md`](specs/001-ai-accounting-assistant/research.md).

## Architecture, in one paragraph

Two independently-deployed projects (`backend/`, `frontend/`) integrated
through the REST contract in `contracts/openapi.yaml`. The backend is
layered: routers stay thin, business rules live in a `services/` layer,
data access is behind `repositories/`. The AI assistant (`backend/src/agent/`)
is a LangGraph state graph whose tools call the **exact same services** the
REST API calls — never a repository or raw query directly — which is what
guarantees the AI path can never bypass the validation and role-permission
rules the manual path enforces (see `research.md` §8 and §11, and
`plan.md`'s "Complexity Tracking" section for why this mattered enough to be
a deliberate architectural decision rather than an assumption).

## Project structure

```text
backend/     FastAPI app — src/{core,models,schemas,repositories,services,api,agent}, tests/, scripts/
frontend/    Next.js app — src/{app,components,hooks,lib}, tests/{unit,e2e}
specs/       Spec-driven development artifacts (spec, plan, tasks, contracts, research)
docs/        Setup, API, environment variables, and deployment guides
docker/      (reserved — Dockerfiles currently live at backend/Dockerfile and frontend/Dockerfile)
```

## Project status

Phases 1–10 of `tasks.md` are complete: authentication, expense/income
management, the ledger, all 7 financial reports, the AI accounting agent,
the dashboard, an expanded test suite, and Docker/Compose. Deploying to a
real Neon/Railway-or-Render/Vercel environment (`tasks.md` T100–T102) has
**not** been done — that requires cloud accounts and credentials only the
project owner has; see the deployment guide for the exact steps. No backend
test in this codebase has run against a live Postgres in the environment
this was built in — see each phase's "Implementation notes" in `tasks.md`
for what's verified vs. what's structurally complete but unexecuted.
