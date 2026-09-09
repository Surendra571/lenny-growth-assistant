from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient, ConnectError, TimeoutException
from app.agent.providers import (
    CloudProvider,
    FakeLLMProvider,
    OllamaProvider,
    get_active_provider_info,
    get_llm_provider,
    set_llm_provider_override,
)
from app.core.config import settings
from app.core.errors import (
    ConfigurationException,
    ModelTimeoutException,
    ModelUnavailableException,
)
from app.main import app


@pytest.fixture(autouse=True)
def reset_provider_override():
    """Ensure provider override is cleared after each test."""
    set_llm_provider_override(None)
    yield
    set_llm_provider_override(None)


def test_provider_factory_resolution_ollama(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    set_llm_provider_override(None)
    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.provider_name == "ollama"
    assert provider.model == settings.OLLAMA_MODEL


def test_provider_factory_resolution_cloud(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "cloud")
    set_llm_provider_override(None)
    provider = get_llm_provider()
    assert isinstance(provider, CloudProvider)
    assert provider.provider_name.startswith("cloud:")


def test_provider_factory_resolution_mock(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    set_llm_provider_override(None)
    provider = get_llm_provider()
    assert isinstance(provider, FakeLLMProvider)


def test_provider_factory_invalid_provider_raises():
    set_llm_provider_override(None)
    with pytest.raises(ConfigurationException) as exc_info:
        get_llm_provider(provider_type="unsupported_provider_xyz")
    assert "Unsupported LLM provider" in str(exc_info.value.message)


def test_active_provider_info_redacts_secrets(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "cloud")
    monkeypatch.setattr(settings, "CLOUD_PROVIDER", "anthropic")
    monkeypatch.setattr(settings, "CLOUD_MODEL", "claude-3-5-sonnet-20241022")
    set_llm_provider_override(None)

    info = get_active_provider_info()
    assert info["provider"] == "cloud:anthropic"
    assert info["model"] == "claude-3-5-sonnet-20241022"
    # Ensure no API keys or tokens are in dictionary keys or values
    assert "api_key" not in info
    assert "key" not in str(info).lower()


@pytest.mark.asyncio
async def test_cloud_provider_missing_anthropic_key(monkeypatch):
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    provider = CloudProvider(provider="anthropic")
    with pytest.raises(ModelUnavailableException) as exc_info:
        async for _ in provider.generate_stream(prompt="Test prompt"):
            pass
    assert "ANTHROPIC_API_KEY is not configured" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_cloud_provider_missing_openai_key(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    provider = CloudProvider(provider="openai")
    with pytest.raises(ModelUnavailableException) as exc_info:
        async for _ in provider.generate_stream(prompt="Test prompt"):
            pass
    assert "OPENAI_API_KEY is not configured" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_cloud_provider_unsupported_subprovider():
    provider = CloudProvider(provider="cohere")
    with pytest.raises(ConfigurationException) as exc_info:
        async for _ in provider.generate_stream(prompt="Test prompt"):
            pass
    assert "Unsupported cloud provider" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_ollama_provider_connection_failure_maps_to_503():
    provider = OllamaProvider(base_url="http://localhost:99999")
    with patch("httpx.AsyncClient.stream") as mock_stream:
        mock_stream.side_effect = ConnectError("Connection refused")
        with pytest.raises(ModelUnavailableException) as exc_info:
            async for _ in provider.generate_stream(prompt="Test prompt"):
                pass
        assert "Cannot connect to Ollama daemon" in str(exc_info.value.message)
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_ollama_provider_timeout_maps_to_504():
    provider = OllamaProvider(base_url="http://localhost:11434")
    with patch("httpx.AsyncClient.stream") as mock_stream:
        mock_stream.side_effect = TimeoutException("Read timed out")
        with pytest.raises(ModelTimeoutException) as exc_info:
            async for _ in provider.generate_stream(prompt="Test prompt"):
                pass
        assert "timed out" in str(exc_info.value.message)
        assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_health_endpoint_reports_active_provider_and_model(monkeypatch, client: AsyncClient):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_MODEL", "llama3.1:8b")
    set_llm_provider_override(None)

    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["llm_provider"] == "ollama"
    assert data["active_model"] == "llama3.1:8b"


@pytest.mark.asyncio
async def test_ready_endpoint_reports_provider_status(client: AsyncClient):
    set_llm_provider_override(FakeLLMProvider(is_healthy=True))
    with patch("app.api.v1.health.check_db_health", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = True
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert data["llm_status"] == "connected"


@pytest.mark.asyncio
async def test_chat_resilience_on_llm_failure_preserves_session(client: AsyncClient):
    # Verify that when an LLM failure occurs, the session is not destroyed and 503 is returned
    failing_provider = FakeLLMProvider(
        should_raise=ModelUnavailableException("Ollama daemon is not reachable.")
    )
    set_llm_provider_override(failing_provider)

    # 1. Create a session
    create_res = await client.post("/api/v1/sessions", json={"title": "Resilience Session"})
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # 2. Attempt chat - should fail cleanly with 503
    chat_res = await client.post(
        f"/api/v1/sessions/{session_id}/chat",
        json={"message": "What is Superhuman's PMF engine?"},
    )
    assert chat_res.status_code == 503
    error_data = chat_res.json()["error"]
    assert error_data["code"] == "MODEL_UNAVAILABLE"
    assert "Ollama daemon is not reachable" in error_data["message"]

    # 3. Session should still exist and be intact
    get_sess_res = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_sess_res.status_code == 200
    assert get_sess_res.json()["title"] == "Resilience Session"
