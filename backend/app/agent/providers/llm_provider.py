from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional


class LLMProvider(ABC):
    """
    Abstract Base Class for all LLM inference providers (Ollama, Anthropic Claude, OpenAI).
    Decouples application logic from vendor SDKs.
    """

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        turn_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """
        Stream generation tokens asynchronously.
        """
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        turn_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate complete text response synchronously.
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Verify provider connectivity and model availability.
        """
        pass

