import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.artifact import Artifact


class ArtifactRepository:
    """
    Data access layer for Artifact persistence and session queries.
    """

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        title: str,
        artifact_type: str,
        content: str,
        message_id: Optional[uuid.UUID] = None,
        version: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        artifact = Artifact(
            session_id=session_id,
            message_id=message_id,
            title=title,
            artifact_type=artifact_type,
            content=content,
            version=version,
            artifact_metadata=metadata or {},
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        return artifact

    @classmethod
    async def get_by_id(cls, db: AsyncSession, artifact_id: uuid.UUID) -> Optional[Artifact]:
        stmt = select(Artifact).where(Artifact.id == artifact_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list_for_session(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Artifact]:
        stmt = (
            select(Artifact)
            .where(Artifact.session_id == session_id)
            .order_by(desc(Artifact.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def delete(cls, db: AsyncSession, artifact: Artifact) -> None:
        await db.delete(artifact)
        await db.commit()

