import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.artifact import ArtifactCreate, ArtifactResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.session import SessionCreate, SessionDetailResponse, SessionResponse, SessionUpdate
from app.schemas.ship30 import Ship30Request, Ship30Response
from app.services.agent_service import AgentService
from app.services.artifact_service import ArtifactService
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: Optional[SessionCreate] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new independent conversational chat session.
    """
    create_data = payload or SessionCreate()
    return await SessionService.create_session(db, create_data)


@router.get("", response_model=List[SessionResponse], status_code=status.HTTP_200_OK)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum sessions to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    List chat sessions ordered by most recent activity (updated_at DESC).
    """
    return await SessionService.list_sessions(db, limit, offset)


@router.get("/{session_id}", response_model=SessionDetailResponse, status_code=status.HTTP_200_OK)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve full session details, message history, and associated artifacts.
    """
    return await SessionService.get_session(db, session_id)


@router.patch("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def update_session(
    session_id: uuid.UUID,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update session title or metadata.
    """
    return await SessionService.update_session(db, session_id, payload)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a session and all its associated messages and artifacts.
    """
    await SessionService.delete_session(db, session_id)


@router.post("/{session_id}/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_session(
    session_id: uuid.UUID,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the Lenny Growth Assistant within an isolated session.
    Retrieves grounded transcript excerpts, applies system prompts and LLM inference,
    persists the conversation turn, and returns citations and grounded answer.
    """
    return await AgentService.chat(db=db, session_id=session_id, payload=payload)


@router.post("/{session_id}/ship30", response_model=Ship30Response, status_code=status.HTTP_200_OK)
async def generate_ship30_essay(
    session_id: uuid.UUID,
    payload: Optional[Ship30Request] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a grounded ~1,250-word Ship 30 for 30 essay synthesized from Lenny's Podcast transcripts.
    """
    req_data = payload or Ship30Request()
    return await AgentService.generate_ship30(db=db, session_id=session_id, payload=req_data)


@router.post("/{session_id}/artifacts", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_session_artifact(
    session_id: uuid.UUID,
    payload: ArtifactCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new artifact associated with a specific session.
    """
    # Enforce session_id from URL
    payload.session_id = session_id
    return await ArtifactService.create_artifact(db, payload)


@router.get("/{session_id}/artifacts", response_model=List[ArtifactResponse], status_code=status.HTTP_200_OK)
async def list_session_artifacts(
    session_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List all artifacts generated within this session.
    """
    return await ArtifactService.list_session_artifacts(db, session_id, limit=limit, offset=offset)
