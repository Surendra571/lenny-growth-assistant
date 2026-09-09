import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message_service import MessageService

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["Messages"])


@router.get("", response_model=List[MessageResponse], status_code=status.HTTP_200_OK)
async def list_messages(
    session_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500, description="Maximum messages to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all messages belonging to a specific session in deterministic chronological order.
    """
    return await MessageService.list_messages_for_session(
        db=db,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    session_id: uuid.UUID,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Persist a message into an existing chat session.
    Validates session boundary and prevents orphan records.
    """
    return await MessageService.create_message(
        db=db,
        session_id=session_id,
        payload=payload,
    )
