import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import ArtifactNotFoundException, SessionNotFoundException
from app.core.security import sanitizer
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.artifact import ArtifactCreate, ArtifactResponse
from app.schemas.ship30 import Ship30Response


class ArtifactService:
    """
    Manages artifact persistence, retrieval, session boundary enforcement, and sanitization.
    """

    @classmethod
    async def create_artifact(
        cls,
        db: AsyncSession,
        payload: ArtifactCreate,
    ) -> ArtifactResponse:
        """
        Create and persist a new artifact within an isolated session with multi-layer sanitization.
        """
        session = await SessionRepository.get_by_id(db, payload.session_id)
        if not session:
            raise SessionNotFoundException(str(payload.session_id))

        # Sanitize HTML content prior to persistence
        sanitized_content = payload.content
        if payload.artifact_type == "html":
            sanitized_content = sanitizer.sanitize_html(payload.content)

        artifact = await ArtifactRepository.create(
            db=db,
            session_id=payload.session_id,
            title=payload.title,
            artifact_type=payload.artifact_type,
            content=sanitized_content,
            message_id=payload.message_id,
            version=payload.version,
            metadata=payload.metadata,
        )
        return ArtifactResponse.model_validate(artifact)

    @classmethod
    async def get_artifact(
        cls,
        db: AsyncSession,
        artifact_id: uuid.UUID,
    ) -> ArtifactResponse:
        """
        Retrieve an artifact by its unique ID.
        """
        artifact = await ArtifactRepository.get_by_id(db, artifact_id)
        if not artifact:
            raise ArtifactNotFoundException(str(artifact_id))
        return ArtifactResponse.model_validate(artifact)

    @classmethod
    async def list_session_artifacts(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ArtifactResponse]:
        """
        List all artifacts associated with a specific session ordered by created_at DESC.
        """
        session = await SessionRepository.get_by_id(db, session_id)
        if not session:
            raise SessionNotFoundException(str(session_id))

        artifacts = await ArtifactRepository.list_for_session(
            db=db,
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        return [ArtifactResponse.model_validate(a) for a in artifacts]

    @classmethod
    async def delete_artifact(
        cls,
        db: AsyncSession,
        artifact_id: uuid.UUID,
    ) -> None:
        """
        Delete an artifact by its ID.
        """
        artifact = await ArtifactRepository.get_by_id(db, artifact_id)
        if not artifact:
            raise ArtifactNotFoundException(str(artifact_id))
        await ArtifactRepository.delete(db, artifact)

    @classmethod
    async def create_from_ship30(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        ship30_res: Ship30Response,
        message_id: Optional[uuid.UUID] = None,
    ) -> ArtifactResponse:
        """
        Helper to convert a generated Ship 30 essay into a persisted Markdown artifact.
        """
        payload = ArtifactCreate(
            session_id=session_id,
            message_id=message_id,
            title=ship30_res.title,
            artifact_type="markdown",
            content=ship30_res.content,
            version=1,
            metadata={
                "skill": "ship30",
                "word_count": ship30_res.word_count,
                "sources": [s.model_dump(mode="json") for s in ship30_res.sources],
            },
        )
        return await cls.create_artifact(db, payload)
