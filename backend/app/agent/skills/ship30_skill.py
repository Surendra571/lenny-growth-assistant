import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.prompts import (
    STANDARD_REFUSAL_MESSAGE,
    SYSTEM_PROMPT_SHIP30,
    format_ship30_prompt,
)
from app.agent.providers import LLMProvider, get_llm_provider
from app.core.config import settings
from app.core.logging import logger
from app.knowledge.retriever import HybridRetriever
from app.schemas.message import SourceCitation
from app.schemas.ship30 import Ship30Response


class Ship30Skill:
    """
    Dedicated agent skill that synthesizes grounded Lenny's Podcast insights
    into high-impact, skimmable ~1,250-word editorial essays following the Ship 30 for 30 methodology.
    """

    @classmethod
    def resolve_effective_topic(
        cls,
        topic: Optional[str],
        turn_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Resolve pronouns, implicit follow-ups, or context from prior turns if the query is a reference.
        """
        raw_topic = (topic or "").strip()
        
        # Check if user prompt is a context follow-up (e.g. "turn those ideas into a post")
        reference_patterns = [
            "those ideas", "these ideas", "that topic", "this topic", "what we discussed", "the previous topic",
            "the podcast insights", "turn this into", "turn that into", "write a post about that",
            "write an essay about that", "write an article about that", "make a post about that",
            "turn into a ship 30", "turn into a ship30", "make a ship 30", "make a ship30",
            "turn into a post", "turn into an essay", "turn into an article",
            "turn that into", "turn this into",
        ]
        is_reference = any(p in raw_topic.lower() for p in reference_patterns) or len(raw_topic) < 10

        if is_reference and turn_history:
            # Look backwards through history: prefer prior user queries that established the topic
            prior_user_turns = [
                t.get("content", "").strip()
                for t in turn_history
                if t.get("role") == "user"
                and len(t.get("content", "").strip()) > 8
                and not any(p in t.get("content", "").lower() for p in ["turn this into", "turn that into", "write a ship 30", "make a ship 30"])
            ]
            if prior_user_turns:
                return prior_user_turns[-1]

            # Fallback to any prior substantial turn
            for turn in reversed(turn_history):
                content = turn.get("content", "").strip()
                if content and len(content) > 10:
                    return content[:200]

        return raw_topic or "Product management, growth strategy, and product-market fit"

    @classmethod
    async def generate_essay(
        cls,
        db: Optional[AsyncSession],
        session_id: uuid.UUID,
        topic: Optional[str] = None,
        audience: Optional[str] = None,
        angle: Optional[str] = None,
        tone: Optional[str] = None,
        temperature: float = 0.7,
        turn_history: Optional[List[Dict[str, str]]] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> Ship30Response:
        """
        Execute the Ship 30 for 30 generation pipeline:
        1. Resolve contextual follow-ups from turn history.
        2. Retrieve diverse transcript evidence from knowledge base.
        3. Check grounding threshold — refuse if unsupported.
        4. Assemble structured prompt with strict boundary isolation.
        5. Generate ~1,250-word essay with hook, narrative, 3 pillars, and takeaway.
        6. Extract metadata and calculate exact word count.
        """
        effective_topic = cls.resolve_effective_topic(topic, turn_history)
        logger.info(f"Ship30Skill executing for session {session_id} on topic: '{effective_topic[:80]}'")

        # 1. Retrieve knowledge evidence
        retriever = HybridRetriever(db=db)
        citations: List[SourceCitation] = await retriever.retrieve(
            query=effective_topic,
            limit=6,
            similarity_threshold=settings.GROUNDING_SIMILARITY_THRESHOLD,
        )

        provider = llm_provider or get_llm_provider()

        # 2. Refusal check for unsupported topics
        if not citations:
            logger.info(f"Ship30Skill: No transcript evidence found for topic '{effective_topic}'. Returning refusal.")
            refusal_text = (
                f"# Topic Not Covered in Lenny's Podcast Transcripts\n\n"
                f"{STANDARD_REFUSAL_MESSAGE}\n\n"
                f"**Requested Topic:** *{topic or 'Unspecified'}*\n\n"
                f"To generate a grounded Ship 30 for 30 essay, please choose a topic covered by podcast guests, "
                f"such as Superhuman's PMF engine (Rahul Vohra), B2B Product-Led Growth (Elena Verna), "
                f"or Product Strategy & Founder Mode (Brian Chesky)."
            )
            words = len(re.findall(r"\b\w+\b", refusal_text))
            return Ship30Response(
                session_id=session_id,
                title="Topic Not Covered in Lenny's Podcast Transcripts",
                content=refusal_text,
                word_count=words,
                sources=[],
                metadata={
                    "skill": "ship30",
                    "status": "refusal",
                    "reason": "insufficient_evidence",
                    "topic": topic,
                },
            )

        # 3. Assemble Ship 30 prompt
        prompt = format_ship30_prompt(
            query=effective_topic,
            citations=citations,
            audience=audience,
            angle=angle,
            tone=tone,
        )

        # 4. Generate essay
        essay_markdown = await provider.generate_text(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT_SHIP30,
            temperature=temperature,
            max_tokens=3500,
        )

        # 5. Extract title
        title_match = re.search(r"^#\s+(.+)$", essay_markdown, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            lines = [l.strip() for l in essay_markdown.splitlines() if l.strip()]
            title = lines[0].lstrip("#").strip() if lines else "Ship 30 for 30: Growth & Product Strategy"

        # 6. Calculate word count
        word_count = len(re.findall(r"\b\w+\b", essay_markdown))

        # 7. Build response
        return Ship30Response(
            session_id=session_id,
            title=title,
            content=essay_markdown,
            word_count=word_count,
            sources=citations,
            metadata={
                "skill": "ship30",
                "status": "success",
                "topic": topic,
                "effective_topic": effective_topic,
                "audience": audience,
                "angle": angle,
                "tone": tone,
                "model": getattr(provider, "model", "default"),
                "source_count": len(citations),
            },
        )
