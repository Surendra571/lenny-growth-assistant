import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255, description="Optional custom session title")
    user_id: Optional[uuid.UUID] = Field(default=None, description="Optional associated user UUID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="session_metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SessionDetailResponse(SessionResponse):
    messages: List[Any] = []
    artifacts: List[Any] = []
