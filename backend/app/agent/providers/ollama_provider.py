import json
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
from app.agent.providers.llm_provider import LLMProvider
from app.core.config import settings
from app.core.errors import ModelTimeoutException, ModelUnavailableException
from app.core.logging import logger


class OllamaProvider(LLMProvider):
    """
    Client adapter for local Ollama instances running open-weight models.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.provider_name = "ollama"
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        turn_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if turn_history:
            for turn in turn_history:
                messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        url = f"{self.base_url}/api/chat"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Ollama API error {response.status_code}: {error_text.decode('utf-8')}")
                        raise ModelUnavailableException(f"Ollama returned HTTP {response.status_code}")

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            chunk_text = data.get("message", {}).get("content", "")
                            if chunk_text:
                                yield chunk_text
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {e}")
            raise ModelUnavailableException(f"Cannot connect to Ollama daemon at {self.base_url}. Is Ollama running?")
        except httpx.TimeoutException as e:
            logger.error(f"Ollama inference timed out: {e}")
            raise ModelTimeoutException("Ollama inference execution timed out.")

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
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed on {self.base_url}: {e}")
            return False

