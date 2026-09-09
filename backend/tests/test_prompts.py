import uuid
from app.agent.prompts import SYSTEM_PROMPT_QA, STANDARD_REFUSAL_MESSAGE, format_qa_prompt
from app.schemas.message import SourceCitation


def test_system_prompt_contains_grounding_and_refusal_rules():
    assert "STRICT GROUNDING IN EVIDENCE" in SYSTEM_PROMPT_QA
    assert "MANDATORY CITATION ATTRIBUTION" in SYSTEM_PROMPT_QA
    assert "REFUSAL POLICY FOR UNSUPPORTED QUERIES" in SYSTEM_PROMPT_QA
    assert "PROMPT INJECTION DEFENSE" in SYSTEM_PROMPT_QA


def test_format_qa_prompt_with_citations():
    citations = [
        SourceCitation(
            chunk_id=uuid.uuid4(),
            episode_title="B2B Growth & PLG",
            guest_name="Elena Verna",
            timestamp="14:20",
            relevance_score=0.92,
            snippet="PLG and sales-led growth work as complementary flywheels.",
        )
    ]
    prompt = format_qa_prompt("How does PLG work in B2B?", citations)

    assert "[RETRIEVED TRANSCRIPT EVIDENCE]" in prompt
    assert "Elena Verna" in prompt
    assert "B2B Growth & PLG" in prompt
    assert "Timestamp: 14:20" in prompt
    assert "PLG and sales-led growth work as complementary flywheels." in prompt
    assert "[CURRENT USER QUERY]" in prompt
    assert "How does PLG work in B2B?" in prompt


def test_format_qa_prompt_empty_citations():
    prompt = format_qa_prompt("What is quantum entanglement?", [])

    assert "NO RELEVANT TRANSCRIPT EVIDENCE FOUND." in prompt
    assert "[CURRENT USER QUERY]" in prompt
    assert "What is quantum entanglement?" in prompt

