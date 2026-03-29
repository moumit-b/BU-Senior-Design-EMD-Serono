"""
Persistent Session Manager

Drop-in replacement for the in-memory SessionManager using SQLite + ChromaDB.
Implements the "Session-as-Database" pattern from MIT Recursive Language Models research.
"""

import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.session import (
    ResearchSession, QueryContext, Hypothesis, Insight, ProactiveSuggestion,
    HypothesisStatus, InsightType
)
from models.entities import Entity, EntityType
from .database import DatabaseManager
from .db_models import (
    SessionRecord, EntityRecord, QueryRecord, HypothesisRecord,
    InsightRecord, SuggestionRecord
)


class PersistentSessionManager:
    """
    Persistent session manager using SQLite + ChromaDB.

    Drop-in replacement for the in-memory SessionManager with the same interface.
    """

    def __init__(self, db_path: str = "data/sessions.db", vector_store_path: str = "data/chroma"):
        """
        Initialize persistent session manager.

        Args:
            db_path: Path to SQLite database
            vector_store_path: Path to ChromaDB storage
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()
        self.vector_store_path = vector_store_path
        self._vector_store = None

    @property
    def vector_store(self):
        """Lazy-loaded vector store."""
        if self._vector_store is None:
            from .vector_store import VectorStore
            self._vector_store = VectorStore(self.vector_store_path)
        return self._vector_store

        self._vector_store = None

    @property
    def vector_store(self):
        """Lazy-loaded vector store."""
        if self._vector_store is None:
            from .vector_store import VectorStore
            self._vector_store = VectorStore(self.persist_directory if hasattr(self, 'persist_directory') else self.vector_store_path)
        return self._vector_store

    def create_session(
        self,
        user_id: str,
        research_goal: str = "",
        topic_area: Optional[str] = None
    ) -> ResearchSession:
        """
        Create a new research session.

        Args:
            user_id: User identifier
            research_goal: High-level research goal
            topic_area: Topic area (e.g., "oncology")

        Returns:
            New ResearchSession
        """
        session_id = str(uuid.uuid4())

        with self.db_manager.get_session() as db_session:
            # Create session record
            session_record = SessionRecord(
                session_id=session_id,
                user_id=user_id,
                research_goal=research_goal,
                topic_area=topic_area,
                metadata_json={}
            )
            db_session.add(session_record)
            db_session.commit()

        # Return in-memory representation
        return ResearchSession(
            session_id=session_id,
            user_id=user_id,
            research_goal=research_goal,
            topic_area=topic_area
        )

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Load a session from persistent storage.

        Args:
            session_id: Session identifier

        Returns:
            ResearchSession or None if not found
        """
        with self.db_manager.get_session() as db_session:
            session_record = db_session.query(SessionRecord).filter_by(
                session_id=session_id
            ).first()

            if not session_record:
                return None

            # Reconstruct ResearchSession from database
            research_session = ResearchSession(
                session_id=session_record.session_id,
                user_id=session_record.user_id,
                created_at=session_record.created_at,
                last_active=session_record.last_active,
                research_goal=session_record.research_goal,
                topic_area=session_record.topic_area,
                metadata=session_record.metadata_json or {}
            )

            # Load entities
            for entity_record in session_record.entities:
                entity = self._entity_record_to_entity(entity_record)
                research_session.entities[entity.entity_id] = entity

            # Load queries
            for query_record in session_record.queries:
                query = self._query_record_to_query(query_record)
                research_session.queries.append(query)

            # Load hypotheses
            for hypothesis_record in session_record.hypotheses:
                hypothesis = self._hypothesis_record_to_hypothesis(hypothesis_record)
                research_session.hypotheses.append(hypothesis)

            # Load insights
            for insight_record in session_record.insights:
                insight = self._insight_record_to_insight(insight_record)
                research_session.insights.append(insight)

            # Load suggestions
            for suggestion_record in session_record.suggestions:
                suggestion = self._suggestion_record_to_suggestion(suggestion_record)
                research_session.suggestions.append(suggestion)

            return research_session

    def update_session(self, session: ResearchSession) -> None:
        """
        Persist session changes to database.

        Args:
            session: ResearchSession to update
        """
        with self.db_manager.get_session() as db_session:
            # Update session record
            session_record = db_session.query(SessionRecord).filter_by(
                session_id=session.session_id
            ).first()

            if session_record:
                session_record.last_active = datetime.now()
                session_record.research_goal = session.research_goal
                session_record.topic_area = session.topic_area
                session_record.metadata_json = session.metadata
                db_session.commit()

    def add_query(self, session_id: str, query_context: QueryContext) -> None:
        """
        Add a query to the session.

        Args:
            session_id: Session identifier
            query_context: Query context to add
        """
        with self.db_manager.get_session() as db_session:
            query_record = QueryRecord(
                query_id=query_context.query_id,
                session_id=session_id,
                query_text=query_context.query_text,
                timestamp=query_context.timestamp,
                parent_query_id=query_context.parent_query_id,
                related_entities_json=query_context.related_entities,
                agents_used_json=query_context.agents_used,
                mcps_used_json=query_context.mcps_used,
                execution_time=query_context.execution_time,
                entities_discovered_json=query_context.entities_discovered,
                insights_generated_json=query_context.insights_generated
            )
            db_session.add(query_record)

            # Update session last_active
            session_record = db_session.query(SessionRecord).filter_by(
                session_id=session_id
            ).first()
            if session_record:
                session_record.last_active = datetime.now()

            db_session.commit()

        # Add to vector store for semantic search
        self.vector_store.add_query(session_id, query_context)

    def add_entity(self, session_id: str, entity: Entity) -> None:
        """
        Add an entity to the session.

        Args:
            session_id: Session identifier
            entity: Entity to add
        """
        with self.db_manager.get_session() as db_session:
            entity_record = EntityRecord(
                entity_id=entity.entity_id,
                session_id=session_id,
                entity_type=entity.entity_type.value,
                name=entity.name,
                discovered_at=entity.discovered_at,
                source_mcp=entity.source_mcp,
                entity_data_json=entity.metadata
            )
            db_session.add(entity_record)

            # Update session last_active
            session_record = db_session.query(SessionRecord).filter_by(
                session_id=session_id
            ).first()
            if session_record:
                session_record.last_active = datetime.now()

            db_session.commit()

        # Add to vector store
        self.vector_store.add_entity(session_id, entity)

    def add_hypothesis(self, session_id: str, hypothesis: Hypothesis) -> None:
        """
        Add a hypothesis to the session.

        Args:
            session_id: Session identifier
            hypothesis: Hypothesis to add
        """
        with self.db_manager.get_session() as db_session:
            hypothesis_record = HypothesisRecord(
                hypothesis_id=hypothesis.hypothesis_id,
                session_id=session_id,
                statement=hypothesis.statement,
                proposed_by=hypothesis.proposed_by,
                proposed_at=hypothesis.proposed_at,
                status=hypothesis.status.value,
                confidence=hypothesis.confidence,
                supporting_evidence_json=hypothesis.supporting_evidence,
                contradicting_evidence_json=hypothesis.contradicting_evidence,
                related_entities_json=hypothesis.related_entities
            )
            db_session.add(hypothesis_record)

            # Update session last_active
            session_record = db_session.query(SessionRecord).filter_by(
                session_id=session_id
            ).first()
            if session_record:
                session_record.last_active = datetime.now()

            db_session.commit()

    def add_insight(self, session_id: str, insight: Insight) -> None:
        """
        Add an insight to the session.

        Args:
            session_id: Session identifier
            insight: Insight to add
        """
        with self.db_manager.get_session() as db_session:
            insight_record = InsightRecord(
                insight_id=insight.insight_id,
                session_id=session_id,
                insight_type=insight.insight_type.value,
                description=insight.description,
                discovered_by=insight.discovered_by,
                discovered_at=insight.discovered_at,
                confidence=insight.confidence,
                related_entities_json=insight.related_entities,
                supporting_data_json=insight.supporting_data
            )
            db_session.add(insight_record)

            # Update session last_active
            session_record = db_session.query(SessionRecord).filter_by(
                session_id=session_id
            ).first()
            if session_record:
                session_record.last_active = datetime.now()

            db_session.commit()

        # Add to vector store
        self.vector_store.add_insight(session_id, insight)

    def add_suggestion(self, session_id: str, suggestion: ProactiveSuggestion) -> None:
        """
        Add a proactive suggestion to the session.

        Args:
            session_id: Session identifier
            suggestion: Suggestion to add
        """
        with self.db_manager.get_session() as db_session:
            suggestion_record = SuggestionRecord(
                suggestion_id=suggestion.suggestion_id,
                session_id=session_id,
                suggestion_text=suggestion.suggestion_text,
                suggested_at=suggestion.suggested_at,
                priority=suggestion.priority,
                rationale=suggestion.rationale,
                related_entities_json=suggestion.related_entities
            )
            db_session.add(suggestion_record)
            db_session.commit()

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session summary statistics.

        Args:
            session_id: Session identifier

        Returns:
            Summary dictionary or None
        """
        session = self.get_session(session_id)
        return session.get_summary() if session else None

    def list_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List all sessions for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        with self.db_manager.get_session() as db_session:
            sessions = db_session.query(SessionRecord).filter_by(
                user_id=user_id
            ).order_by(
                SessionRecord.last_active.desc()
            ).limit(limit).all()

            return [{
                "session_id": s.session_id,
                "research_goal": s.research_goal,
                "created_at": s.created_at.isoformat(),
                "last_active": s.last_active.isoformat(),
                "topic_area": s.topic_area
            } for s in sessions]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all related data.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        with self.db_manager.get_session() as db_session:
            session_record = db_session.query(SessionRecord).filter_by(
                session_id=session_id
            ).first()

            if not session_record:
                return False

            db_session.delete(session_record)
            db_session.commit()

        # Delete from vector store
        self.vector_store.delete_session(session_id)
        return True

    # Helper methods for converting database records to domain models

    def _entity_record_to_entity(self, record: EntityRecord) -> Entity:
        """Convert EntityRecord to Entity."""
        return Entity(
            entity_id=record.entity_id,
            entity_type=EntityType(record.entity_type),
            name=record.name,
            discovered_at=record.discovered_at,
            metadata=record.entity_data_json or {},
            source_mcp=record.source_mcp
        )

    def _query_record_to_query(self, record: QueryRecord) -> QueryContext:
        """Convert QueryRecord to QueryContext."""
        return QueryContext(
            query_id=record.query_id,
            query_text=record.query_text,
            timestamp=record.timestamp,
            parent_query_id=record.parent_query_id,
            related_entities=record.related_entities_json or [],
            agents_used=record.agents_used_json or [],
            mcps_used=record.mcps_used_json or [],
            execution_time=record.execution_time,
            entities_discovered=record.entities_discovered_json or [],
            insights_generated=record.insights_generated_json or []
        )

    def _hypothesis_record_to_hypothesis(self, record: HypothesisRecord) -> Hypothesis:
        """Convert HypothesisRecord to Hypothesis."""
        return Hypothesis(
            hypothesis_id=record.hypothesis_id,
            statement=record.statement,
            proposed_by=record.proposed_by,
            proposed_at=record.proposed_at,
            status=HypothesisStatus(record.status),
            confidence=record.confidence,
            supporting_evidence=record.supporting_evidence_json or [],
            contradicting_evidence=record.contradicting_evidence_json or [],
            related_entities=record.related_entities_json or []
        )

    def _insight_record_to_insight(self, record: InsightRecord) -> Insight:
        """Convert InsightRecord to Insight."""
        return Insight(
            insight_id=record.insight_id,
            insight_type=InsightType(record.insight_type),
            description=record.description,
            discovered_by=record.discovered_by,
            discovered_at=record.discovered_at,
            confidence=record.confidence,
            related_entities=record.related_entities_json or [],
            supporting_data=record.supporting_data_json or {}
        )

    def _suggestion_record_to_suggestion(self, record: SuggestionRecord) -> ProactiveSuggestion:
        """Convert SuggestionRecord to ProactiveSuggestion."""
        return ProactiveSuggestion(
            suggestion_id=record.suggestion_id,
            suggestion_text=record.suggestion_text,
            suggested_at=record.suggested_at,
            priority=record.priority,
            rationale=record.rationale,
            related_entities=record.related_entities_json or []
        )
