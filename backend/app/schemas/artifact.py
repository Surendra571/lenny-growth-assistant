import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ArtifactCreate(BaseModel):
    session_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None
    title: str = Field(min_length=1, max_length=255)
    artifact_type: Literal["markdown", "html", "svg"] = Field(description="Format of the artifact")
    content: str = Field(description="Raw markdown, HTML, or SVG payload")
    version: int = Field(default=1, ge=1)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    message_id: Optional[uuid.UUID] = None
    title: str
    artifact_type: str
    content: str
    version: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="artifact_metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
