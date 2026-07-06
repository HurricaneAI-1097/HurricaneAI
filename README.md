# AI Lead Generation Platform

An AI-powered lead generation application that discovers, enriches, scores,
and helps convert B2B leads using LangChain + OpenAI, with a FastAPI backend
and a Next.js 14 dashboard.

## Overview

AI Lead Generation lets sales and growth teams:

- Define campaigns in plain English (an "ideal customer profile" brief) and
  have AI generate targeted buyer personas.
- Import or manually add leads, which are automatically enriched with
  firmographic data and an AI-generated fit score.
- Track leads through a pipeline (`NEW → CONTACTED → QUALIFIED → CONVERTED`)
  with campaign-level conversion analytics.
- Generate personalized outreach email drafts per lead/campaign context.

## Architecture

```
┌────────────────┐        HTTPS/JSON        ┌───────────────────┐
│  Next.js 14     │ ───────────────────────▶ │   FastAPI backend  │
│  (App Router)   │ ◀─────────────────────── │   (Python 3.11+)   │
│  Tailwind CSS   │                           └─────────┬─────────┘
│  Supabase Auth  │                                     │
└────────┬────────┘                                     │
         │ Supabase session cookie                      │ Prisma ORM
         ▼                                               ▼
┌─────────────────┐                             ┌───────────────────┐
│  Supabase Auth   │                             │  PostgreSQL (via  │
│  (JWT issuer)    │                             │  Supabase)         │
└──────────────────┘                             └───────────────────┘
                                                            ▲
                                                            │
                                          ┌─────────────────┴────────────────┐
                                          │   ARQ workers (Redis-backed)      │
                                          │   - enrich_lead_task              │
                                          │   - score_lead_task               │
                                          │   - process_campaign_task         │
                                          │   Uses LangChain + OpenAI chains  │
                                          └────────────────────────────────────┘
```

**Frontend** — Next.js 14 (App Router) + TypeScript + Tailwind CSS. Auth
session state is managed via Supabase SSR helpers and enforced by
`middleware.ts` on all `/dashboard/*` routes.

**Backend** — FastAPI exposes a versioned REST API (`/api/v1`) for leads,
campaigns, enrichment, and analytics. A custom middleware verifies Supabase-
issued JWTs on every request; `app/api/deps.py` performs the authoritative
per-route user resolution and role checks.

**Database** — PostgreSQL hosted via Supabase, accessed through
`prisma-client-py` using the schema defined in `backend/prisma/schema.prisma`.

**AI** — LangChain chains (`backend/app/ai/chains.py`) wrap `ChatOpenAI` with
structured JSON output parsing for lead scoring, enrichment, campaign persona
generation, and personalized outreach email drafting.

**Queue** — Redis + ARQ run background jobs (`backend/app/workers/tasks.py`)
for enrichment, scoring, and AI-driven campaign lead generation, so these
LLM calls never block API request/response cycles.

## Prerequisites

- Node.js 18.17+ and npm
- Python 3.11+ and [Poetry](https://python-poetry.org/)
- Docker and Docker Compose (for containerized local development)
- A [Supabase](https://supabase.com) project (Auth + Postgres)
- An [OpenAI](https://platform.openai.com) API key

## Setup Instructions

### 1. Clone and configure environment variables

```bash
cd ai-leadgen-scaffold
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Fill in the Supabase and OpenAI credentials in both `.env` files (see the
[Environment Variables](#environment-variables) table below).

### 2. Start the full stack with Docker Compose

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, the FastAPI backend, the ARQ worker, and the
Next.js frontend. The frontend is available at `http://localhost:3000` and
the API at `http://localhost:8000`.

### 3. Run Prisma migrations

With the `postgres` service running (via Docker Compose or a Supabase
connection string in `DATABASE_URL`):

```bash
cd backend
poetry install
poetry run prisma generate
poetry run prisma migrate dev --name init
```

### 4. Local development without Docker (optional)

**Backend:**

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

**ARQ worker:**

```bash
cd backend
poetry run arq app.workers.tasks.WorkerSettings
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

| Variable               | Description                                              |
| ----------------------- | --------------------------------------------------------- |
| `DATABASE_URL`          | PostgreSQL connection string (Supabase pooled connection) |
| `SUPABASE_URL`          | Supabase project URL                                       |
| `SUPABASE_KEY`          | Supabase service role or anon key                          |
| `SUPABASE_JWT_SECRET`   | Secret used to verify Supabase-issued JWTs                 |
| `OPENAI_API_KEY`        | OpenAI API key for LangChain chains                         |
| `OPENAI_MODEL`          | Chat model name (default `gpt-4o-mini`)                     |
| `REDIS_URL`             | Redis connection string used by ARQ                         |
| `CORS_ORIGINS`          | Comma-separated list of allowed frontend origins             |
| `APP_ENV`               | `dev`, `staging`, or `prod`                                  |
| `DEBUG`                 | Enable verbose logging (`true`/`false`)                     |

### Frontend (`frontend/.env.local`)

| Variable                          | Description                                 |
| ---------------------------------- | -------------------------------------------- |
| `NEXT_PUBLIC_SUPABASE_URL`         | Supabase project URL (public)                |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`    | Supabase anon/public API key                 |
| `NEXT_PUBLIC_API_URL`              | Base URL of the FastAPI backend's `/api/v1`  |

## API Documentation

Once the backend is running, interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Development Workflow

1. **Schema changes**: Update `backend/prisma/schema.prisma`, then run
   `poetry run prisma migrate dev --name <description>` to generate a
   migration and regenerate the Prisma client.
2. **New API endpoints**: Add routes under `backend/app/api/v1/`, register
   them in `backend/app/api/v1/router.py`, and back them with a service in
   `backend/app/services/`.
3. **AI chain changes**: Update prompts in `backend/app/ai/prompts.py` and
   chain wiring in `backend/app/ai/chains.py`. All chains return parsed JSON
   dicts — keep prompts and their JSON schemas in sync.
4. **Background jobs**: Add new task functions to
   `backend/app/workers/tasks.py` and register them in `WorkerSettings.functions`.
5. **Frontend pages**: Add routes under `frontend/app/`. Protected routes
   belong under `frontend/app/dashboard/`, which is guarded by
   `frontend/middleware.ts`.
6. **Testing**: Run backend tests with `poetry run pytest` from `backend/`.
   Run frontend type-checking with `npm run type-check` from `frontend/`.
7. **Linting/formatting**: `poetry run ruff check .` and `poetry run black .`
   for the backend; `npm run lint` for the frontend.
