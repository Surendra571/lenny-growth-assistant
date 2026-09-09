from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field
from app.agent.providers import get_active_provider_info, get_llm_provider
from app.core.config import settings
from app.core.logging import logger
from app.db.session import check_db_health

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service liveness indicator")
    service: str = Field(default="lenny-growth-assistant")
    version: str = Field(default="1.0.0")
    environment: str
    llm_provider: str = Field(default="ollama", description="Configured LLM provider")
    active_model: str = Field(default="llama3.1:8b", description="Configured active model")


class ReadinessResponse(BaseModel):
    status: str = Field(description="Service readiness indicator ('ready' or 'not_ready')")
    database: str = Field(description="Database connectivity state ('connected' or 'disconnected')")
    llm_provider: str = Field(description="Configured LLM provider")
    active_model: str = Field(description="Configured active model")
    llm_status: str = Field(default="connected", description="LLM provider reachability ('connected' or 'unavailable')")


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health():
    """
    Liveness probe verifying that the application process is running and responding.
    """
    provider_info = get_active_provider_info()
    return HealthResponse(
        status="ok",
        service="lenny-growth-assistant",
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        llm_provider=provider_info["provider"],
        active_model=provider_info["model"],
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(response: Response):
    """
    Readiness probe verifying that core dependencies (PostgreSQL and LLM provider) are reachable.
    Returns 200 when ready, 503 when critical dependencies (database) are unreachable.
    """
    db_connected = await check_db_health()
    provider_info = get_active_provider_info()

    provider_healthy = False
    try:
        provider = get_llm_provider()
        provider_healthy = await provider.check_health()
    except Exception as e:
        logger.warning(f"Provider health check failed: {e}")
        provider_healthy = False

    llm_status_str = "connected" if provider_healthy else "unavailable"

    if not db_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="not_ready",
            database="disconnected",
            llm_provider=provider_info["provider"],
            active_model=provider_info["model"],
            llm_status=llm_status_str,
        )

    return ReadinessResponse(
        status="ready",
        database="connected",
        llm_provider=provider_info["provider"],
        active_model=provider_info["model"],
        llm_status=llm_status_str,
    )
