# Environment Variables Reference

Template: [`.env.example`](../.env.example) at the repo root — copy it to
`.env` and fill in real values. **Never commit `.env` with real secrets**;
`.env`/`.env.*` are gitignored everywhere except `.env.example` itself.

Both `backend/` (via `pydantic-settings`, `src/core/config.py`) and
`frontend/` (via Next.js's built-in env loading) read from a `.env` at the
repo root during local development; `docker-compose.yml` passes the same
file to the backend/migrate containers via `env_file`, and the frontend's
`NEXT_PUBLIC_API_BASE_URL` is instead passed as a Docker **build arg** (see
the note on that variable below — it behaves differently from every other
one here).

## Backend

| Variable | Purpose | Example (placeholder) |
|---|---|---|
| `ENVIRONMENT` | Free-text label (`local`/`staging`/`production`); not currently branched on in code, informational | `local` |
| `DATABASE_URL` | Async SQLAlchemy connection string (`postgresql+asyncpg://...`) | `postgresql+asyncpg://finpilot:finpilot@localhost:5432/finpilot` |
| `JWT_SECRET` | HMAC signing key for access/refresh tokens. **Must** be long and random in staging/production — the default is a deliberately weak placeholder that triggers a `PyJWT` warning if used as-is | `replace-with-a-long-random-value` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (rotated on each use — see `AuthService`) | `30` |
| `CORS_ORIGINS` | JSON array of allowed frontend origins | `["http://localhost:3000"]` |
| `AI_PROVIDER` | Passed to LangChain's `init_chat_model(model_provider=...)` — swapping this is the entire mechanism for changing AI providers (`src/agent/provider.py`) | `openai` |
| `AI_MODEL` | Model name for the chosen provider | `gpt-5` |
| `OPENAI_API_KEY` | Required only if `AI_PROVIDER=openai`. Missing/invalid → the AI assistant reports itself unavailable (503) rather than crashing (FR-033) — every non-AI feature is unaffected | `replace-with-your-own-key` |

## Frontend

| Variable | Purpose | Example (placeholder) |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL the **browser** uses to reach the backend's `/api/v1` prefix. `NEXT_PUBLIC_*` vars are inlined into the client JS bundle at **build time**, not read at runtime — in Docker this must be passed as a `build.args` entry (already wired in `docker-compose.yml`), not a normal container env var, or it silently falls back to its default | `http://localhost:8000/api/v1` |

## Deployment-only (not in `.env.example` — set directly in each platform's secret store)

These only exist once you've done `tasks.md` T100–T102; see
[`deployment-guide.md`](deployment-guide.md) for where each one is set.

| Variable | Where | Purpose |
|---|---|---|
| Production `DATABASE_URL` | Railway/Render backend service secrets | Points at the Neon **production** branch, distinct from the dev `.env` value |
| Staging `DATABASE_URL` | Railway/Render staging service secrets (if you run a staging environment) | Points at a separate Neon branch |
| `PRODUCTION_DATABASE_URL` | GitHub Actions repo secret | Used by the (currently commented-out) `deploy` job in `.github/workflows/ci.yml` to run `alembic upgrade head` before traffic switches |
| Production `JWT_SECRET`, `OPENAI_API_KEY`, `CORS_ORIGINS` | Railway/Render backend service secrets | Same purpose as local, production values — **must differ from any value ever committed or used locally** |
| Vercel project env vars | Vercel dashboard | `NEXT_PUBLIC_API_BASE_URL` pointing at the deployed backend's public URL |
