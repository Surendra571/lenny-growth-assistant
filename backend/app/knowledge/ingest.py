import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.knowledge.chunker import ProcessedChunk, TranscriptChunker
from app.knowledge.cleaner import TranscriptCleaner
from app.knowledge.embeddings import EmbeddingProvider, get_embedding_provider
from app.knowledge.loader import RawTranscript, TranscriptLoader
from app.models.chunk import TranscriptChunk
from app.models.episode import Episode


class IngestionStats(BaseModel):
    total_loaded: int = 0
    processed_episodes: int = 0
    skipped_unchanged: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IngestionPipeline:
    """
    Idempotent ingestion pipeline for Lenny's Podcast transcripts.
    """

    def __init__(
        self,
        raw_dir: str = "data/raw",
        manifest_dir: str = "data/manifests",
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.raw_dir = raw_dir
        self.manifest_dir = manifest_dir
        self.cleaner = TranscriptCleaner()
        self.chunker = TranscriptChunker()
        self.embedder = embedding_provider or get_embedding_provider()

    async def run_ingestion(self, db: Optional[AsyncSession] = None) -> IngestionStats:
        start_time = datetime.now()
        stats = IngestionStats()

        logger.info(f"Starting transcript ingestion from '{self.raw_dir}'...")
        transcripts = TranscriptLoader.load_from_directory(self.raw_dir)
        stats.total_loaded = len(transcripts)

        if not transcripts:
            logger.warning("No raw transcripts found to ingest.")
            stats.duration_seconds = (datetime.now() - start_time).total_seconds()
            return stats

        # Ensure manifest directory exists
        Path(self.manifest_dir).mkdir(parents=True, exist_ok=True)
        manifest_path = Path(self.manifest_dir) / "ingestion_manifest.json"
        
        existing_manifest: Dict[str, Any] = {}
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    existing_manifest = json.load(f)
            except Exception:
                existing_manifest = {}

        manifest_episodes = existing_manifest.get("episodes", {})

        all_processed_chunks: List[ProcessedChunk] = []
        all_embeddings: List[List[float]] = []

        for raw_t in transcripts:
            # Check idempotency hash
            prev_hash = manifest_episodes.get(raw_t.episode_id, {}).get("content_hash")
            if prev_hash == raw_t.content_hash:
                logger.info(f"Skipping unchanged episode: {raw_t.title} ({raw_t.episode_id})")
                stats.skipped_unchanged += 1
                continue

            try:
                # 1. Clean
                cleaned_text = self.cleaner.clean(raw_t.transcript_text)

                # 2. Chunk
                chunks = self.chunker.chunk_transcript(
                    episode_id=raw_t.episode_id,
                    title=raw_t.title,
                    guest_name=raw_t.guest_name,
                    text=cleaned_text,
                    extra_metadata={
                        "episode_url": raw_t.episode_url,
                        "guest_role": raw_t.guest_role,
                        "publication_date": raw_t.publication_date,
                    },
                )

                # 3. Embed
                texts = [c.text for c in chunks]
                embeddings = await self.embedder.embed_batch(texts)

                stats.processed_episodes += 1
                stats.chunks_created += len(chunks)
                stats.embeddings_generated += len(embeddings)

                # 4. Store in Database if session available
                if db is not None:
                    await self._store_episode_and_chunks(db, raw_t, chunks, embeddings)

                # Update manifest record
                manifest_episodes[raw_t.episode_id] = {
                    "title": raw_t.title,
                    "guest_name": raw_t.guest_name,
                    "content_hash": raw_t.content_hash,
                    "chunk_count": len(chunks),
                    "last_ingested": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                logger.error(f"Error ingesting episode '{raw_t.title}': {e}", exc_info=True)
                stats.errors += 1

        # Write updated manifest
        manifest_payload = {
            "version": "1.0.0",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "total_episodes": len(manifest_episodes),
            "episodes": manifest_episodes,
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_payload, f, indent=2)

        stats.duration_seconds = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Ingestion complete: Processed {stats.processed_episodes}, Skipped {stats.skipped_unchanged}, "
            f"Chunks {stats.chunks_created}, Embeddings {stats.embeddings_generated}, Errors {stats.errors} "
            f"in {stats.duration_seconds:.2f}s"
        )
        return stats

    async def _store_episode_and_chunks(
        self,
        db: AsyncSession,
        raw_t: RawTranscript,
        chunks: List[ProcessedChunk],
        embeddings: List[List[float]],
    ):
        # Query existing episode by title or URL
        stmt = select(Episode).where(Episode.title == raw_t.title)
        result = await db.execute(stmt)
        existing_ep = result.scalar_one_or_none()

        if existing_ep:
            # Delete old chunks for clean update
            del_stmt = delete(TranscriptChunk).where(TranscriptChunk.episode_id == existing_ep.id)
            await db.execute(del_stmt)
            ep_id = existing_ep.id
        else:
            ep = Episode(
                title=raw_t.title,
                guest_name=raw_t.guest_name,
                guest_role=raw_t.guest_role,
                episode_url=raw_t.episode_url,
                duration_seconds=raw_t.duration_seconds,
                episode_metadata={"content_hash": raw_t.content_hash, "episode_id": raw_t.episode_id},
            )
            db.add(ep)
            await db.flush()
            ep_id = ep.id

        # Insert chunks
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            db_chunk = TranscriptChunk(
                episode_id=ep_id,
                chunk_index=idx,
                chunk_text=chunk.text,
                token_count=chunk.token_count,
                embedding=emb,
                chunk_metadata=chunk.metadata,
            )
            db.add(db_chunk)

        await db.commit()


async def main():
    """CLI entrypoint for running ingestion."""
    from app.db.session import check_db_health
    
    pipeline = IngestionPipeline()
    db_alive = await check_db_health()

    if db_alive:
        logger.info("PostgreSQL connection confirmed. Ingesting into database & manifest...")
        async with AsyncSessionLocal() as session:
            stats = await pipeline.run_ingestion(db=session)
    else:
        logger.info("PostgreSQL is offline. Ingesting in standalone manifest mode...")
        stats = await pipeline.run_ingestion(db=None)

    print(f"\n====================== INGESTION REPORT ======================")
    print(f"Total Transcripts Loaded:    {stats.total_loaded}")
    print(f"Episodes Processed:          {stats.processed_episodes}")
    print(f"Skipped Unchanged:           {stats.skipped_unchanged}")
    print(f"Total Chunks Created:        {stats.chunks_created}")
    print(f"Total Embeddings Generated:  {stats.embeddings_generated}")
    print(f"Ingestion Errors:            {stats.errors}")
    print(f"Duration:                    {stats.duration_seconds:.2f}s")
    print(f"==============================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
