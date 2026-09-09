import math
import numpy as np
import pytest
from app.knowledge.embeddings import LocalDeterministicEmbeddingProvider


@pytest.mark.asyncio
async def test_deterministic_embedding_provider():
    provider = LocalDeterministicEmbeddingProvider(dimension=384)
    assert provider.dimension == 384

    emb1 = await provider.embed_text("Product market fit and retention curves")
    assert len(emb1) == 384
    
    # Check L2 unit norm
    norm = np.linalg.norm(emb1)
    assert math.isclose(norm, 1.0, rel_tol=1e-4)

    # Determinism check
    emb2 = await provider.embed_text("Product market fit and retention curves")
    assert emb1 == emb2

    # Semantic similarity check: related texts should have higher cosine similarity than unrelated texts
    emb_related = await provider.embed_text("Measuring PMF with customer surveys and retention")
    emb_unrelated = await provider.embed_text("Kubernetes cluster network topology configuration")

    sim_related = float(np.dot(emb1, emb_related))
    sim_unrelated = float(np.dot(emb1, emb_unrelated))

    assert sim_related > sim_unrelated


@pytest.mark.asyncio
async def test_embed_batch():
    provider = LocalDeterministicEmbeddingProvider(dimension=384)
    texts = ["First document", "Second document", "Third document"]
    embeddings = await provider.embed_batch(texts)
    assert len(embeddings) == 3
    assert all(len(e) == 384 for e in embeddings)

