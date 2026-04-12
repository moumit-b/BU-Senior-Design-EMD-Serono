"""
Chat Vector Store

Provides semantic search over chat history using pgvector (PostgreSQL)
or numpy cosine similarity (SQLite fallback).

Embeddings are generated locally via sentence-transformers (all-MiniLM-L6-v2,
384 dimensions) — no external API calls for embedding generation.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from pgvector.sqlalchemy import Vector
    _PGVECTOR_AVAILABLE = True
except ImportError:
    _PGVECTOR_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


class ChatVectorStore:
    """
    Stores and retrieves chat context embeddings for semantic search.

    Uses PostgreSQL + pgvector when SUPABASE_DB_URL is set.
    Falls back to in-memory numpy similarity for SQLite.
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self._using_postgres = db_manager._using_postgres
        self._model = self._load_embedding_model()

    def _load_embedding_model(self):
        """Load sentence-transformers model with dummy fallback."""
        if not _ST_AVAILABLE:
            return _DummyEmbeddingModel()

        import time
        for attempt in range(3):
            try:
                model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("ChatVectorStore: embedding model loaded")
                return model
            except Exception as e:
                logger.warning(f"Embedding model load attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2)

        logger.error("ChatVectorStore: falling back to dummy embedding model")
        return _DummyEmbeddingModel()

    def _embed(self, text: str) -> List[float]:
        """Generate a 384-dim embedding for the given text."""
        embedding = self._model.encode(text)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return list(embedding)

    def add_chat_context(
        self,
        chat_session_id: str,
        user_id: str,
        user_msg: str,
        assistant_msg: str,
    ) -> None:
        """
        Embed and store a user/assistant exchange for future semantic retrieval.

        Args:
            chat_session_id: The chat session this exchange belongs to
            user_id: The user who sent the message
            user_msg: The user's question/prompt
            assistant_msg: The assistant's response (first 500 chars for embedding)
        """
        combined = f"User: {user_msg}\nAssistant: {assistant_msg[:500]}"
        embedding = self._embed(combined)

        try:
            from .db_models import ChatEmbeddingRecord
            with self.db.get_session() as session:
                if self._using_postgres and _PGVECTOR_AVAILABLE:
                    record = ChatEmbeddingRecord(
                        chat_session_id=chat_session_id,
                        user_id=user_id,
                        content_text=combined,
                        embedding=embedding,
                        timestamp=datetime.now(),
                    )
                else:
                    # SQLite fallback: store embedding as JSON text
                    record = ChatEmbeddingRecord(
                        chat_session_id=chat_session_id,
                        user_id=user_id,
                        content_text=combined,
                        embedding=json.dumps(embedding),
                        timestamp=datetime.now(),
                    )
                session.add(record)
        except Exception as e:
            logger.warning(f"ChatVectorStore.add_chat_context failed: {e}")

    def search_chat_contexts(
        self,
        query: str,
        user_id: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find the most semantically relevant past chat exchanges.

        Args:
            query: The search query (e.g., drug name or research topic)
            user_id: Optional filter — only return results for this user
            n_results: Maximum number of results to return

        Returns:
            List of dicts with keys: content_text, chat_session_id, timestamp, distance
        """
        if self._using_postgres and _PGVECTOR_AVAILABLE:
            return self._search_pgvector(query, user_id, n_results)
        else:
            return self._search_numpy(query, user_id, n_results)

    def _search_pgvector(self, query: str, user_id: Optional[str], n_results: int) -> List[Dict[str, Any]]:
        """Cosine similarity search via pgvector's <=> operator."""
        import numpy as np
        query_vec = self._embed(query)

        try:
            from .db_models import ChatEmbeddingRecord
            with self.db.get_session() as session:
                q = session.query(ChatEmbeddingRecord)
                if user_id:
                    q = q.filter(ChatEmbeddingRecord.user_id == user_id)
                # pgvector cosine distance (lower = more similar)
                q = q.order_by(ChatEmbeddingRecord.embedding.cosine_distance(query_vec))
                rows = q.limit(n_results).all()

                return [
                    {
                        "content_text": r.content_text,
                        "chat_session_id": r.chat_session_id,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.warning(f"ChatVectorStore._search_pgvector failed: {e}")
            return []

    def _search_numpy(self, query: str, user_id: Optional[str], n_results: int) -> List[Dict[str, Any]]:
        """Python-side cosine similarity for SQLite fallback."""
        import numpy as np

        query_vec = np.array(self._embed(query))
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        try:
            from .db_models import ChatEmbeddingRecord
            with self.db.get_session() as session:
                q = session.query(ChatEmbeddingRecord)
                if user_id:
                    q = q.filter(ChatEmbeddingRecord.user_id == user_id)
                rows = q.all()

            scored = []
            for r in rows:
                try:
                    if isinstance(r.embedding, str):
                        vec = np.array(json.loads(r.embedding))
                    else:
                        vec = np.array(r.embedding)
                    norm = np.linalg.norm(vec)
                    if norm == 0:
                        continue
                    similarity = float(np.dot(query_vec, vec) / (query_norm * norm))
                    scored.append((similarity, r))
                except Exception:
                    continue

            scored.sort(key=lambda x: x[0], reverse=True)
            return [
                {
                    "content_text": r.content_text,
                    "chat_session_id": r.chat_session_id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                }
                for _, r in scored[:n_results]
            ]
        except Exception as e:
            logger.warning(f"ChatVectorStore._search_numpy failed: {e}")
            return []


class _DummyEmbeddingModel:
    """Returns random normalized vectors when sentence-transformers is unavailable."""

    def encode(self, text, **kwargs):
        import numpy as np
        vec = np.random.randn(384)
        return vec / np.linalg.norm(vec)
