from app.knowledge.chunker import TranscriptChunker


def test_chunker_creates_deterministic_chunks():
    chunker = TranscriptChunker(target_chunk_chars=300, overlap_chars=50)
    text = (
        "Lenny: Let's talk about PMF.\n\n"
        "Rahul Vohra: Step 1 is segmenting to find your High-Expectation Customer.\n\n"
        "Lenny: What is Step 2?\n\n"
        "Rahul Vohra: Step 2 is analyzing feedback to convert on-the-fence users."
    )

    chunks = chunker.chunk_transcript(
        episode_id="ep-01",
        title="PMF Engine",
        guest_name="Rahul Vohra",
        text=text,
    )

    assert len(chunks) >= 1
    assert chunks[0].episode_id == "ep-01"
    assert chunks[0].guest_name == "Rahul Vohra"
    assert chunks[0].chunk_index == 0
    assert chunks[0].token_count > 0


def test_chunker_handles_empty_text():
    chunker = TranscriptChunker()
    chunks = chunker.chunk_transcript("ep-00", "Empty", "Guest", "")
    assert chunks == []

