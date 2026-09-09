import uuid
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.message import MessageResponse, SourceCitation


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000, description="User question or prompt")
    skill_override: Optional[Literal["qa", "ship30", "artifact", "unsupported"]] = Field(
        default=None,
        description="Optional explicit skill override ('qa', 'ship30', 'artifact', 'unsupported')",
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=1.5,
        description="Inference sampling temperature",
    )

    @field_validator("message")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty or whitespace only.")
        return v.strip()


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    intent: str = Field(description="Classified or overridden skill intent")
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="Grounding transcript citations used in the response",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

