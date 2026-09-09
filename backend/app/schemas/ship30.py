import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.message import MessageResponse, SourceCitation


class Ship30Request(BaseModel):
    topic: Optional[str] = Field(
        default=None,
        max_length=20000,
        description="Core topic, question, or context to turn into a Ship 30 for 30 essay",
    )
    audience: Optional[str] = Field(
        default="Product managers, growth leaders, and startup founders",
        description="Target readership persona",
    )
    angle: Optional[str] = Field(
        default="Counterintuitive lessons, practical frameworks, and real-world podcast case studies",
        description="Editorial angle or emphasis",
    )
    tone: Optional[str] = Field(
        default="Authoritative, sharp, actionable, and engaging",
        description="Tone of voice",
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=1.5,
        description="Inference temperature",
    )


class Ship30Response(BaseModel):
    session_id: uuid.UUID
    title: str = Field(description="Headline / Title of the Ship 30 essay")
    content: str = Field(description="Full markdown content of the essay (~1,250 words)")
    word_count: int = Field(description="Total word count of the generated article")
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="Grounded transcript citations supporting the claims in the essay",
    )
    user_message: Optional[MessageResponse] = None
    assistant_message: Optional[MessageResponse] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

