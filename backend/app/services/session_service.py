import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import SessionNotFoundException
from app.repositories.session_repository import SessionRepository
from app.schemas.session import SessionCreate, SessionDetailResponse, SessionResponse, SessionUpdate


class SessionService:
    """
    Manages session lifecycle, CRUD operations, and relations.
    """

    @classmethod
    async def create_session(cls, db: AsyncSession, payload: SessionCreate) -> SessionResponse:
        session = await SessionRepository.create(
            db=db,
            title=payload.title,
            metadata=payload.metadata,
            user_id=payload.user_id,
        )
        return SessionResponse.model_validate(session)

    @classmethod
    async def get_session(cls, db: AsyncSession, session_id: uuid.UUID) -> SessionDetailResponse:
        session = await SessionRepository.get_by_id(db, session_id, with_relations=True)
        if not session:
            raise SessionNotFoundException(str(session_id))

        return SessionDetailResponse(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=len(session.messages),
            metadata=session.session_metadata,
            messages=session.messages,
            artifacts=session.artifacts,
        )

    @classmethod
    async def list_sessions(cls, db: AsyncSession, limit: int = 50, offset: int = 0) -> List[SessionResponse]:
        sessions = await SessionRepository.list(db, limit=limit, offset=offset)
        return [SessionResponse.model_validate(s) for s in sessions]

    @classmethod
    async def update_session(cls, db: AsyncSession, session_id: uuid.UUID, payload: SessionUpdate) -> SessionResponse:
        session = await SessionRepository.update(
            db=db,
            session_id=session_id,
            title=payload.title,
            metadata=payload.metadata,
        )
        if not session:
            raise SessionNotFoundException(str(session_id))
        return SessionResponse.model_validate(session)

    @classmethod
    async def delete_session(cls, db: AsyncSession, session_id: uuid.UUID) -> None:
        deleted = await SessionRepository.delete(db, session_id)
        if not deleted:
            raise SessionNotFoundException(str(session_id))
