# HurricaneAI Backend — Deployment Guide

The frontend is live at https://hurricaneai.vercel.app. This guide wires up
the FastAPI backend + ARQ worker + Redis + Supabase Postgres so the app
becomes fully functional.

## Architecture recap

```
Vercel (Next.js)  ──HTTPS──▶  Render/Railway (FastAPI web)  ──▶  Supabase Postgres
                                          │
                                          ▼
                              Render/Railway (ARQ worker)
                                          │
                                          ▼
                              Redis (Render managed / Upstash)
```

## Step 1 — Provision Supabase

1. Create a project at https://supabase.com/dashboard.
2. From **Project Settings → Database → Connection string → URI** copy the
   pooled connection string (port 6543). This is your `DATABASE_URL`.
3. From **Project Settings → API** copy:
   - `Project URL`               → `SUPABASE_URL`
   - `service_role` secret       → `SUPABASE_KEY`   (backend only, never ship to browser)
   - `anon public` key           → `NEXT_PUBLIC_SUPABASE_ANON_KEY` (for Vercel)
4. From **Project Settings → API → JWT Settings** copy the `JWT Secret`
   → `SUPABASE_JWT_SECRET`.

## Step 2 — Get an OpenAI API key

- https://platform.openai.com/api-keys  → `OPENAI_API_KEY`
- Recommended starter model: `gpt-4o-mini` (already the default).

## Step 3 — Deploy the backend

### Option A: Render (blueprint, recommended)

1. Push this repo to GitHub (or GitLab/Bitbucket).
2. In Render, click **New + → Blueprint** and select the repo.
3. Render reads `backend/render.yaml` and creates three services:
   - `hurricaneai-api`     — FastAPI web service
   - `hurricaneai-worker`  — ARQ background worker
   - `hurricaneai-redis`   — managed Redis (wired to both above)
4. In the Render dashboard, open each of `hurricaneai-api` and
   `hurricaneai-worker` and set these **secret** env vars (blueprint marks
   them `sync: false` so you must enter them manually):
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_JWT_SECRET`
   - `OPENAI_API_KEY`
5. Trigger a manual deploy on `hurricaneai-api`. Wait for the health check
   at `/health` to go green.
6. Copy the public URL (something like `https://hurricaneai-api.onrender.com`)
   — this is your `NEXT_PUBLIC_API_URL` (append `/api/v1`).

### Option B: Railway

1. In Railway, **New Project → Deploy from GitHub repo** → point at this repo,
   root directory `backend/`.
2. Railway detects `railway.json` and builds from the Dockerfile.
3. Add a **Redis** plugin from the Railway marketplace to the project.
4. Add a second service in the same project (Deploy → same repo, root
   `backend/`) and set its start command to
   `arq app.workers.tasks.WorkerSettings` (this is your worker).
5. On both services, set these env vars (Railway → Variables tab):
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_JWT_SECRET`
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL=gpt-4o-mini`
   - `REDIS_URL` — use Railway's `${{Redis.REDIS_URL}}` reference
   - `CORS_ORIGINS=https://hurricaneai.vercel.app,http://localhost:3000`
6. Deploy. The web service's public domain becomes your `NEXT_PUBLIC_API_URL`
   (append `/api/v1`).

## Step 4 — Run Prisma migrations

The Prisma schema is at `backend/prisma/schema.prisma`. First deploy needs
tables created in Supabase. Two options:

- **From your laptop** (one-off):
  ```bash
  cd backend
  export DATABASE_URL="<your supabase pooled URI>"
  pip install prisma
  prisma db push
  ```
- **From the platform shell** (Render → Shell tab, or `railway run`):
  ```bash
  prisma db push
  ```

For future changes, use `prisma migrate deploy` with a proper migrations
folder. `railway.json` already runs `prisma migrate deploy || prisma db push`
on every start; on Render, add a **pre-deploy command** in the dashboard.

## Step 5 — Point Vercel at the live backend

In the Vercel dashboard for the `hurricaneai` project → **Settings → Environment
Variables**, replace the placeholders with real values for **Production**:

| Variable                          | Value                                                     |
|-----------------------------------|-----------------------------------------------------------|
| `NEXT_PUBLIC_SUPABASE_URL`        | your Supabase project URL                                 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`   | your Supabase `anon public` key                           |
| `NEXT_PUBLIC_API_URL`             | `https://<your-backend-host>/api/v1`                      |

Then **Redeployments → Redeploy** the latest production build so Next.js
picks up the new envs at build time (they are inlined into the browser
bundle because they start with `NEXT_PUBLIC_`).

## Step 6 — Smoke test

```bash
# Backend health
curl https://<your-backend-host>/health
# Expected: {"status":"ok","app":"AI Lead Generation API",...}

# Frontend loads
open https://hurricaneai.vercel.app

# Try to sign up. The Supabase magic-link email should arrive within a minute.
# After clicking, you should land on /dashboard with the overview KPIs
# (all zeros initially — populate by creating a campaign or importing leads).
```

## Cost summary (starter tiers)

| Component                    | Provider           | Monthly cost |
|------------------------------|--------------------|--------------|
| Frontend hosting             | Vercel Hobby       | $0           |
| Backend web + worker         | Render Starter x2  | ~$14         |
| Redis                        | Render Starter     | ~$10         |
| Postgres                     | Supabase Free      | $0 (up to 500 MB) |
| OpenAI usage (`gpt-4o-mini`) | OpenAI             | pay-per-token |

Railway alternative: ~$5–$20/mo total on their usage-based pricing.

## Troubleshooting

- **Frontend loads but every API call 401s** → `SUPABASE_JWT_SECRET` on the
  backend does not match the Supabase project the frontend is using.
- **Backend 502 / cold start times out** → free/starter web dynos on Render
  sleep. Add a keep-alive ping or upgrade to Standard.
- **Worker not picking up jobs** → check that both API and worker have the
  same `REDIS_URL` and that they can reach the Redis instance.
- **CORS errors in browser console** → add the Vercel domain to
  `CORS_ORIGINS` on the backend (comma-separated).
