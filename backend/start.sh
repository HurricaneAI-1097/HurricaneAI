#!/bin/sh
# HurricaneAI backend startup script
# Runs Prisma migrations (if DATABASE_URL is set) then starts the API server.

set -e

echo "==> HurricaneAI API starting (env: ${APP_ENV:-dev})"

if [ -n "$DATABASE_URL" ]; then
  echo "==> DATABASE_URL detected — running Prisma migrations..."
  if prisma migrate deploy; then
    echo "==> Migrations applied successfully."
  else
    echo "==> migrate deploy failed — trying db push..."
    prisma db push --accept-data-loss || echo "==> db push also failed — continuing anyway."
  fi
else
  echo "==> WARNING: DATABASE_URL not set — skipping migrations."
fi

echo "==> Starting FastAPI on 0.0.0.0:${PORT:-8000} ..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
