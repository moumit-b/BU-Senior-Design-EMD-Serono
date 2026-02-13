"""
Memory Retriever

Provides query interface for agents to access session history semantically.
Implements the recursive context pattern from MIT RLM research.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .session_db import PersistentSessionManager
from .vector_store import VectorStore


class MemoryRetriever:
    """
    Memory retriever for agents to query session history.

    Instead of injecting entire conversation history into context,
    agents can write queries to retrieve exactly what they need.

    This solves "cognitive context rot" by treating memory as a database.
    """

    def __init__(self, session_manager: PersistentSessionManager):
        """
        Initialize memory retriever.

        Args:
            session_manager: Persistent session manager instance
        """
        self.session_manager = session_manager
        self.vector_store = session_manager.vector_store

    def query_memory(
        self,
        query: str,
        session_id: str,
        time_range: Optional[str] = None,
        memory_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Query session memory semantically.

        Args:
            query: Natural language query
            session_id: Session identifier
            time_range: Time range filter (e.g., "last_hour", "today", "this_week")
            memory_type: Type of memory to search ("queries", "entities", "insights", "all")

        Returns:
            Dictionary with query results

        Example:
            result = retriever.query_memory(
                query="What hypotheses were formed about BRCA1?",
                session_id="session_123",
                time_range="today"
            )
        """
        results = {
            "query": query,
            "session_id": session_id,
            "time_range": time_range,
            "results": {}
        }

        # Search appropriate collections
        if memory_type in ["queries", "all"]:
            query_results = self.vector_store.search_queries(
                query=query,
                session_id=session_id,
                n_results=5
            )
            results["results"]["queries"] = query_results

        if memory_type in ["entities", "all"]:
            entity_results = self.vector_store.search_entities(
                query=query,
                session_id=session_id,
                n_results=5
            )
            results["results"]["entities"] = entity_results

        if memory_type in ["insights", "all"]:
            insight_results = self.vector_store.search_insights(
                query=query,
                session_id=session_id,
                n_results=5
            )
            results["results"]["insights"] = insight_results

        # Apply time range filter if specified
        if time_range:
            results["results"] = self._filter_by_time_range(results["results"], time_range)

        return results

    def get_recent_context(self, session_id: str, n_queries: int = 5) -> Dict[str, Any]:
        """
        Get recent context from session (last N queries).

        Args:
            session_id: Session identifier
            n_queries: Number of recent queries to retrieve

        Returns:
            Dictionary with recent context
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        recent_queries = session.get_recent_queries(limit=n_queries)

        return {
            "session_id": session_id,
            "recent_queries": [
                {
                    "query_id": q.query_id,
                    "query_text": q.query_text,
                    "timestamp": q.timestamp.isoformat(),
                    "agents_used": q.agents_used,
                    "entities_discovered": q.entities_discovered
                }
                for q in recent_queries
            ]
        }

    def get_entity_context(self, session_id: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get all context related to a specific entity.

        Args:
            session_id: Session identifier
            entity_id: Entity identifier

        Returns:
            Dictionary with entity context
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return None

        entity = session.get_entity(entity_id)
        if not entity:
            return None

        # Find related queries
        related_queries = [
            q for q in session.queries
            if entity_id in q.related_entities or entity_id in q.entities_discovered
        ]

        # Find related hypotheses
        related_hypotheses = [
            h for h in session.hypotheses
            if entity_id in h.related_entities
        ]

        # Find related insights
        related_insights = [
            i for i in session.insights
            if entity_id in i.related_entities
        ]

        return {
            "entity": {
                "entity_id": entity.entity_id,
                "name": entity.name,
                "type": entity.entity_type.value,
                "metadata": entity.metadata
            },
            "related_queries": [
                {
                    "query_id": q.query_id,
                    "query_text": q.query_text,
                    "timestamp": q.timestamp.isoformat()
                }
                for q in related_queries
            ],
            "related_hypotheses": [
                {
                    "hypothesis_id": h.hypothesis_id,
                    "statement": h.statement,
                    "status": h.status.value,
                    "confidence": h.confidence
                }
                for h in related_hypotheses
            ],
            "related_insights": [
                {
                    "insight_id": i.insight_id,
                    "description": i.description,
                    "confidence": i.confidence
                }
                for i in related_insights
            ]
        }

    def search_hypotheses(
        self,
        session_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search hypotheses in session.

        Args:
            session_id: Session identifier
            status: Filter by status (proposed, testing, supported, rejected, inconclusive)

        Returns:
            List of matching hypotheses
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return []

        hypotheses = session.hypotheses
        if status:
            hypotheses = [h for h in hypotheses if h.status.value == status]

        return [
            {
                "hypothesis_id": h.hypothesis_id,
                "statement": h.statement,
                "proposed_by": h.proposed_by,
                "status": h.status.value,
                "confidence": h.confidence,
                "proposed_at": h.proposed_at.isoformat()
            }
            for h in hypotheses
        ]

    def get_session_timeline(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session timeline.

        Args:
            session_id: Session identifier

        Returns:
            Timeline of all session activities
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # Build chronological timeline
        timeline = []

        # Add queries
        for query in session.queries:
            timeline.append({
                "type": "query",
                "timestamp": query.timestamp.isoformat(),
                "content": query.query_text,
                "agents_used": query.agents_used
            })

        # Add hypotheses
        for hypothesis in session.hypotheses:
            timeline.append({
                "type": "hypothesis",
                "timestamp": hypothesis.proposed_at.isoformat(),
                "content": hypothesis.statement,
                "status": hypothesis.status.value
            })

        # Add insights
        for insight in session.insights:
            timeline.append({
                "type": "insight",
                "timestamp": insight.discovered_at.isoformat(),
                "content": insight.description,
                "discovered_by": insight.discovered_by
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return {
            "session_id": session_id,
            "timeline": timeline
        }

    def _filter_by_time_range(self, results: Dict[str, List], time_range: str) -> Dict[str, List]:
        """
        Filter results by time range.

        Args:
            results: Results dictionary
            time_range: Time range string

        Returns:
            Filtered results
        """
        now = datetime.now()
        cutoff = None

        if time_range == "last_hour":
            cutoff = now - timedelta(hours=1)
        elif time_range == "today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "this_week":
            cutoff = now - timedelta(days=7)
        elif time_range == "this_month":
            cutoff = now - timedelta(days=30)

        if not cutoff:
            return results

        # Filter each result type
        filtered_results = {}
        for key, items in results.items():
            if not items:
                filtered_results[key] = []
                continue

            filtered_items = []
            for item in items:
                if "metadata" in item and "timestamp" in item["metadata"]:
                    timestamp_str = item["metadata"]["timestamp"]
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp >= cutoff:
                        filtered_items.append(item)
                else:
                    # Include if no timestamp
                    filtered_items.append(item)

            filtered_results[key] = filtered_items

        return filtered_results

    def create_tool(self) -> Dict[str, Any]:
        """
        Create LangChain tool definition for query_memory.

        Returns:
            Tool definition dictionary
        """
        return {
            "name": "query_memory",
            "description": (
                "Query session memory semantically. Instead of reading entire conversation history, "
                "use this to search for specific information from past queries, entities, or insights. "
                "Supports natural language queries and time range filters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier"
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["last_hour", "today", "this_week", "this_month", "all"],
                        "description": "Time range to search within"
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["queries", "entities", "insights", "all"],
                        "description": "Type of memory to search"
                    }
                },
                "required": ["query", "session_id"]
            }
        }
