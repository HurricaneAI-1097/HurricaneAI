"""FastAPI application entrypoint for the AI Lead Generation platform."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
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

# Routes that do not require a verified Supabase session.
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown resources (database connection pool)."""
    logger.info("Starting up %s (env=%s)", settings.APP_NAME, settings.APP_ENV)
    await connect_db()
    yield
    logger.info("Shutting down %s", settings.APP_NAME)
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
    """Logs method, path, status code, and duration for every request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "%s %s -> %d (%.2fms)",
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
    """Performs a lightweight JWT sanity-check ahead of route-level auth.

    This middleware short-circuits requests with clearly malformed or
    expired tokens before they reach route handlers. Fine-grained user
    resolution and role checks still happen in `app.api.deps.get_current_user`,
    which performs the authoritative verification and DB lookup.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        if request.method == "OPTIONS" or any(
            path == p or path.startswith(p) for p in PUBLIC_PATHS
        ):
            return await call_next(request)

        if not path.startswith(settings.API_V1_PREFIX):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or malformed Authorization header"},
            )

        token = auth_header.split(" ", 1)[1].strip()
        try:
            jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
        except JWTError:
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
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Simple liveness/readiness probe."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "version": app.version,
    }
