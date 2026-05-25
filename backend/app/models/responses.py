from pydantic import BaseModel
from typing import Any, Generic, TypeVar, Optional

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard wrapper for all API responses."""
    success: bool
    message: str
    data: Optional[T] = None


class ErrorDetail(BaseModel):
    """Structured error detail."""
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response shape."""
    success: bool = False
    error: ErrorDetail