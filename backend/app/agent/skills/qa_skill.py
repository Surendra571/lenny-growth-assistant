from typing import Dict, List, Optional
from app.agent.prompts import STANDARD_REFUSAL_MESSAGE, SYSTEM_PROMPT_QA, format_qa_prompt
from app.agent.providers import LLMProvider
from app.core.logging import logger
from app.schemas.message import SourceCitation


class GroundedQASkill:
    """
    Dedicated grounded conversational Q&A skill.
    Enforces the core architectural invariant:
    - If no relevant transcript evidence exists: deterministically refuse (NO LLM CALL).
    - If valid transcript evidence exists: synthesize answer grounded strictly in evidence,
      integrating multi-turn conversational context.
    """

    @classmethod
    async def generate_answer(
        cls,
        query: str,
        citations: List[SourceCitation],
        turn_history: Optional[List[Dict[str, str]]] = None,
        llm_provider: Optional[LLMProvider] = None,
        temperature: float = 0.7,
    ) -> str:
        # Priority 1 Architectural Invariant:
        # If no citations pass relevance threshold, DO NOT call LLM.
        if not citations:
            logger.info("Deterministic refusal triggered: no relevant citations meeting grounding threshold.")
            return STANDARD_REFUSAL_MESSAGE

        if llm_provider is None:
            from app.agent.providers import get_llm_provider
            llm_provider = get_llm_provider()

        # Bounded conversation history (latest 6 turns)
        bounded_history = turn_history[-6:] if turn_history else []

        user_prompt = format_qa_prompt(
            query=query,
            citations=citations,
            turn_history=bounded_history,
        )

        response_text = await llm_provider.generate_text(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT_QA,
            turn_history=bounded_history,
            temperature=temperature,
        )

        return response_text
