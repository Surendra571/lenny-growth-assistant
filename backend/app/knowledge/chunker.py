import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessedChunk(BaseModel):
    chunk_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    episode_id: str
    episode_title: str
    guest_name: str
    chunk_index: int
    text: str
    token_count: int
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptChunker:
    """
    Semantic boundary-aware chunker for conversational transcript text.
    Preserves dialogue context, speaker tags, and prevents mid-sentence fragmentation.
    """

    def __init__(
        self,
        target_chunk_chars: int = 1500,
        overlap_chars: int = 300,
    ):
        self.target_chunk_chars = target_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_transcript(
        self,
        episode_id: str,
        title: str,
        guest_name: str,
        text: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ProcessedChunk]:
        if not text.strip():
            return []

        # Split into natural dialogue segments by double newline
        segments = [s.strip() for s in text.split("\n\n") if s.strip()]
        
        chunks: List[ProcessedChunk] = []
        current_segments: List[str] = []
        current_length = 0
        chunk_idx = 0

        for seg in segments:
            seg_len = len(seg)
            
            # If adding this segment exceeds target and we already have content, finalize chunk
            if current_length + seg_len > self.target_chunk_chars and current_segments:
                chunk_text = "\n\n".join(current_segments)
                chunks.append(
                    ProcessedChunk(
                        episode_id=episode_id,
                        episode_title=title,
                        guest_name=guest_name,
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        token_count=max(1, len(chunk_text.split())),
                        metadata=extra_metadata or {},
                    )
                )
                chunk_idx += 1

                # Carry over last segment for overlap context if available
                if self.overlap_chars > 0 and len(current_segments) > 1:
                    last_seg = current_segments[-1]
                    current_segments = [last_seg, seg]
                    current_length = len(last_seg) + seg_len
                else:
                    current_segments = [seg]
                    current_length = seg_len
            else:
                current_segments.append(seg)
                current_length += seg_len

        # Finalize trailing segment
        if current_segments:
            chunk_text = "\n\n".join(current_segments)
            chunks.append(
                ProcessedChunk(
                    episode_id=episode_id,
                    episode_title=title,
                    guest_name=guest_name,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    token_count=max(1, len(chunk_text.split())),
                    metadata=extra_metadata or {},
                )
            )

        return chunks

