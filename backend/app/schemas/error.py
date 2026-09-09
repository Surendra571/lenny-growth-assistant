from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    request_id: Optional[str] = Field(default=None, description="Request tracking identifier")
    details: Optional[Any] = Field(default=None, description="Supplementary diagnostic data")


class ErrorResponse(BaseModel):
    error: ErrorDetail

