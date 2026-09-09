import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceCitation(BaseModel):
    chunk_id: Optional[uuid.UUID] = None
    episode_title: str = Field(description="Title of the podcast episode")
    guest_name: str = Field(description="Guest speaker name")
    timestamp: Optional[str] = Field(default=None, description="Timestamp segment if available")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score from hybrid RAG")
    snippet: str = Field(description="Exact excerpt from transcript")


class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"] = Field(default="user", description="Author role")
    content: str = Field(min_length=1, max_length=20000, description="User message text")
    skill_override: Optional[str] = Field(default=None, description="Optional explicit skill selection: 'qa', 'ship30', 'artifact'")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty or whitespace only.")
        return v.strip()


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    tool_calls: Optional[Dict[str, Any]] = None
    sources: List[SourceCitation] = []
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict, validation_alias="message_metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
