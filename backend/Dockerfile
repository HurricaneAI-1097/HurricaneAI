# --- Base image -------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies for prisma (openssl) + building wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        openssl \
        libssl-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Python dependencies ---------------------------------------------
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# --- Application code -----------------------------------------------
COPY . .

# Generate the Prisma client (schema only — no DB connection required)
RUN prisma generate

# Default port for the web service (Render/Railway override with $PORT)
ENV PORT=8000
EXPOSE 8000

# Web service default command. Workers override CMD via platform config.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
