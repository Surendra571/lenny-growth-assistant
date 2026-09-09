from typing import List, Literal, Optional
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """
    Centralized application configuration loaded from environment variables
    with strict type validation.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General App Settings
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database Persistence
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_assistant"
    DATABASE_SYNC_URL: Optional[str] = "postgresql://postgres:postgres@localhost:5432/lenny_assistant"

    # LLM Provider Configuration
    LLM_PROVIDER: Literal["ollama", "cloud", "mock", "fake"] = "ollama"

    # Local Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0

    # Cloud Provider Settings
    CLOUD_PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    CLOUD_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    OPENAI_API_KEY: Optional[SecretStr] = None
    CLOUD_TIMEOUT_SECONDS: float = 45.0

    # Embedding Provider Configuration
    EMBEDDING_PROVIDER: Literal["local", "openai"] = "local"
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Retrieval & Grounding Guardrails
    GROUNDING_SIMILARITY_THRESHOLD: float = 0.30
    MAX_RETRIEVAL_CHUNKS: int = 6

    # Security & Artifact Policies
    ALLOW_ARTIFACT_SCRIPTS: bool = True
    SANITIZE_ARTIFACT_HTML: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()

