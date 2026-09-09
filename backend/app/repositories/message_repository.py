import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message


class MessageRepository:
    """
    Data-access repository for Chat Messages.
    Enforces chronological order and strict session boundary filtering.
    """

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[Dict[str, Any]] = None,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
            tool_calls=tool_calls,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @classmethod
    async def list_for_session(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(asc(Message.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        message_id: uuid.UUID,
    ) -> Optional[Message]:
        stmt = select(Message).where(Message.id == message_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def count_for_session(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> int:
        stmt = select(func.count(Message.id)).where(Message.session_id == session_id)
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def delete_for_session(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> int:
        stmt = select(Message).where(Message.session_id == session_id)
        result = await db.execute(stmt)
        messages = result.scalars().all()
        count = len(messages)
        for msg in messages:
            await db.delete(msg)
        await db.commit()
        return count

