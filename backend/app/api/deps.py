"""Shared FastAPI dependencies: authentication, authorization, and DB access."""

import logging
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prisma import Prisma

from app.config import get_settings
from app.database import get_client

logger = logging.getLogger("app.api.deps")
settings = get_settings()

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[Prisma, None]:
    """Yield the shared Prisma client for use inside route handlers."""
    client = get_client()
    if not client.is_connected():
        await client.connect()
    yield client


def _decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """Decode and verify a Supabase-issued JWT.

    Supabase signs access tokens with the project's JWT secret using HS256.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True},
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Prisma = Depends(get_db),
) -> Dict[str, Any]:
    """Extract and verify the Bearer token, returning the authenticated user.

    The Supabase JWT `sub` claim holds the Supabase auth user id; we look the
    user up (or lazily create a local record) in our own `User` table so
    downstream services can rely on relational integrity.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = _decode_supabase_jwt(token)

    supabase_user_id: Optional[str] = payload.get("sub")
    email: Optional[str] = payload.get("email")

    if not supabase_user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing required claims",
        )

    user = await db.user.find_unique(where={"email": email})
    if user is None:
        # Lazily provision a local user record on first authenticated request.
        user = await db.user.create(
            data={
                "id": supabase_user_id,
                "email": email,
                "name": payload.get("user_metadata", {}).get("full_name"),
            }
        )

    request.state.user_id = user.id
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
    }


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Dependency that restricts access to ADMIN-role users."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user
