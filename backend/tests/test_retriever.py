import pytest
from app.knowledge.retriever import HybridRetriever
from app.knowledge.evaluator import RetrievalEvaluator


@pytest.mark.asyncio
async def test_hybrid_retriever_positive_query():
    retriever = HybridRetriever(local_raw_dir="data/raw")
    citations = await retriever.retrieve("How did Superhuman measure product market fit with Rahul Vohra?", limit=3)
    
    assert len(citations) > 0
    top = citations[0]
    assert "Rahul Vohra" in top.guest_name
    assert top.relevance_score >= 0.30
    assert len(top.snippet) > 0


@pytest.mark.asyncio
async def test_hybrid_retriever_negative_refusal():
    retriever = HybridRetriever(local_raw_dir="data/raw")
    # Highly technical out-of-domain query with no growth/product intersection
    citations = await retriever.retrieve("Quantum chromodynamics gluon plasma hadron decay rates", limit=3)
    
    # Should produce 0 results passing threshold
    assert len(citations) == 0


@pytest.mark.asyncio
async def test_hybrid_retriever_ordering_and_scores():
    retriever = HybridRetriever(local_raw_dir="data/raw")
    citations = await retriever.retrieve("What is Elena Verna advice on B2B product-led growth and freemium?", limit=5)
    
    assert len(citations) >= 1
    # Verify scores are sorted descending
    scores = [c.relevance_score for c in citations]
    assert scores == sorted(scores, reverse=True)
    # Verify top result matches guest
    assert citations[0].guest_name == "Elena Verna"
    assert citations[0].relevance_score > 0.50


@pytest.mark.asyncio
async def test_hybrid_retriever_threshold_boundary():
    retriever = HybridRetriever(local_raw_dir="data/raw")
    # With a high threshold of 0.95, only direct guest matches qualify
    strict_citations = await retriever.retrieve("How to build growth loops?", similarity_threshold=0.95)
    # With a calibrated threshold of 0.30, relevant chunks qualify
    calibrated_citations = await retriever.retrieve("How to build growth loops?", similarity_threshold=0.30)
    
    assert len(calibrated_citations) >= len(strict_citations)


@pytest.mark.asyncio
async def test_retrieval_benchmark_evaluator():
    evaluator = RetrievalEvaluator()
    res = await evaluator.run_evaluation(k=5)
    
    assert res.total_queries >= 20
    assert res.hit_rate_at_k >= 0.80
    assert res.refusal_precision >= 0.90
    assert res.traceability_rate == 1.0

