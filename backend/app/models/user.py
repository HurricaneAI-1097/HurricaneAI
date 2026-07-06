"""User domain enums (mirrors `User` model in schema.prisma)."""

from enum import Enum


class UserRole(str, Enum):
    """Application-level authorization role."""

    USER = "USER"
    ADMIN = "ADMIN"
