"""FastAPI application entrypoint for the HurricaneAI Lead Generation platform."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.database import connect_db, disconnect_db

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("app.main")

# Routes that bypass JWT verification
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Track startup state for health checks
_startup_ok = False
_db_ok = False
_db_error = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown resources."""
    global _startup_ok, _db_ok, _db_error

    logger.info("Starting %s (env=%s)", settings.APP_NAME, settings.APP_ENV)

    if settings.db_configured:
        try:
            await connect_db()
            _db_ok = True
            logger.info("Database connected via Prisma.")
        except Exception as exc:
            _db_error = str(exc)
            logger.error("Database connection failed: %s", exc)
    else:
        _db_error = "DATABASE_URL not configured"
        logger.warning("DATABASE_URL not set — DB disabled.")

    _startup_ok = True
    yield

    logger.info("Shutting down %s", settings.APP_NAME)
    if _db_ok:
        await disconnect_db()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "%s %s → %d (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response


app.add_middleware(RequestLoggingMiddleware)


# ---------------------------------------------------------------------------
# Supabase JWT verification middleware
# ---------------------------------------------------------------------------
class SupabaseJWTMiddleware(BaseHTTPMiddleware):
    """Lightweight JWT sanity-check. Skips public paths and non-API routes."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        # Always pass preflight + public paths
        if request.method == "OPTIONS" or any(
            path == p or path.startswith(p) for p in PUBLIC_PATHS
        ):
            return await call_next(request)

        if not path.startswith(settings.API_V1_PREFIX):
            return await call_next(request)

        # If JWT secret not configured, skip verification (degraded mode)
        if not settings.supabase_configured:
            logger.warning("Supabase not configured — JWT verification skipped.")
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or malformed Authorization header"},
            )

        token = auth_header.split(" ", 1)[1].strip()
        try:
            from jose import JWTError, jwt

            jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired authentication token"},
            )

        return await call_next(request)


app.add_middleware(SupabaseJWTMiddleware)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ---------------------------------------------------------------------------
# Health check (rich diagnostics)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Liveness + readiness probe.

    Returns component-level status so CI and monitoring systems can
    distinguish between a healthy full deployment and a degraded one
    (e.g. secrets not yet injected into Render).
    """
    # Check Redis / ARQ worker heartbeat
    worker_status = "unknown"
    worker_error = ""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        # ARQ workers write a heartbeat key — check for it
        keys = await r.keys("arq:health-check:*")
        worker_status = "active" if keys else "no_heartbeat"
        await r.aclose()
    except Exception as exc:
        worker_status = "unavailable"
        worker_error = str(exc)

    components = {
        "database": {
            "status": "ok" if _db_ok else "degraded",
            "configured": settings.db_configured,
            **({"error": _db_error} if _db_error else {}),
        },
        "supabase": {
            "status": "ok" if settings.supabase_configured else "unconfigured",
            "configured": settings.supabase_configured,
        },
        "openai": {
            "status": "ok" if settings.openai_configured else "unconfigured",
            "configured": settings.openai_configured,
        },
        "worker": {
            "status": worker_status,
            **({"error": worker_error} if worker_error else {}),
        },
    }

    # Overall status: "ok" only when all critical components are ready
    overall = (
        "ok"
        if (_db_ok and settings.supabase_configured and settings.openai_configured)
        else "degraded"
    )

    http_status = status.HTTP_200_OK if overall == "ok" else status.HTTP_200_OK  # always 200 for liveness

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall,
            "app": settings.APP_NAME,
            "env": settings.APP_ENV,
            "version": app.version,
            "components": components,
        },
    )
