# Setup Guide (local development, without Docker)

This is the non-Docker path — running each piece directly on your machine.
If you just want the fastest path to a running stack and don't need to
debug the backend/frontend in isolation, use `docker compose up` instead
(see the repo root README and `docker-compose.yml`); this guide is for when
you want tighter iteration loops on one side of the stack.

## Prerequisites

- **Python 3.13** and [`uv`](https://docs.astral.sh/uv/)
- **Node.js 20+** and npm
- **PostgreSQL 16** reachable from your machine — either installed locally,
  or a free [Neon](https://neon.tech) project (recommended: it's what
  staging/production use too, so there's no behavioral drift to debug later)
- An API key for whichever `AI_PROVIDER` you configure (optional — the app
  runs without one; the AI Assistant page reports itself unavailable and
  every other feature works normally, per FR-033/SC-008)

## 1. Clone and configure

```bash
git clone <this-repo-url>
cd "FinAssist AI"
cp .env.example .env
```

Edit `.env`:
- `DATABASE_URL` — point it at your Postgres (Neon gives you a full
  connection string; for a local install it's typically
  `postgresql+asyncpg://<user>:<password>@localhost:5432/finpilot`)
- `JWT_SECRET` — any long random string for local dev
- `AI_PROVIDER` / `AI_MODEL` / `OPENAI_API_KEY` — optional, see above

See [`environment-variables.md`](environment-variables.md) for every key.

## 2. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m scripts.seed_demo_data     # one user per role
uv run python -m scripts.seed_bulk_ledger   # optional: 65 rows for pagination testing
uv run uvicorn src.main:app --reload --port 8000
```

Confirm it's up: `curl http://localhost:8000/healthz` should return
`{"status": "ok"}`. If it returns `{"status": "unavailable"}` (503), the
backend can't reach `DATABASE_URL` — check that first.

The seed script prints the three demo logins it creates
(`owner@finpilot.demo`, `accountant@finpilot.demo`, `admin@finpilot.demo`,
all with password `DemoPass123!`).

## 3. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` — it redirects to `/login`.

`frontend/.env.local` (or the repo-root `.env`, which Next.js also reads)
needs `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` — already set
in `.env.example`.

## 4. Validate it actually works

Walk through [`../specs/001-ai-accounting-assistant/quickstart.md`](../specs/001-ai-accounting-assistant/quickstart.md)
— it has one section per user story with exact steps and expected results,
covering login/roles, manual bookkeeping, the AI assistant, reports, the
ledger, AI analysis/audit, and the AI-unavailable fallback.

## Running the test suites

```bash
# Backend — needs DATABASE_URL pointed at a real, migrated Postgres;
# DB-dependent tests skip cleanly (not fail) without one.
cd backend
uv run ruff check src/ tests/ scripts/
uv run pytest

# Frontend — no backend/DB needed for these (everything's mocked).
cd frontend
npm run lint
npx tsc --noEmit
npm run test

# Frontend e2e (Playwright) — needs the full stack running (or
# docker-composed) at the URLs in playwright.config.ts, plus:
npx playwright install --with-deps chromium
npm run test:e2e
```

## Common issues

- **`/healthz` returns 503**: `DATABASE_URL` is wrong, or Postgres isn't
  running/reachable. Nothing else will work until this is fixed.
- **Login succeeds but every other page is empty/errors**: check the
  frontend's `NEXT_PUBLIC_API_BASE_URL` matches where the backend is
  actually listening, and check the browser console for CORS errors (the
  backend's `CORS_ORIGINS` setting must include your frontend's origin).
- **AI Assistant always says unavailable**: expected without a real
  `OPENAI_API_KEY` (or other configured provider) — this is FR-033 working
  as intended, not a bug.
- **`next dev` and `next build` fought over `.next/` and now the dev server
  500s on every page**: stop all `node` processes, delete `frontend/.next`,
  and restart `npm run dev`. Don't run `next build` while `next dev` is
  running against the same project — this genuinely happened during
  development (see `tasks.md`'s Phase 4 implementation notes) and corrupts
  Turbopack's dev manifest cache.
