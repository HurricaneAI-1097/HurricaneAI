#!/bin/sh
# HurricaneAI backend startup script
# Runs Prisma migrations then starts the API server

set -e

echo "==> Running Prisma migrations..."
prisma migrate deploy || prisma db push --accept-data-loss

echo "==> Starting FastAPI on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
