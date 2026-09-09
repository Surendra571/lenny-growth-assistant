from typing import Dict, Optional
from app.agent.providers.llm_provider import LLMProvider
from app.agent.providers.ollama_provider import OllamaProvider
from app.agent.providers.cloud_provider import CloudProvider
from app.agent.providers.fake_provider import FakeLLMProvider
from app.core.config import settings
from app.core.errors import ConfigurationException

_provider_override: Optional[LLMProvider] = None


def set_llm_provider_override(provider: Optional[LLMProvider]) -> None:
    """
    Override the active LLM provider (useful for testing and dependency injection).
    """
    global _provider_override
    _provider_override = provider


def get_llm_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """
    Factory helper to instantiate the configured LLM provider with validation.
    """
    if _provider_override is not None:
        return _provider_override

    target = (provider_type or settings.LLM_PROVIDER).lower()

    if target in ["mock", "fake", "test"]:
        return FakeLLMProvider()
    elif target == "cloud":
        return CloudProvider()
    elif target == "ollama":
        return OllamaProvider()
    else:
        raise ConfigurationException(
            f"Unsupported LLM provider: '{target}'. Supported options: 'ollama', 'cloud', 'mock'."
        )


def get_active_provider_info() -> Dict[str, str]:
    """
    Safely return metadata about the active provider and model without exposing secrets.
    """
    if _provider_override is not None:
        return {
            "provider": getattr(_provider_override, "provider_name", "custom_override"),
            "model": getattr(_provider_override, "model", "custom_model"),
        }

    provider_type = settings.LLM_PROVIDER.lower()
    if provider_type in ["mock", "fake", "test"]:
        return {
            "provider": "mock",
            "model": "mock-lenny-v1",
        }
    elif provider_type == "cloud":
        return {
            "provider": f"cloud:{settings.CLOUD_PROVIDER}",
            "model": settings.CLOUD_MODEL,
        }
    else:
        return {
            "provider": "ollama",
            "model": settings.OLLAMA_MODEL,
        }


__all__ = [
    "LLMProvider",
    "OllamaProvider",
    "CloudProvider",
    "FakeLLMProvider",
    "get_llm_provider",
    "get_active_provider_info",
    "set_llm_provider_override",
]

