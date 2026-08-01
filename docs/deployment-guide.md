# Deployment Guide

Mirrors `specs/001-ai-accounting-assistant/plan.md` §10. This is the
step-by-step version of `tasks.md` T100–T102 — none of which have been done
yet as of this writing (no cloud accounts/credentials were available in the
environment this project was built in; see `tasks.md`'s Phase 10 notes).
Follow this in order; each step depends on the one before it.

## 0. Prerequisites

- A GitHub account, with this repository pushed to it (it has no remote
  yet — `git init` and a first push happen before anything below is
  possible)
- A [Neon](https://neon.tech) account (free tier is enough to start)
- A [Railway](https://railway.app) or [Render](https://render.com) account
- A [Vercel](https://vercel.com) account
- Your `OPENAI_API_KEY` (or equivalent for whichever `AI_PROVIDER` you use)

## 1. Push this repo to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
gh repo create <your-org>/finpilot-ai --private --source=. --push
# or create the repo on github.com and:
#   git remote add origin git@github.com:<your-org>/finpilot-ai.git
#   git push -u origin main
```

Double-check nothing in `.env` (only `.env.example`) got committed —
`git status` and `git log --stat` before pushing if in doubt.

## 2. Neon (database)

1. Create a Neon project.
2. Create two branches: `production` and `staging` (Neon's branch-per-environment
   model — mirrors Vercel's preview/production split).
3. Copy each branch's connection string (Neon gives you the
   `postgresql://...` form; prepend `+asyncpg` after `postgresql` to match
   what this backend expects: `postgresql+asyncpg://...`).
4. Don't run migrations yet — that happens once the backend service exists
   (step 3) or via CI (step 5).

## 3. Backend — Railway or Render

Both platforms build directly from `backend/Dockerfile` given a repo
connection; steps are equivalent, Railway's UI is used below as the
concrete example.

1. New service → Deploy from GitHub repo → select this repo, root
   directory `backend/`.
2. It should auto-detect the `Dockerfile`. Confirm the build context is
   `backend/` (not the repo root).
3. Set environment variables (service secrets, **not** committed anywhere):
   `DATABASE_URL` (Neon production branch), `JWT_SECRET` (generate a new
   long random value — do not reuse a local dev value), `AI_PROVIDER`,
   `AI_MODEL`, `OPENAI_API_KEY`, `CORS_ORIGINS` (set to your eventual Vercel
   URL once known, e.g. `["https://finpilot-ai.vercel.app"]`).
4. Expose port `8000`; set the health check path to `/healthz`.
5. Before or right after the first deploy, run migrations against this
   branch once (from your machine, with `DATABASE_URL` temporarily pointed
   at the Neon production branch):
   ```bash
   cd backend
   DATABASE_URL=<neon-production-url> uv run alembic upgrade head
   ```
   Going forward, this step is what the CI `deploy` job (currently
   commented out in `.github/workflows/ci.yml`) automates.
6. Confirm: `curl https://<your-backend-domain>/healthz` returns
   `{"status": "ok"}`.
7. Repeat for a `staging` service pointed at the Neon `staging` branch, if
   you want a staging environment.

## 4. Frontend — Vercel

1. Import the GitHub repo into Vercel; set the project root to `frontend/`.
2. Vercel auto-detects Next.js — no Dockerfile needed here (Vercel doesn't
   use `frontend/Dockerfile`; that's only for the `docker compose` local
   path and any non-Vercel deploy target).
3. Set the environment variable `NEXT_PUBLIC_API_BASE_URL` to your deployed
   backend's public URL + `/api/v1` (e.g.
   `https://finpilot-backend.up.railway.app/api/v1`), for both the
   **Production** and **Preview** environments in Vercel's project settings.
4. Deploy. Every PR gets a preview URL automatically; merges to `main`
   deploy to production automatically — this is Vercel's default behavior,
   no extra config needed.
5. Go back to the backend's `CORS_ORIGINS` env var (step 3.3 above) and set
   it to the real Vercel production URL now that you know it, then redeploy
   the backend.

## 5. Wire up CI/CD fully

`.github/workflows/ci.yml` already has working `backend-lint-test` and
`frontend-lint-test` jobs (run on every push/PR). The `e2e` and `deploy`
jobs are written but commented out because they need:

1. `PRODUCTION_DATABASE_URL` set as a **GitHub repo secret** (Settings →
   Secrets and variables → Actions) — the Neon production branch's
   connection string.
2. Playwright's target URLs (`E2E_BASE_URL` in `playwright.config.ts`, and
   the backend URL the frontend build points at) resolved for the
   `docker compose`-based `e2e` job — or point it at your real staging
   deployment instead, if you'd rather test against that.

Once both exist, uncomment the `e2e` and `deploy` jobs in `ci.yml`. Note
that Vercel and Railway/Render both already deploy on git push natively
once connected (steps 3–4) — the `deploy` job's actual purpose is to run
migrations first and act as a required status check that blocks their
auto-deploy until the e2e suite and migrations both succeed, not to trigger
the deploy itself.

## 6. Verify the full production path

Walk through `specs/001-ai-accounting-assistant/quickstart.md` again, this
time against the real deployed URLs instead of `localhost` — same
acceptance scenarios, real infrastructure.
