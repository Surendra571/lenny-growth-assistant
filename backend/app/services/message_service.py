import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import SessionNotFoundException
from app.repositories.message_repository import MessageRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.message import MessageCreate, MessageResponse


class MessageService:
    """
    Business service coordinating message persistence, validation, and session boundaries.
    """

    @classmethod
    async def create_message(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        payload: MessageCreate,
    ) -> MessageResponse:
        # Verify session existence
        session = await SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundException(str(session_id))

        message = await MessageRepository.create(
            db=db,
            session_id=session_id,
            role=payload.role,
            content=payload.content,
            metadata=payload.metadata,
        )

        return MessageResponse.model_validate(message)

    @classmethod
    async def list_messages_for_session(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MessageResponse]:
        # Verify session existence
        session = await SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundException(str(session_id))

        messages = await MessageRepository.list_for_session(
            db=db,
            session_id=session_id,
            limit=limit,
            offset=offset,
        )

        return [MessageResponse.model_validate(m) for m in messages]

