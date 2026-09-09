from abc import ABC, abstractmethod
import math
import re
from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.logging import logger
from app.knowledge.embeddings import EmbeddingProvider, get_embedding_provider
from app.knowledge.loader import TranscriptLoader
from app.models.chunk import TranscriptChunk
from app.models.episode import Episode
from app.schemas.message import SourceCitation


class BaseRetriever(ABC):
    """
    Abstract contract for knowledge retrieval.
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.65,
    ) -> List[SourceCitation]:
        pass


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever combining dense vector semantic similarity with BM25 keyword matching
    and Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        local_raw_dir: str = "data/raw",
    ):
        self.db = db
        self.embedder = embedding_provider or get_embedding_provider()
        self.local_raw_dir = local_raw_dir
        self._in_memory_index: Optional[List[Dict[str, Any]]] = None

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> List[SourceCitation]:
        thresh = similarity_threshold if similarity_threshold is not None else settings.GROUNDING_SIMILARITY_THRESHOLD
        
        if not query or not query.strip():
            return []

        # 1. Generate query embedding
        query_vector = await self.embedder.embed_text(query)

        # 2. If DB session is provided, attempt DB vector retrieval
        if self.db is not None:
            try:
                citations = await self._retrieve_from_db(query, query_vector, limit, thresh)
                if citations:
                    return citations
            except Exception as e:
                logger.warning(f"Database vector retrieval failed ({e}), falling back to memory index.")

        # 3. In-memory fallback hybrid retrieval
        return await self._retrieve_from_memory(query, query_vector, limit, thresh)

    async def _retrieve_from_memory(
        self,
        query: str,
        query_vector: List[float],
        limit: int,
        threshold: float,
    ) -> List[SourceCitation]:
        if self._in_memory_index is None:
            await self._build_in_memory_index()

        if not self._in_memory_index:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        
        # Stopwords to filter out low-entropy query noise
        stopwords = {
            "how", "what", "is", "the", "did", "to", "for", "with", "does", "and",
            "a", "an", "of", "in", "according", "by", "that", "you", "your", "can",
            "tell", "me", "about", "should", "best", "way", "give", "from"
        }
        raw_q_tokens = re.findall(r"\w+", query.lower())
        q_tokens = [t for t in raw_q_tokens if t not in stopwords and len(t) > 2]
        if not q_tokens:
            q_tokens = raw_q_tokens

        scored_candidates = []
        for item in self._in_memory_index:
            c_vec = np.array(item["embedding"], dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            
            # Cosine similarity
            if q_norm > 1e-8 and c_norm > 1e-8:
                cos_sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
            else:
                cos_sim = 0.0

            # Lexical keyword and prefix matching against chunk text, title, and guest name
            target_corpus = f"{item['text']} {item['episode_title']} {item['guest_name']}".lower()
            c_tokens = set(re.findall(r"\w+", target_corpus))
            
            matches = 0
            for qt in q_tokens:
                if any(qt == ct or (len(qt) >= 4 and ct.startswith(qt[:4])) for ct in c_tokens):
                    matches += 1
            keyword_score = matches / max(1, len(q_tokens))

            # Hybrid score (40% dense cosine + 60% keyword overlap)
            hybrid_score = round(0.40 * max(0.0, cos_sim) + 0.60 * min(1.0, keyword_score), 4)

            # Boost score if guest name is in query
            if item["guest_name"].lower() in query.lower():
                hybrid_score = min(1.0, hybrid_score + 0.35)

            # Boost score if title keywords match
            title_tokens = set(re.findall(r"\w+", item["episode_title"].lower()))
            if len(set(q_tokens).intersection(title_tokens)) >= 2:
                hybrid_score = min(1.0, hybrid_score + 0.25)

            if hybrid_score >= threshold:
                scored_candidates.append((hybrid_score, item))

        # Rank descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_k = scored_candidates[:limit]

        citations: List[SourceCitation] = []
        for score, item in top_k:
            snippet = item["text"][:350].strip() + ("..." if len(item["text"]) > 350 else "")
            citations.append(
                SourceCitation(
                    chunk_id=item.get("chunk_id"),
                    episode_title=item["episode_title"],
                    guest_name=item["guest_name"],
                    timestamp=item.get("start_timestamp"),
                    relevance_score=score,
                    snippet=snippet,
                )
            )

        return citations

    async def _build_in_memory_index(self):
        import os
        from pathlib import Path
        from app.knowledge.cleaner import TranscriptCleaner
        from app.knowledge.chunker import TranscriptChunker

        raw_dir = self.local_raw_dir
        if not os.path.exists(raw_dir):
            candidate = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
            if candidate.exists():
                raw_dir = str(candidate)

        transcripts = TranscriptLoader.load_from_directory(raw_dir)
        cleaner = TranscriptCleaner()
        chunker = TranscriptChunker()

        index = []
        for t in transcripts:
            cleaned = cleaner.clean(t.transcript_text)
            chunks = chunker.chunk_transcript(
                episode_id=t.episode_id,
                title=t.title,
                guest_name=t.guest_name,
                text=cleaned,
            )
            texts = [c.text for c in chunks]
            embeddings = await self.embedder.embed_batch(texts)
            for c, emb in zip(chunks, embeddings):
                index.append({
                    "chunk_id": c.chunk_id,
                    "episode_title": t.title,
                    "guest_name": t.guest_name,
                    "text": c.text,
                    "embedding": emb,
                    "start_timestamp": c.start_timestamp,
                })

        self._in_memory_index = index

    async def _retrieve_from_db(
        self,
        query: str,
        query_vector: List[float],
        limit: int,
        threshold: float,
    ) -> List[SourceCitation]:
        # Stopwords to filter out low-entropy query noise
        stopwords = {
            "how", "what", "is", "the", "did", "to", "for", "with", "does", "and",
            "a", "an", "of", "in", "according", "by", "that", "you", "your", "can",
            "tell", "me", "about", "should", "best", "way", "give", "from"
        }
        raw_q_tokens = re.findall(r"\w+", query.lower())
        q_tokens = [t for t in raw_q_tokens if t not in stopwords and len(t) > 2]
        if not q_tokens:
            q_tokens = raw_q_tokens

        # Perform cosine distance query using pgvector operator
        dist_expr = TranscriptChunk.embedding.cosine_distance(query_vector)
        stmt = (
            select(TranscriptChunk, dist_expr.label("distance"))
            .options(selectinload(TranscriptChunk.episode))
            .order_by(dist_expr)
            .limit(limit * 3)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        scored_candidates = []
        for row in rows:
            chunk = row[0]
            distance = float(row[1]) if row[1] is not None else 1.0
            
            # Cosine similarity derived from cosine distance: sim = 1 - distance
            cos_sim = max(0.0, 1.0 - distance)

            episode_title = chunk.episode.title if chunk.episode else "Lenny's Podcast"
            guest_name = chunk.episode.guest_name if chunk.episode else "Guest Speaker"

            # Lexical keyword and prefix matching against chunk text, title, and guest name
            target_corpus = f"{chunk.chunk_text} {episode_title} {guest_name}".lower()
            c_tokens = set(re.findall(r"\w+", target_corpus))
            
            matches = 0
            for qt in q_tokens:
                if any(qt == ct or (len(qt) >= 4 and ct.startswith(qt[:4])) for ct in c_tokens):
                    matches += 1
            keyword_score = matches / max(1, len(q_tokens))

            # Hybrid score (40% dense cosine + 60% keyword overlap)
            hybrid_score = round(0.40 * max(0.0, cos_sim) + 0.60 * min(1.0, keyword_score), 4)

            # Boost score if guest name is in query
            if guest_name.lower() in query.lower():
                hybrid_score = min(1.0, hybrid_score + 0.35)

            # Boost score if title keywords match
            title_tokens = set(re.findall(r"\w+", episode_title.lower()))
            if len(set(q_tokens).intersection(title_tokens)) >= 2:
                hybrid_score = min(1.0, hybrid_score + 0.25)

            # Strict threshold enforcement (exclude sub-threshold chunks)
            if hybrid_score >= threshold:
                scored_candidates.append((hybrid_score, chunk, episode_title, guest_name))

        # Rank descending by true hybrid score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_k = scored_candidates[:limit]

        citations: List[SourceCitation] = []
        for score, chunk, ep_title, g_name in top_k:
            snippet = chunk.chunk_text[:350].strip() + ("..." if len(chunk.chunk_text) > 350 else "")
            citations.append(
                SourceCitation(
                    chunk_id=chunk.id,
                    episode_title=ep_title,
                    guest_name=g_name,
                    timestamp=chunk.start_timestamp,
                    relevance_score=score,
                    snippet=snippet,
                )
            )
        return citations
