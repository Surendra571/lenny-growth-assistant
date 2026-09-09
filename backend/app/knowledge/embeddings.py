from abc import ABC, abstractmethod
import hashlib
import math
import re
from typing import List, Optional
import httpx
import numpy as np
from app.core.config import settings
from app.core.logging import logger


class EmbeddingProvider(ABC):
    """
    Abstract interface for generating vector embeddings from text chunks.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass


class LocalDeterministicEmbeddingProvider(EmbeddingProvider):
    """
    Fast, deterministic, normalized semantic-hash vectorizer (384 dimensions).
    Provides consistent cosine similarity for local testing, offline demo, and unit tests
    without requiring heavy PyTorch/CUDA downloads.
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_text(self, text: str) -> List[float]:
        return self._compute_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._compute_embedding(t) for t in texts]

    def _compute_embedding(self, text: str) -> List[float]:
        words = re.findall(r"\w+", text.lower())
        vec = np.zeros(self._dim, dtype=np.float32)

        if not words:
            return vec.tolist()

        for word in words:
            # Hash word into dimension index and sign
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            
            # Position-sensitive feature weighting
            vec[idx] += sign

            # Bigram feature
            h2 = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx2 = (h2 >> 4) % self._dim
            vec[idx2] += 0.5 * sign

        # L2 Normalization so dot product equals cosine similarity
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec = vec / norm
        return vec.tolist()


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Adapter for local Ollama embedding models (e.g. nomic-embed-text, all-minilm).
    """

    def __init__(self, base_url: Optional[str] = None, model: str = "nomic-embed-text"):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model
        self._dim = 384

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_text(self, text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            if res.status_code == 200:
                data = res.json()
                emb = data.get("embedding", [])
                self._dim = len(emb)
                return emb
            else:
                logger.warning(f"Ollama embeddings fallback: {res.status_code}")
                fallback = LocalDeterministicEmbeddingProvider(self._dim)
                return await fallback.embed_text(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        results = []
        for text in texts:
            results.append(await self.embed_text(text))
        return results


class CloudOpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Adapter for OpenAI embedding API (text-embedding-3-small, 1536 dim).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or (settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else "")
        self.model = model
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed_text(self, text: str) -> List[float]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        res = await client.embeddings.create(model=self.model, input=[text])
        return res.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        res = await client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in res.data]


def get_embedding_provider() -> EmbeddingProvider:
    """
    Factory creating the configured embedding provider.
    """
    if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return CloudOpenAIEmbeddingProvider()
    elif settings.EMBEDDING_PROVIDER == "ollama":
        return OllamaEmbeddingProvider()
    return LocalDeterministicEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)

