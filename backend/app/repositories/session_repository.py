import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.session import Session


class SessionRepository:
    """
    Data-access repository for Chat Sessions.
    """

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Session:
        session = Session(
            title=title or "New Conversation",
            user_id=user_id,
            session_metadata=metadata or {},
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        with_relations: bool = False,
    ) -> Optional[Session]:
        stmt = select(Session).where(Session.id == session_id)
        if with_relations:
            stmt = stmt.options(
                selectinload(Session.messages),
                selectinload(Session.artifacts),
            )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Session]:
        stmt = (
            select(Session)
            .order_by(desc(Session.updated_at))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Session]:
        session = await cls.get_by_id(db, session_id)
        if not session:
            return None

        if title is not None:
            session.title = title
        if metadata is not None:
            # Merge or overwrite metadata
            updated_meta = dict(session.session_metadata)
            updated_meta.update(metadata)
            session.session_metadata = updated_meta

        session.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def delete(cls, db: AsyncSession, session_id: uuid.UUID) -> bool:
        session = await cls.get_by_id(db, session_id)
        if not session:
            return False
        await db.delete(session)
        await db.commit()
        return True

    @classmethod
    async def count(cls, db: AsyncSession) -> int:
        stmt = select(func.count(Session.id))
        result = await db.execute(stmt)
        return result.scalar() or 0

