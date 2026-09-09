import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.prompts import STANDARD_REFUSAL_MESSAGE
from app.agent.providers.fake_provider import FakeLLMProvider
from app.core.errors import SessionNotFoundException
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.chat import ChatRequest
from app.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_chat_supported_question_grounded_response(db_session: AsyncSession):
    # 1. Create a session
    session = await SessionRepository.create(
        db=db_session,
        title="Superhuman PMF Discussion",
    )

    # 2. Ask supported question
    fake_llm = FakeLLMProvider()
    req = ChatRequest(message="How did Superhuman measure product market fit with Rahul Vohra?")

    response = await AgentService.chat(
        db=db_session,
        session_id=session.id,
        payload=req,
        llm_provider=fake_llm,
    )

    # 3. Assertions
    assert response.session_id == session.id
    assert response.intent == "qa"
    assert len(response.sources) > 0
    assert any("Rahul Vohra" in s.guest_name for s in response.sources)
    assert "Rahul Vohra" in response.assistant_message.content
    assert response.user_message.role == "user"
    assert response.assistant_message.role == "assistant"

    # 4. Verify DB persistence
    messages = await MessageRepository.list_for_session(db=db_session, session_id=session.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert "sources" in messages[1].message_metadata
    assert len(messages[1].message_metadata["sources"]) > 0


@pytest.mark.asyncio
async def test_chat_unsupported_question_refusal(db_session: AsyncSession):
    # 1. Create a session
    session = await SessionRepository.create(
        db=db_session,
        title="Unrelated Science Topic",
    )

    # 2. Ask completely unrelated question
    fake_llm = FakeLLMProvider()
    req = ChatRequest(message="Can you explain how to calculate quantum thermodynamics entropy in physics?")

    response = await AgentService.chat(
        db=db_session,
        session_id=session.id,
        payload=req,
        llm_provider=fake_llm,
    )

    # 3. Verify refusal without hallucinations
    assert response.session_id == session.id
    assert len(response.sources) == 0
    assert STANDARD_REFUSAL_MESSAGE in response.assistant_message.content


@pytest.mark.asyncio
async def test_chat_multi_turn_history_isolation(db_session: AsyncSession):
    # 1. Create two separate sessions
    session_a = await SessionRepository.create(db=db_session, title="Session A (Elena Verna)")
    session_b = await SessionRepository.create(db=db_session, title="Session B (Shreyas Doshi)")

    fake_llm = FakeLLMProvider()

    # Turn 1 on Session A
    req_a1 = ChatRequest(message="What does Elena Verna teach about B2B PLG?")
    resp_a1 = await AgentService.chat(db=db_session, session_id=session_a.id, payload=req_a1, llm_provider=fake_llm)
    assert len(resp_a1.sources) > 0

    # Turn 1 on Session B
    req_b1 = ChatRequest(message="What is Shreyas Doshi's LNO framework?")
    resp_b1 = await AgentService.chat(db=db_session, session_id=session_b.id, payload=req_b1, llm_provider=fake_llm)
    assert len(resp_b1.sources) > 0

    # Verify messages in Session A do not leak into Session B
    msgs_a = await MessageRepository.list_for_session(db=db_session, session_id=session_a.id)
    msgs_b = await MessageRepository.list_for_session(db=db_session, session_id=session_b.id)

    assert len(msgs_a) == 2
    assert len(msgs_b) == 2
    assert all(m.session_id == session_a.id for m in msgs_a)
    assert all(m.session_id == session_b.id for m in msgs_b)


@pytest.mark.asyncio
async def test_chat_nonexistent_session_raises_404(db_session: AsyncSession):
    fake_llm = FakeLLMProvider()
    random_id = uuid.uuid4()
    req = ChatRequest(message="Hello?")

    with pytest.raises(SessionNotFoundException):
        await AgentService.chat(
            db=db_session,
            session_id=random_id,
            payload=req,
            llm_provider=fake_llm,
        )

