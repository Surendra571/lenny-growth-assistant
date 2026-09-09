from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Overall service status")
    service: str = Field(default="lenny-growth-assistant", description="Service identifier")
    version: str = Field(default="1.0.0", description="API version")
    environment: str = Field(description="Runtime environment (development, production, test)")
    llm_provider: str = Field(description="Active LLM provider (ollama or cloud)")
    database_connected: bool = Field(description="PostgreSQL connectivity flag")

