import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.artifact import ArtifactCreate, ArtifactResponse
from app.services.artifact_service import ArtifactService

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    payload: ArtifactCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Persist and sanitize a generated artifact.
    """
    return await ArtifactService.create_artifact(db, payload)


@router.get("/{artifact_id}", response_model=ArtifactResponse, status_code=status.HTTP_200_OK)
async def get_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve an artifact by its unique ID.
    """
    return await ArtifactService.get_artifact(db, artifact_id)


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an artifact by its unique ID.
    """
    await ArtifactService.delete_artifact(db, artifact_id)


@router.get("/session/{session_id}", response_model=List[ArtifactResponse], status_code=status.HTTP_200_OK)
async def list_session_artifacts(
    session_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List all artifacts generated within a session.
    """
    return await ArtifactService.list_session_artifacts(db, session_id, limit=limit, offset=offset)
