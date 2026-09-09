import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.core.logging import logger


class RawTranscript(BaseModel):
    episode_id: str
    title: str
    guest_name: str
    guest_role: Optional[str] = None
    episode_url: Optional[str] = None
    publication_date: Optional[str] = None
    duration_seconds: Optional[int] = None
    description: Optional[str] = None
    transcript_text: str
    content_hash: str = Field(default="")
    file_path: Optional[str] = None

    def compute_hash(self) -> str:
        """
        Compute SHA-256 content hash of the transcript text and title for idempotency.
        """
        raw = f"{self.title}:{self.guest_name}:{self.transcript_text}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


class TranscriptLoader:
    """
    Scans and loads raw podcast transcripts from local directories or single JSON/Markdown files.
    """

    @classmethod
    def load_from_directory(cls, dir_path: str) -> List[RawTranscript]:
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            logger.warning(f"Transcript directory '{dir_path}' does not exist.")
            return []

        transcripts: List[RawTranscript] = []
        for file in sorted(p.glob("*.json")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    t = RawTranscript(**data, file_path=str(file))
                    t.content_hash = t.compute_hash()
                    transcripts.append(t)
            except Exception as e:
                logger.error(f"Failed to load transcript file {file}: {e}")

        logger.info(f"Loaded {len(transcripts)} raw transcripts from '{dir_path}'")
        return transcripts

    @classmethod
    def load_single_file(cls, file_path: str) -> Optional[RawTranscript]:
        p = Path(file_path)
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                t = RawTranscript(**data, file_path=str(file_path))
                t.content_hash = t.compute_hash()
                return t
        except Exception as e:
            logger.error(f"Failed to load transcript file {file_path}: {e}")
            return None

