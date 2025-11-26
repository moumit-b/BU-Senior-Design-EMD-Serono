"""
Session Manager - Research session memory (Novel Feature 8).
Enables collaborative multi-turn research sessions with context.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import uuid
from models.session import (
    ResearchSession,
    QueryContext,
    Hypothesis,
    Insight,
    ProactiveSuggestion,
    HypothesisStatus,
    InsightType,
)
from models.entities import Entity


class SessionManager:
    """
    Manages research sessions with persistent context and memory.
    This enables collaborative, multi-turn research workflows.
    """

    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, ResearchSession] = {}
        self.active_session_by_user: Dict[str, str] = {}  # user_id -> session_id

    def create_session(
        self,
        user_id: str,
        initial_query: Optional[str] = None,
        research_goal: Optional[str] = None,
    ) -> ResearchSession:
        """
        Create a new research session.

        Args:
            user_id: User identifier
            initial_query: Optional initial query
            research_goal: Optional research goal

        Returns:
            Created research session
        """
        session_id = str(uuid.uuid4())

        session = ResearchSession(
            session_id=session_id,
            user_id=user_id,
            research_goal=research_goal or initial_query or "",
        )

        self.sessions[session_id] = session
        self.active_session_by_user[user_id] = session_id

        return session

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Retrieve a session by ID."""
        return self.sessions.get(session_id)

    def get_active_session(self, user_id: str) -> Optional[ResearchSession]:
        """Get the active session for a user."""
        session_id = self.active_session_by_user.get(user_id)
        if session_id:
            return self.sessions.get(session_id)
        return None

    def get_or_create_session(self, user_id: str) -> ResearchSession:
        """Get active session or create a new one."""
        session = self.get_active_session(user_id)
        if not session:
            session = self.create_session(user_id)
        return session

    def add_query_to_session(
        self,
        session_id: str,
        query_text: str,
        parent_query_id: Optional[str] = None,
    ) -> QueryContext:
        """
        Add a query to a session's history.

        Args:
            session_id: Session identifier
            query_text: The query text
            parent_query_id: Optional parent query (for lineage)

        Returns:
            Created query context
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        query_id = str(uuid.uuid4())
        query_context = QueryContext(
            query_id=query_id,
            query_text=query_text,
            parent_query_id=parent_query_id,
        )

        session.add_query(query_context)

        return query_context

    def add_entity_to_session(
        self,
        session_id: str,
        entity: Entity,
    ):
        """Add a discovered entity to the session."""
        session = self.get_session(session_id)
        if session:
            session.add_entity(entity)

    def add_hypothesis_to_session(
        self,
        session_id: str,
        statement: str,
        proposed_by: str,
        confidence: float = 0.5,
        related_entities: List[str] = None,
    ) -> Hypothesis:
        """
        Add a hypothesis to the session.

        Args:
            session_id: Session identifier
            statement: Hypothesis statement
            proposed_by: Who proposed it (agent name or "user")
            confidence: Confidence score (0-1)
            related_entities: Entity IDs related to this hypothesis

        Returns:
            Created hypothesis
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        hypothesis_id = str(uuid.uuid4())
        hypothesis = Hypothesis(
            hypothesis_id=hypothesis_id,
            statement=statement,
            proposed_by=proposed_by,
            confidence=confidence,
            related_entities=related_entities or [],
        )

        session.add_hypothesis(hypothesis)

        return hypothesis

    def update_hypothesis_status(
        self,
        session_id: str,
        hypothesis_id: str,
        status: HypothesisStatus,
        evidence: Optional[str] = None,
    ):
        """Update the status of a hypothesis."""
        session = self.get_session(session_id)
        if not session:
            return

        for hypothesis in session.hypotheses:
            if hypothesis.hypothesis_id == hypothesis_id:
                hypothesis.status = status
                if evidence:
                    if status in [HypothesisStatus.SUPPORTED, HypothesisStatus.TESTING]:
                        hypothesis.supporting_evidence.append(evidence)
                    elif status == HypothesisStatus.REJECTED:
                        hypothesis.contradicting_evidence.append(evidence)
                break

    def add_insight_to_session(
        self,
        session_id: str,
        insight_type: InsightType,
        description: str,
        discovered_by: str,
        confidence: float = 0.5,
        related_entities: List[str] = None,
        supporting_data: Dict[str, Any] = None,
    ) -> Insight:
        """
        Add an insight to the session.

        Args:
            session_id: Session identifier
            insight_type: Type of insight
            description: Insight description
            discovered_by: Who discovered it
            confidence: Confidence score
            related_entities: Related entity IDs
            supporting_data: Supporting data

        Returns:
            Created insight
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        insight_id = str(uuid.uuid4())
        insight = Insight(
            insight_id=insight_id,
            insight_type=insight_type,
            description=description,
            discovered_by=discovered_by,
            confidence=confidence,
            related_entities=related_entities or [],
            supporting_data=supporting_data or {},
        )

        session.add_insight(insight)

        return insight

    def add_suggestion_to_session(
        self,
        session_id: str,
        suggestion_text: str,
        priority: int = 1,
        rationale: str = "",
        related_entities: List[str] = None,
    ) -> ProactiveSuggestion:
        """
        Add a proactive suggestion to the session.

        Args:
            session_id: Session identifier
            suggestion_text: The suggestion
            priority: Priority (1-5, higher is more important)
            rationale: Why this is suggested
            related_entities: Related entity IDs

        Returns:
            Created suggestion
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        suggestion_id = str(uuid.uuid4())
        suggestion = ProactiveSuggestion(
            suggestion_id=suggestion_id,
            suggestion_text=suggestion_text,
            priority=priority,
            rationale=rationale,
            related_entities=related_entities or [],
        )

        session.add_suggestion(suggestion)

        return suggestion

    def generate_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate a summary of a research session.

        Returns:
            Summary dict with key findings, entities, hypotheses, etc.
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Basic stats
        summary = session.get_summary()

        # Add recent activity
        summary["recent_queries"] = [
            {
                "query": q.query_text,
                "timestamp": q.timestamp.isoformat(),
                "entities_found": len(q.entities_discovered),
            }
            for q in session.get_recent_queries(5)
        ]

        # Add key entities
        summary["key_entities"] = [
            {
                "id": entity_id,
                "name": entity.name,
                "type": entity.entity_type.value,
            }
            for entity_id, entity in list(session.entities.items())[:10]
        ]

        # Add active hypotheses
        summary["active_hypotheses"] = [
            {
                "statement": h.statement,
                "confidence": h.confidence,
                "status": h.status.value,
            }
            for h in session.get_active_hypotheses()
        ]

        # Add recent insights
        summary["recent_insights"] = [
            {
                "type": i.insight_type.value,
                "description": i.description,
                "confidence": i.confidence,
            }
            for i in session.insights[-5:]
        ]

        # Add pending suggestions
        summary["suggestions"] = [
            {
                "text": s.suggestion_text,
                "priority": s.priority,
                "rationale": s.rationale,
            }
            for s in sorted(session.suggestions, key=lambda x: x.priority, reverse=True)[:5]
        ]

        return summary

    def detect_session_changes(
        self,
        session_id: str,
        since_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Detect what changed in research landscape since last session.

        Args:
            session_id: Session identifier
            since_days: Number of days to look back

        Returns:
            Dict of changes detected
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        # Calculate time threshold
        threshold = datetime.now() - timedelta(days=since_days)

        changes = {
            "new_entities": [],
            "updated_hypotheses": [],
            "new_insights": [],
            "time_range_days": since_days,
        }

        # Find entities discovered since threshold
        for entity_id, entity in session.entities.items():
            if entity.discovered_at >= threshold:
                changes["new_entities"].append({
                    "name": entity.name,
                    "type": entity.entity_type.value,
                    "discovered": entity.discovered_at.isoformat(),
                })

        # Find hypothesis status changes
        for hypothesis in session.hypotheses:
            if hypothesis.proposed_at >= threshold:
                changes["updated_hypotheses"].append({
                    "statement": hypothesis.statement,
                    "status": hypothesis.status.value,
                    "confidence": hypothesis.confidence,
                })

        # Find new insights
        for insight in session.insights:
            if insight.discovered_at >= threshold:
                changes["new_insights"].append({
                    "type": insight.insight_type.value,
                    "description": insight.description,
                })

        return changes

    def suggest_next_steps(self, session_id: str) -> List[str]:
        """
        Generate proactive suggestions for next research steps.

        Args:
            session_id: Session identifier

        Returns:
            List of suggested next steps
        """
        session = self.get_session(session_id)
        if not session:
            return []

        suggestions = []

        # If there are active hypotheses, suggest testing them
        active_hypotheses = session.get_active_hypotheses()
        if active_hypotheses:
            h = active_hypotheses[0]
            suggestions.append(
                f"Test hypothesis: '{h.statement}' (current confidence: {h.confidence:.0%})"
            )

        # If recent queries found many entities of one type, suggest deeper dive
        recent = session.get_recent_queries(3)
        if recent:
            last_query = recent[-1]
            if len(last_query.entities_discovered) > 3:
                suggestions.append(
                    f"Deep dive into entities discovered in last query (found {len(last_query.entities_discovered)})"
                )

        # If research goal involves comparison, suggest comparative analysis
        if any(word in session.research_goal.lower() for word in ["compare", "versus", "vs", "competitive"]):
            if len(session.entities) >= 2:
                suggestions.append(
                    "Create comparative analysis of discovered entities"
                )

        # Suggest monitoring if session is older than a week
        if (datetime.now() - session.created_at).days >= 7:
            suggestions.append(
                "Check for updates since last session (new trials, papers, etc.)"
            )

        return suggestions[:3]  # Top 3 suggestions

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get overall session statistics."""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(self.active_session_by_user),
            "total_queries": sum(len(s.queries) for s in self.sessions.values()),
            "total_entities": sum(len(s.entities) for s in self.sessions.values()),
            "total_hypotheses": sum(len(s.hypotheses) for s in self.sessions.values()),
        }
