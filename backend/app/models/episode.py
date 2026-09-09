import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Integer, JSON, String, Uuid
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

JSON_TYPE = JSON().with_variant(postgresql.JSONB(), "postgresql")


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    guest_role: Mapped[str] = mapped_column(String(255), nullable=True)
    episode_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    publication_date: Mapped[date] = mapped_column(Date, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    episode_metadata: Mapped[dict] = mapped_column("metadata", JSON_TYPE, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    chunks = relationship("TranscriptChunk", back_populates="episode", cascade="all, delete-orphan", order_by="TranscriptChunk.chunk_index")
