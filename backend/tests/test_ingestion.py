import pytest
from pathlib import Path
import tempfile
import json
from app.knowledge.ingest import IngestionPipeline
from app.knowledge.embeddings import LocalDeterministicEmbeddingProvider


@pytest.mark.asyncio
async def test_ingestion_pipeline_standalone_and_idempotent():
    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir) / "raw"
        raw_dir.mkdir()
        manifest_dir = Path(temp_dir) / "manifests"

        # Create a sample raw transcript
        sample_transcript = {
            "episode_id": "test-ep-01",
            "title": "Finding PMF",
            "guest_name": "Test Guest",
            "transcript_text": "Lenny: How to find PMF?\n\nTest Guest: Use the 40% rule.",
        }
        with open(raw_dir / "ep_01.json", "w", encoding="utf-8") as f:
            json.dump(sample_transcript, f)

        pipeline = IngestionPipeline(
            raw_dir=str(raw_dir),
            manifest_dir=str(manifest_dir),
            embedding_provider=LocalDeterministicEmbeddingProvider(),
        )

        # First run: should process 1 episode
        stats1 = await pipeline.run_ingestion(db=None)
        assert stats1.total_loaded == 1
        assert stats1.processed_episodes == 1
        assert stats1.skipped_unchanged == 0
        assert stats1.chunks_created >= 1
        assert stats1.errors == 0

        # Second run with same unchanged transcript: should skip and not duplicate
        stats2 = await pipeline.run_ingestion(db=None)
        assert stats2.total_loaded == 1
        assert stats2.processed_episodes == 0
        assert stats2.skipped_unchanged == 1
        assert stats2.chunks_created == 0

