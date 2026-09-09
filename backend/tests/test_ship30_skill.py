import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.prompts import SYSTEM_PROMPT_SHIP30, format_ship30_prompt
from app.agent.providers.fake_provider import FakeLLMProvider
from app.agent.skills.ship30_skill import Ship30Skill
from app.repositories.session_repository import SessionRepository
from app.schemas.message import SourceCitation


def test_ship30_system_prompt_structure():
    assert "Ship 30 for 30 Editorial Essay Mode" in SYSTEM_PROMPT_SHIP30
    assert "1,250 words" in SYSTEM_PROMPT_SHIP30
    assert "PUNCHY TITLE" in SYSTEM_PROMPT_SHIP30
    assert "STRONG HOOK & TENSION" in SYSTEM_PROMPT_SHIP30
    assert "THREE CORE GROUNDED PILLARS" in SYSTEM_PROMPT_SHIP30
    assert "ACTIONABLE TAKEAWAY FRAMEWORK" in SYSTEM_PROMPT_SHIP30
    assert "ZERO HALLUCINATIONS" in SYSTEM_PROMPT_SHIP30


def test_format_ship30_prompt_customizations():
    citations = [
        SourceCitation(
            chunk_id=uuid.uuid4(),
            episode_title="Superhuman's Product-Market Fit Engine",
            guest_name="Rahul Vohra",
            timestamp="12:30",
            relevance_score=0.91,
            snippet="We created a quantitative survey measuring disappointment if the product vanished.",
        )
    ]
    prompt = format_ship30_prompt(
        query="Product Market Fit Engine",
        citations=citations,
        audience="Seed stage founders",
        angle="Quantitative metrics vs intuition",
        tone="Punchy and direct",
    )

    assert "[EDITORIAL CUSTOMIZATION GUIDELINES]" in prompt
    assert "Target Audience: Seed stage founders" in prompt
    assert "Editorial Angle: Quantitative metrics vs intuition" in prompt
    assert "[RETRIEVED TRANSCRIPT EVIDENCE]" in prompt
    assert "Rahul Vohra" in prompt
    assert "[ESSAY TOPIC / USER REQUEST]" in prompt


def test_resolve_effective_topic_with_history():
    history = [
        {"role": "user", "content": "How does Elena Verna explain B2B product-led growth and freemium funnels?"},
        {"role": "assistant", "content": "Elena Verna explains that PLG is not just self-serve signups..."},
    ]
    resolved = Ship30Skill.resolve_effective_topic("Turn those ideas into a Ship 30 post", history)
    assert "Elena Verna" in resolved or "B2B" in resolved


@pytest.mark.asyncio
async def test_ship30_skill_generate_supported_topic(db_session: AsyncSession):
    session = await SessionRepository.create(db=db_session, title="Ship 30 Test Session")
    fake_llm = FakeLLMProvider()

    result = await Ship30Skill.generate_essay(
        db=db_session,
        session_id=session.id,
        topic="How did Superhuman measure product market fit with Rahul Vohra?",
        audience="Startup PMs",
        llm_provider=fake_llm,
    )

    assert result.session_id == session.id
    assert len(result.sources) > 0
    assert any("Rahul Vohra" in s.guest_name for s in result.sources)
    assert result.word_count >= 1000
    assert result.word_count <= 1500
    assert result.title
    assert "## Pillar 1" in result.content or "Pillar 1" in result.content or "##" in result.content
    assert "Try This Next" in result.content
    assert result.metadata["status"] == "success"


@pytest.mark.asyncio
async def test_ship30_skill_unsupported_topic_refusal(db_session: AsyncSession):
    session = await SessionRepository.create(db=db_session, title="Unsupported Topic Session")
    fake_llm = FakeLLMProvider()

    result = await Ship30Skill.generate_essay(
        db=db_session,
        session_id=session.id,
        topic="Quantum thermodynamics molecular orbit decay in astrophysics",
        llm_provider=fake_llm,
    )

    assert result.session_id == session.id
    assert len(result.sources) == 0
    assert result.metadata["status"] == "refusal"
    assert "Topic Not Covered" in result.title
    assert "available Lenny podcast transcript material" in result.content

