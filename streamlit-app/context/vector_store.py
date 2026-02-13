"""
Vector Store using ChromaDB

Provides semantic search over session queries, entities, and insights
for implementing the "Session-as-Database" pattern.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from models.session import QueryContext, Insight
from models.entities import Entity


class VectorStore:
    """
    ChromaDB-based vector store for semantic session memory.

    Enables agents to query their own history semantically rather than
    loading entire conversation logs (solves context rot).
    """

    def __init__(self, persist_directory: str = "data/chroma"):
        """
        Initialize vector store.

        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        self._ensure_directory()

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=False
        ))

        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Create collections
        self.queries_collection = self.client.get_or_create_collection(
            name="queries",
            metadata={"description": "Query history with semantic search"}
        )
        self.entities_collection = self.client.get_or_create_collection(
            name="entities",
            metadata={"description": "Entity descriptions"}
        )
        self.insights_collection = self.client.get_or_create_collection(
            name="insights",
            metadata={"description": "Insights discovered during research"}
        )

    def _ensure_directory(self):
        """Create persist directory if it doesn't exist."""
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

    def add_query(self, session_id: str, query_context: QueryContext) -> None:
        """
        Add a query to the vector store for semantic search.

        Args:
            session_id: Session identifier
            query_context: Query context to add
        """
        # Generate embedding
        embedding = self.embedding_model.encode(query_context.query_text).tolist()

        # Add to collection
        self.queries_collection.add(
            ids=[query_context.query_id],
            embeddings=[embedding],
            documents=[query_context.query_text],
            metadatas=[{
                "session_id": session_id,
                "timestamp": query_context.timestamp.isoformat(),
                "agents_used": ",".join(query_context.agents_used),
                "mcps_used": ",".join(query_context.mcps_used),
                "execution_time": query_context.execution_time or 0.0
            }]
        )

    def add_entity(self, session_id: str, entity: Entity) -> None:
        """
        Add an entity to the vector store.

        Args:
            session_id: Session identifier
            entity: Entity to add
        """
        # Create searchable text from entity
        entity_text = f"{entity.name} ({entity.entity_type.value})"
        if entity.metadata:
            # Add key metadata fields to searchable text
            metadata_str = " ".join([f"{k}:{v}" for k, v in entity.metadata.items()])
            entity_text += f" {metadata_str}"

        # Generate embedding
        embedding = self.embedding_model.encode(entity_text).tolist()

        # Add to collection
        self.entities_collection.add(
            ids=[entity.entity_id],
            embeddings=[embedding],
            documents=[entity_text],
            metadatas=[{
                "session_id": session_id,
                "entity_type": entity.entity_type.value,
                "name": entity.name,
                "source_mcp": entity.source_mcp or ""
            }]
        )

    def add_insight(self, session_id: str, insight: Insight) -> None:
        """
        Add an insight to the vector store.

        Args:
            session_id: Session identifier
            insight: Insight to add
        """
        # Generate embedding
        embedding = self.embedding_model.encode(insight.description).tolist()

        # Add to collection
        self.insights_collection.add(
            ids=[insight.insight_id],
            embeddings=[embedding],
            documents=[insight.description],
            metadatas=[{
                "session_id": session_id,
                "insight_type": insight.insight_type.value,
                "discovered_by": insight.discovered_by,
                "confidence": insight.confidence
            }]
        )

    def search_queries(
        self,
        query: str,
        session_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over query history.

        Args:
            query: Search query
            session_id: Optional session filter
            n_results: Number of results to return

        Returns:
            List of matching queries with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Build where filter
        where_filter = {"session_id": session_id} if session_id else None

        # Search
        results = self.queries_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "query_id": results['ids'][0][i],
                "query_text": results['documents'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None,
                "metadata": results['metadatas'][0][i]
            })

        return formatted_results

    def search_entities(
        self,
        query: str,
        session_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over entities.

        Args:
            query: Search query
            session_id: Optional session filter
            entity_type: Optional entity type filter
            n_results: Number of results to return

        Returns:
            List of matching entities with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Build where filter
        where_filter = {}
        if session_id:
            where_filter["session_id"] = session_id
        if entity_type:
            where_filter["entity_type"] = entity_type

        # Search
        results = self.entities_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "entity_id": results['ids'][0][i],
                "entity_text": results['documents'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None,
                "metadata": results['metadatas'][0][i]
            })

        return formatted_results

    def search_insights(
        self,
        query: str,
        session_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over insights.

        Args:
            query: Search query
            session_id: Optional session filter
            n_results: Number of results to return

        Returns:
            List of matching insights with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Build where filter
        where_filter = {"session_id": session_id} if session_id else None

        # Search
        results = self.insights_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "insight_id": results['ids'][0][i],
                "description": results['documents'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None,
                "metadata": results['metadatas'][0][i]
            })

        return formatted_results

    def delete_session(self, session_id: str) -> None:
        """
        Delete all vectors for a session.

        Args:
            session_id: Session identifier
        """
        # Delete from all collections
        for collection in [self.queries_collection, self.entities_collection, self.insights_collection]:
            # Get all IDs for this session
            results = collection.get(where={"session_id": session_id})
            if results['ids']:
                collection.delete(ids=results['ids'])

    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about vector store collections.

        Returns:
            Dictionary with collection counts
        """
        return {
            "queries": self.queries_collection.count(),
            "entities": self.entities_collection.count(),
            "insights": self.insights_collection.count()
        }
