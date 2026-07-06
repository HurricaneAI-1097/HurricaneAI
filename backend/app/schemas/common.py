"""Shared/common Pydantic schemas used across multiple routers."""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination query parameters."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response envelope."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def build(
        cls, items: List[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ApiResponse(BaseModel, Generic[T]):
    """Generic single-object success response envelope."""

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response body."""

    success: bool = False
    detail: str
    code: Optional[str] = None
