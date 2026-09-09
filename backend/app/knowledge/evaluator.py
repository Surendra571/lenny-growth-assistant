import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.core.logging import logger
from app.knowledge.retriever import HybridRetriever
from app.schemas.message import SourceCitation


class EvalQuestion(BaseModel):
    id: str
    category: str
    query: str
    expected_guest: Optional[str] = None
    expected_topic: Optional[str] = None
    is_out_of_domain: bool = False


# Canonical 20-Question Gold Standard Evaluation Set
EVALUATION_DATASET: List[EvalQuestion] = [
    # 1. Product-Market Fit
    EvalQuestion(
        id="q-01",
        category="product-market-fit",
        query="How did Superhuman measure product-market fit with the 40% rule?",
        expected_guest="Rahul Vohra",
        expected_topic="PMF Engine",
    ),
    EvalQuestion(
        id="q-02",
        category="product-market-fit",
        query="What survey question does Rahul Vohra ask to find the High-Expectation Customer?",
        expected_guest="Rahul Vohra",
        expected_topic="HXC segmentation",
    ),
    # 2. Product Leadership & Founder Mode
    EvalQuestion(
        id="q-03",
        category="leadership",
        query="What is Brian Chesky's Founder Mode philosophy at Airbnb?",
        expected_guest="Brian Chesky",
        expected_topic="Founder Mode",
    ),
    EvalQuestion(
        id="q-04",
        category="leadership",
        query="Why did Airbnb combine product management with product marketing?",
        expected_guest="Brian Chesky",
        expected_topic="Product Marketing integration",
    ),
    # 3. Task Prioritization & Strategy
    EvalQuestion(
        id="q-05",
        category="product-strategy",
        query="How does Shreyas Doshi define the LNO framework for Leverage, Neutral, and Overhead tasks?",
        expected_guest="Shreyas Doshi",
        expected_topic="LNO Framework",
    ),
    EvalQuestion(
        id="q-06",
        category="product-strategy",
        query="How do pre-mortems help product teams identify risks before shipping?",
        expected_guest="Shreyas Doshi",
        expected_topic="Pre-mortems",
    ),
    # 4. B2B Product-Led Growth (PLG)
    EvalQuestion(
        id="q-07",
        category="growth-plg",
        query="How does Elena Verna recommend choosing between Freemium and a 14-day Free Trial?",
        expected_guest="Elena Verna",
        expected_topic="Freemium vs Free Trial",
    ),
    EvalQuestion(
        id="q-08",
        category="growth-plg",
        query="What features should go behind the paid paywall according to Elena Verna?",
        expected_guest="Elena Verna",
        expected_topic="Paywalls & Monetization",
    ),
    # 5. Product Architecture & Multiplayer Growth
    EvalQuestion(
        id="q-09",
        category="collaboration",
        query="How did Figma use WebGL in the browser to unlock multiplayer design collaboration?",
        expected_guest="Dylan Field",
        expected_topic="Multiplayer collaboration",
    ),
    # 6. Decision Making & SPADE
    EvalQuestion(
        id="q-10",
        category="decision-making",
        query="What are the 5 components of Gokul Rajaram's SPADE decision-making framework?",
        expected_guest="Gokul Rajaram",
        expected_topic="SPADE Framework",
    ),
    EvalQuestion(
        id="q-11",
        category="decision-making",
        query="How should a company choose its North Star Metric according to Gokul Rajaram?",
        expected_guest="Gokul Rajaram",
        expected_topic="North Star Metric",
    ),
    # 7. Experimentation & Growth Hacking
    EvalQuestion(
        id="q-12",
        category="experimentation",
        query="How do you calculate the ICE score for growth experiments according to Sean Ellis?",
        expected_guest="Sean Ellis",
        expected_topic="ICE Score",
    ),
    EvalQuestion(
        id="q-13",
        category="experimentation",
        query="What is the relationship between testing velocity and growth rate?",
        expected_guest="Sean Ellis",
        expected_topic="Testing Velocity",
    ),
    # 8. Product Positioning
    EvalQuestion(
        id="q-14",
        category="positioning",
        query="What are the 5 components of product positioning defined by April Dunford?",
        expected_guest="April Dunford",
        expected_topic="5 Components of Positioning",
    ),
    EvalQuestion(
        id="q-15",
        category="positioning",
        query="Why is falling into the 'Better Trap' dangerous according to April Dunford?",
        expected_guest="April Dunford",
        expected_topic="The Better Trap",
    ),
    # 9. Marketplace Cold Start
    EvalQuestion(
        id="q-16",
        category="marketplaces",
        query="How do two-sided marketplaces solve the cold start chicken-and-egg problem?",
        expected_guest="Lenny Rachitsky",
        expected_topic="Marketplace Cold Start",
    ),
    # 10. Retention Curves
    EvalQuestion(
        id="q-17",
        category="retention",
        query="How does Casey Winters analyze cohort retention curves to identify product-market fit?",
        expected_guest="Casey Winters",
        expected_topic="Retention Curves",
    ),
    EvalQuestion(
        id="q-18",
        category="retention",
        query="What is the difference between a Feature PM and a Growth PM according to Casey Winters?",
        expected_guest="Casey Winters",
        expected_topic="Feature vs Growth PM",
    ),
    # 11. Negative / Out-of-Domain Controls (Must Refuse / Yield 0 Results)
    EvalQuestion(
        id="q-19",
        category="negative-control",
        query="How do I configure an Nginx SSL reverse proxy for Kubernetes ingress?",
        expected_guest=None,
        is_out_of_domain=True,
    ),
    EvalQuestion(
        id="q-20",
        category="negative-control",
        query="What is the biochemical mechanism of CRISPR Cas9 gene editing in T-cells?",
        expected_guest=None,
        is_out_of_domain=True,
    ),
]


class RetrievalEvaluationResult(BaseModel):
    total_queries: int
    positive_queries: int
    negative_queries: int
    hit_rate_at_k: float = Field(description="Percentage of positive queries where expected source was in top-k")
    mrr: float = Field(description="Mean Reciprocal Rank")
    refusal_precision: float = Field(description="Percentage of out-of-domain queries correctly producing 0 results")
    traceability_rate: float = Field(description="Percentage of retrieved chunks with valid episode and guest metadata")
    details: List[Dict[str, Any]] = []


class RetrievalEvaluator:
    """
    Automated evaluation harness benchmarking retrieval accuracy, MRR, and guardrails.
    """

    def __init__(self, retriever: Optional[HybridRetriever] = None):
        self.retriever = retriever or HybridRetriever()

    async def run_evaluation(self, k: int = 5) -> RetrievalEvaluationResult:
        logger.info(f"Running retrieval benchmark across {len(EVALUATION_DATASET)} queries (Top-K = {k})...")
        
        positive_queries = [q for q in EVALUATION_DATASET if not q.is_out_of_domain]
        negative_queries = [q for q in EVALUATION_DATASET if q.is_out_of_domain]

        hits = 0
        reciprocal_ranks = []
        traceable_chunks = 0
        total_retrieved_chunks = 0
        correct_refusals = 0
        details = []

        for q in EVALUATION_DATASET:
            citations = await self.retriever.retrieve(q.query, limit=k)
            total_retrieved_chunks += len(citations)

            for c in citations:
                if c.episode_title and c.guest_name:
                    traceable_chunks += 1

            if q.is_out_of_domain:
                if len(citations) == 0:
                    correct_refusals += 1
                details.append({
                    "id": q.id,
                    "query": q.query,
                    "is_negative": True,
                    "citations_found": len(citations),
                    "passed": len(citations) == 0,
                })
            else:
                hit = False
                rank = 0
                for idx, c in enumerate(citations):
                    if q.expected_guest and q.expected_guest.lower() in c.guest_name.lower():
                        hit = True
                        rank = idx + 1
                        break

                if hit:
                    hits += 1
                    reciprocal_ranks.append(1.0 / rank)
                else:
                    reciprocal_ranks.append(0.0)

                details.append({
                    "id": q.id,
                    "query": q.query,
                    "expected_guest": q.expected_guest,
                    "hit": hit,
                    "rank": rank,
                    "top_guest": citations[0].guest_name if citations else None,
                    "top_score": citations[0].relevance_score if citations else 0.0,
                })

        hit_rate = round(hits / max(1, len(positive_queries)), 4)
        mrr = round(sum(reciprocal_ranks) / max(1, len(positive_queries)), 4)
        refusal_prec = round(correct_refusals / max(1, len(negative_queries)), 4)
        traceability = round(traceable_chunks / max(1, total_retrieved_chunks), 4) if total_retrieved_chunks > 0 else 1.0

        res = RetrievalEvaluationResult(
            total_queries=len(EVALUATION_DATASET),
            positive_queries=len(positive_queries),
            negative_queries=len(negative_queries),
            hit_rate_at_k=hit_rate,
            mrr=mrr,
            refusal_precision=refusal_prec,
            traceability_rate=traceability,
            details=details,
        )

        logger.info(
            f"Benchmark Results: Hit Rate @ {k}: {hit_rate * 100:.1f}%, MRR: {mrr:.3f}, "
            f"Refusal Precision: {refusal_prec * 100:.1f}%, Traceability: {traceability * 100:.1f}%"
        )
        return res


async def main():
    evaluator = RetrievalEvaluator()
    result = await evaluator.run_evaluation(k=5)
    print(f"\n=================== RETRIEVAL BENCHMARK REPORT ===================")
    print(f"Total Queries Evaluated:    {result.total_queries}")
    print(f"Positive Test Cases:        {result.positive_queries}")
    print(f"Negative Control Cases:     {result.negative_queries}")
    print(f"Hit Rate @ K=5:             {result.hit_rate_at_k * 100:.1f}%")
    print(f"Mean Reciprocal Rank (MRR): {result.mrr:.3f}")
    print(f"Refusal Precision:          {result.refusal_precision * 100:.1f}%")
    print(f"Source Traceability:        {result.traceability_rate * 100:.1f}%")
    print(f"==================================================================\n")


if __name__ == "__main__":
    asyncio.run(main())

