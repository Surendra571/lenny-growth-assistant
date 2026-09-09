import uuid
from typing import AsyncIterator, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.prompts import SYSTEM_PROMPT_QA, format_qa_prompt
from app.agent.providers import LLMProvider, get_llm_provider
from app.agent.router import AgentRouter
from app.agent.skills import GroundedQASkill, Ship30Skill
from app.core.config import settings
from app.core.errors import SessionNotFoundException
from app.core.logging import logger
from app.knowledge.retriever import HybridRetriever
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.message import MessageResponse, SourceCitation
from app.schemas.ship30 import Ship30Request, Ship30Response
from app.services.artifact_service import ArtifactService


class AgentService:
    """
    Core conversational agent service orchestrating session context,
    hybrid retrieval, skill dispatching (Q&A, Ship 30), LLM execution,
    and transactional persistence.
    """

    @classmethod
    async def chat(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        payload: ChatRequest,
        llm_provider: Optional[LLMProvider] = None,
    ) -> ChatResponse:
        """
        Execute a complete conversational turn:
        1. Validate session existence.
        2. Classify intent via deterministic router (or respect explicit override).
        3. Dispatch to specialized skill (Ship 30 or Grounded Q&A).
        4. Persist user and assistant messages atomically.
        5. Return structured ChatResponse with source citations.
        """
        # 1. Validate session existence
        session = await SessionRepository.get_by_id(db, session_id)
        if not session:
            logger.warning(f"Chat execution requested for nonexistent session: {session_id}")
            raise SessionNotFoundException(str(session_id))

        # 2. Intent classification
        intent_result = AgentRouter.classify_intent(
            user_message=payload.message,
            skill_override=payload.skill_override,
        )

        # 3. Load recent session turn history for context
        recent_messages = await MessageRepository.list_for_session(
            db=db,
            session_id=session_id,
            limit=10,
        )
        turn_history = [
            {"role": m.role, "content": m.content}
            for m in recent_messages
            if m.role in ["user", "assistant"]
        ]

        provider = llm_provider or get_llm_provider()

        # 4. Route to Ship 30 for 30 Skill if intent is ship30
        if intent_result.intent == "ship30":
            ship30_res = await Ship30Skill.generate_essay(
                db=db,
                session_id=session_id,
                topic=payload.message,
                turn_history=turn_history,
                llm_provider=provider,
                temperature=payload.temperature if payload.temperature is not None else 0.7,
            )

            # Persist user message
            user_msg = await MessageRepository.create(
                db=db,
                session_id=session_id,
                role="user",
                content=payload.message,
                metadata={
                    "intent": "ship30",
                    "skill_override": payload.skill_override,
                },
            )

            # Persist assistant message
            sources_data = [c.model_dump(mode="json") for c in ship30_res.sources]
            assistant_metadata = {
                "intent": "ship30",
                "skill": "ship30",
                "title": ship30_res.title,
                "word_count": ship30_res.word_count,
                "sources": sources_data,
                "model": getattr(provider, "model", "default"),
            }

            # If Ship 30 generation was successful, auto-persist as Markdown artifact
            if ship30_res.metadata.get("status") == "success":
                try:
                    artifact = await ArtifactService.create_from_ship30(
                        db=db,
                        session_id=session_id,
                        ship30_res=ship30_res,
                    )
                    assistant_metadata["artifact_id"] = str(artifact.id)
                except Exception as e:
                    logger.warning(f"Failed to auto-persist Ship 30 artifact: {e}")

            assistant_msg = await MessageRepository.create(
                db=db,
                session_id=session_id,
                role="assistant",
                content=ship30_res.content,
                metadata=assistant_metadata,
            )

            return ChatResponse(
                session_id=session_id,
                intent="ship30",
                user_message=MessageResponse.model_validate(user_msg),
                assistant_message=MessageResponse.model_validate(assistant_msg),
                sources=ship30_res.sources,
            )

        # 5. Default Grounded Q&A Path
        retriever = HybridRetriever(db=db)
        citations: List[SourceCitation] = await retriever.retrieve(
            query=payload.message,
            limit=settings.MAX_RETRIEVAL_CHUNKS,
            similarity_threshold=settings.GROUNDING_SIMILARITY_THRESHOLD,
        )

        response_text = await GroundedQASkill.generate_answer(
            query=payload.message,
            citations=citations,
            turn_history=turn_history,
            llm_provider=provider,
            temperature=payload.temperature if payload.temperature is not None else 0.7,
        )

        # Persist messages atomically
        user_msg = await MessageRepository.create(
            db=db,
            session_id=session_id,
            role="user",
            content=payload.message,
            metadata={
                "intent": intent_result.intent,
                "skill_override": payload.skill_override,
            },
        )

        sources_data = [c.model_dump(mode="json") for c in citations]
        assistant_msg = await MessageRepository.create(
            db=db,
            session_id=session_id,
            role="assistant",
            content=response_text,
            metadata={
                "intent": intent_result.intent,
                "sources": sources_data,
                "model": getattr(provider, "model", "default"),
            },
        )

        return ChatResponse(
            session_id=session_id,
            intent=intent_result.intent,
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
            sources=citations,
        )

    @classmethod
    async def generate_ship30(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        payload: Ship30Request,
        llm_provider: Optional[LLMProvider] = None,
    ) -> Ship30Response:
        """
        Direct dedicated endpoint execution for Ship 30 for 30 essay generation.
        """
        session = await SessionRepository.get_by_id(db, session_id)
        if not session:
            logger.warning(f"Ship30 requested for nonexistent session: {session_id}")
            raise SessionNotFoundException(str(session_id))

        recent_messages = await MessageRepository.list_for_session(
            db=db,
            session_id=session_id,
            limit=10,
        )
        turn_history = [
            {"role": m.role, "content": m.content}
            for m in recent_messages
            if m.role in ["user", "assistant"]
        ]

        provider = llm_provider or get_llm_provider()

        result = await Ship30Skill.generate_essay(
            db=db,
            session_id=session_id,
            topic=payload.topic,
            audience=payload.audience,
            angle=payload.angle,
            tone=payload.tone,
            temperature=payload.temperature if payload.temperature is not None else 0.7,
            turn_history=turn_history,
            llm_provider=provider,
        )

        # Persist conversation turn
        user_prompt_text = payload.topic or "Generate a Ship 30 for 30 essay"
        user_msg = await MessageRepository.create(
            db=db,
            session_id=session_id,
            role="user",
            content=user_prompt_text,
            metadata={
                "intent": "ship30",
                "audience": payload.audience,
                "angle": payload.angle,
                "tone": payload.tone,
            },
        )

        sources_data = [c.model_dump(mode="json") for c in result.sources]
        assistant_metadata = {
            "intent": "ship30",
            "skill": "ship30",
            "title": result.title,
            "word_count": result.word_count,
            "sources": sources_data,
            "model": getattr(provider, "model", "default"),
        }

        # If Ship 30 generation was successful, auto-persist as Markdown artifact
        if result.metadata.get("status") == "success":
            try:
                artifact = await ArtifactService.create_from_ship30(
                    db=db,
                    session_id=session_id,
                    ship30_res=result,
                )
                assistant_metadata["artifact_id"] = str(artifact.id)
            except Exception as e:
                logger.warning(f"Failed to auto-persist Ship 30 artifact: {e}")

        assistant_msg = await MessageRepository.create(
            db=db,
            session_id=session_id,
            role="assistant",
            content=result.content,
            metadata=assistant_metadata,
        )

        result.user_message = MessageResponse.model_validate(user_msg)
        result.assistant_message = MessageResponse.model_validate(assistant_msg)
        return result
