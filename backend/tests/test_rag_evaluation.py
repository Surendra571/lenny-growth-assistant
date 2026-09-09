import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.prompts import STANDARD_REFUSAL_MESSAGE
from app.agent.providers.fake_provider import FakeLLMProvider
from app.agent.skills.qa_skill import GroundedQASkill
from app.knowledge.retriever import HybridRetriever
from app.repositories.session_repository import SessionRepository
from app.schemas.chat import ChatRequest
from app.services.agent_service import AgentService


class CountingMockProvider(FakeLLMProvider):
    """Mock provider that tracks how many times generate_text/stream is called."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.call_count = 0

    async def generate_text(self, *args, **kwargs):
        self.call_count += 1
        return await super().generate_text(*args, **kwargs)

    async def generate_stream(self, *args, **kwargs):
        self.call_count += 1
        async for chunk in super().generate_stream(*args, **kwargs):
            yield chunk


@pytest.mark.asyncio
async def test_unsupported_query_bypasses_llm_completely(db_session: AsyncSession):
    """
    Priority 1 & 8 Invariant:
    When a query has no relevant transcript evidence, the system MUST NOT call the LLM,
    and MUST return the deterministic refusal with zero fake citations.
    """
    session = await SessionRepository.create(db=db_session, title="Refusal Invariant Test")
    mock_llm = CountingMockProvider()

    req = ChatRequest(message="How do I make chocolate chip cookies from scratch?")
    response = await AgentService.chat(
        db=db_session,
        session_id=session.id,
        payload=req,
        llm_provider=mock_llm,
    )

    # 1. Assert LLM was never called
    assert mock_llm.call_count == 0, "LLM was called when evidence was absent!"

    # 2. Assert deterministic refusal message
    assert STANDARD_REFUSAL_MESSAGE in response.assistant_message.content

    # 3. Assert zero citations/sources
    assert len(response.sources) == 0


@pytest.mark.asyncio
async def test_grounded_query_invokes_llm_with_citations(db_session: AsyncSession):
    """
    Valid on-domain query passes threshold, retrieves citations, and invokes the LLM.
    """
    session = await SessionRepository.create(db=db_session, title="Grounded Query Test")
    mock_llm = CountingMockProvider()

    req = ChatRequest(message="How did Superhuman measure product market fit with Rahul Vohra?")
    response = await AgentService.chat(
        db=db_session,
        session_id=session.id,
        payload=req,
        llm_provider=mock_llm,
    )

    # 1. Assert LLM was called exactly once
    assert mock_llm.call_count == 1

    # 2. Assert citations present with real scores
    assert len(response.sources) > 0
    for s in response.sources:
        assert s.relevance_score >= 0.30
        assert len(s.guest_name) > 0
        assert len(s.episode_title) > 0
        assert len(s.snippet) > 0


@pytest.mark.asyncio
async def test_multi_turn_follow_up_passes_history(db_session: AsyncSession):
    """
    Priority 2 Invariant:
    Follow-up questions receive previous conversational turn history.
    """
    session = await SessionRepository.create(db=db_session, title="Multi-Turn Flow Test")
    mock_llm = CountingMockProvider()

    # Turn 1
    req1 = ChatRequest(message="What did Brian Chesky say about leading Airbnb in founder mode?")
    resp1 = await AgentService.chat(db=db_session, session_id=session.id, payload=req1, llm_provider=mock_llm)
    assert mock_llm.call_count == 1
    assert "Brian Chesky" in resp1.assistant_message.content

    # Turn 2 (Follow-up relying on Turn 1 context)
    req2 = ChatRequest(message="How does that apply to designing core product details?")
    resp2 = await AgentService.chat(db=db_session, session_id=session.id, payload=req2, llm_provider=mock_llm)
    assert mock_llm.call_count == 2
    assert mock_llm.last_turn_history is not None
    assert len(mock_llm.last_turn_history) >= 2


@pytest.mark.asyncio
async def test_citation_attribution_integrity():
    """
    Priority 9 Invariant:
    Ensure citations contain clean, human-readable guest names, episode titles,
    and do not leak raw database IDs or credentials.
    """
    retriever = HybridRetriever(local_raw_dir="data/raw")
    citations = await retriever.retrieve("What is Shreyas Doshi advice on high agency?", limit=3)

    assert len(citations) > 0
    for c in citations:
        assert c.guest_name == "Shreyas Doshi"
        assert "password" not in c.snippet.lower()
        assert "secret" not in c.snippet.lower()
        assert c.relevance_score <= 1.0
        assert c.relevance_score >= 0.30
