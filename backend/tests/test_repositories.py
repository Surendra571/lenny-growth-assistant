import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository


@pytest.mark.asyncio
async def test_session_repository_crud(db_session: AsyncSession):
    # 1. Create
    session = await SessionRepository.create(
        db=db_session,
        title="Repo Test Session",
        metadata={"test": True},
    )
    assert session.id is not None
    assert session.title == "Repo Test Session"

    # 2. Get
    fetched = await SessionRepository.get_by_id(db_session, session.id)
    assert fetched is not None
    assert fetched.title == "Repo Test Session"

    # 3. Update
    updated = await SessionRepository.update(
        db_session,
        session.id,
        title="Updated Repo Title",
        metadata={"version": 2},
    )
    assert updated is not None
    assert updated.title == "Updated Repo Title"
    assert updated.session_metadata["version"] == 2

    # 4. Count
    count = await SessionRepository.count(db_session)
    assert count >= 1

    # 5. Delete
    deleted = await SessionRepository.delete(db_session, session.id)
    assert deleted is True
    assert (await SessionRepository.get_by_id(db_session, session.id)) is None


@pytest.mark.asyncio
async def test_message_repository_crud(db_session: AsyncSession):
    session = await SessionRepository.create(db=db_session, title="Message Repo Session")

    # 1. Create Message
    msg1 = await MessageRepository.create(
        db=db_session,
        session_id=session.id,
        role="user",
        content="First message in repo test",
    )
    assert msg1.id is not None
    assert msg1.role == "user"

    msg2 = await MessageRepository.create(
        db=db_session,
        session_id=session.id,
        role="assistant",
        content="Second message in repo test",
    )

    # 2. List
    messages = await MessageRepository.list_for_session(db_session, session.id)
    assert len(messages) == 2
    assert messages[0].content == "First message in repo test"
    assert messages[1].content == "Second message in repo test"

    # 3. Count
    msg_count = await MessageRepository.count_for_session(db_session, session.id)
    assert msg_count == 2

