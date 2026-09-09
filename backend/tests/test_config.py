from app.core.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.ENVIRONMENT in ["development", "production", "test"]
    assert settings.LLM_PROVIDER in ["ollama", "cloud", "mock", "fake"]
    assert settings.GROUNDING_SIMILARITY_THRESHOLD == 0.30
    assert settings.MAX_RETRIEVAL_CHUNKS == 6
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0

