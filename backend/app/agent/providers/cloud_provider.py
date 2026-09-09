from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
from app.agent.providers.llm_provider import LLMProvider
from app.core.config import settings
from app.core.errors import ConfigurationException, ModelTimeoutException, ModelUnavailableException
from app.core.logging import logger


class CloudProvider(LLMProvider):
    """
    Client adapter for Cloud LLM Providers (Anthropic Claude or OpenAI).
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = (provider or settings.CLOUD_PROVIDER).lower()
        self.provider_name = f"cloud:{self.provider}"
        self.model = model or settings.CLOUD_MODEL
        self.timeout = timeout or settings.CLOUD_TIMEOUT_SECONDS
        self._custom_api_key = api_key

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        turn_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        if self.provider == "anthropic":
            async for chunk in self._stream_anthropic(prompt, system_prompt, turn_history, temperature, max_tokens):
                yield chunk
        elif self.provider == "openai":
            async for chunk in self._stream_openai(prompt, system_prompt, turn_history, temperature, max_tokens):
                yield chunk
        else:
            raise ConfigurationException(
                f"Unsupported cloud provider: '{self.provider}'. Supported options: 'anthropic', 'openai'."
            )

    async def _stream_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        turn_history: Optional[List[Dict[str, str]]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        api_key = self._custom_api_key or (settings.ANTHROPIC_API_KEY.get_secret_value() if settings.ANTHROPIC_API_KEY else "")
        if not api_key:
            raise ModelUnavailableException("ANTHROPIC_API_KEY is not configured in environment.")

        try:
            from anthropic import AsyncAnthropic, APITimeoutError
        except ImportError:
            raise ConfigurationException("anthropic library is not installed. Please install anthropic to use Anthropic provider.")

        client = AsyncAnthropic(api_key=api_key, timeout=self.timeout)

        messages = []
        if turn_history:
            for turn in turn_history:
                messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        try:
            async with client.messages.stream(
                model=self.model,
                system=system_prompt or "You are Lenny Growth Assistant, a helpful expert growth advisor.",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except APITimeoutError as e:
            logger.error(f"Anthropic inference timed out: {e}")
            raise ModelTimeoutException("Anthropic API inference timed out.")
        except httpx.TimeoutException as e:
            logger.error(f"Anthropic request timed out: {e}")
            raise ModelTimeoutException("Anthropic API connection timed out.")
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise ModelUnavailableException(f"Anthropic API error: {str(e)}")

    async def _stream_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        turn_history: Optional[List[Dict[str, str]]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        api_key = self._custom_api_key or (settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else "")
        if not api_key:
            raise ModelUnavailableException("OPENAI_API_KEY is not configured in environment.")

        try:
            from openai import AsyncOpenAI, APITimeoutError
        except ImportError:
            raise ConfigurationException("openai library is not installed. Please install openai to use OpenAI provider.")

        client = AsyncOpenAI(api_key=api_key, timeout=self.timeout)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if turn_history:
            for turn in turn_history:
                messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content
        except APITimeoutError as e:
            logger.error(f"OpenAI inference timed out: {e}")
            raise ModelTimeoutException("OpenAI API inference timed out.")
        except httpx.TimeoutException as e:
            logger.error(f"OpenAI request timed out: {e}")
            raise ModelTimeoutException("OpenAI API connection timed out.")
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise ModelUnavailableException(f"OpenAI API error: {str(e)}")

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        turn_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        collected = []
        async for chunk in self.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            turn_history=turn_history,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            collected.append(chunk)
        return "".join(collected)

    async def check_health(self) -> bool:
        if self.provider == "anthropic":
            key = self._custom_api_key or (settings.ANTHROPIC_API_KEY.get_secret_value() if settings.ANTHROPIC_API_KEY else "")
            return bool(key)
        elif self.provider == "openai":
            key = self._custom_api_key or (settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else "")
            return bool(key)
        return False

