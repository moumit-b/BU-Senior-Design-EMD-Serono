"""Research session models for collaborative research memory (Novel Feature 8)."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from .entities import Entity
from enum import Enum


class HypothesisStatus(Enum):
    """Status of a research hypothesis."""
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class InsightType(Enum):
    """Types of insights discovered during research."""
    PATTERN_DETECTED = "pattern_detected"
    TREND_IDENTIFIED = "trend_identified"
    CONTRADICTION_FOUND = "contradiction_found"
    GAP_DISCOVERED = "gap_discovered"
    OPPORTUNITY = "opportunity"


@dataclass
class QueryContext:
    """Context for a single query in a research session."""
    query_id: str
    query_text: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Lineage - what this query builds upon
    parent_query_id: Optional[str] = None
    related_entities: List[str] = field(default_factory=list)  # Entity IDs

    # Execution details
    agents_used: List[str] = field(default_factory=list)
    mcps_used: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None

    # Results
    entities_discovered: List[str] = field(default_factory=list)  # New entity IDs
    insights_generated: List[str] = field(default_factory=list)  # Insight IDs


@dataclass
class Hypothesis:
    """A research hypothesis formed during a session."""
    hypothesis_id: str
    statement: str
    proposed_by: str  # Agent name or "user"

    proposed_at: datetime = field(default_factory=datetime.now)
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = 0.5  # 0-1 confidence score

    # Evidence
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)

    # Related entities
    related_entities: List[str] = field(default_factory=list)


@dataclass
class Insight:
    """An insight discovered by the system."""
    insight_id: str
    insight_type: InsightType
    description: str
    discovered_by: str  # Agent name or "system"

    discovered_at: datetime = field(default_factory=datetime.now)
    confidence: float = 0.5  # 0-1 confidence score
    related_entities: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProactiveSuggestion:
    """A proactive suggestion for next research steps."""
    suggestion_id: str
    suggestion_text: str
    suggested_at: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1-5, higher is more important

    rationale: str = ""  # Why this is suggested
    related_entities: List[str] = field(default_factory=list)


@dataclass
class ResearchSession:
    """
    A complete research session with context and memory.
    This enables collaborative multi-turn research (Novel Feature 8).
    """

    # Identity
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    # Research context
    research_goal: str = ""  # High-level goal (e.g., "Find BRCA1 inhibitors")
    topic_area: Optional[str] = None  # e.g., "oncology", "neurology"

    # Discovered entities
    entities: Dict[str, Entity] = field(default_factory=dict)  # entity_id -> Entity

    # Hypotheses formed
    hypotheses: List[Hypothesis] = field(default_factory=list)

    # Insights discovered
    insights: List[Insight] = field(default_factory=list)

    # Query history with lineage
    queries: List[QueryContext] = field(default_factory=list)

    # Proactive suggestions
    suggestions: List[ProactiveSuggestion] = field(default_factory=list)

    # Agent activity timeline (for visualization)
    agent_timeline: List[Dict[str, Any]] = field(default_factory=list)

    # Session metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_query(self, query_context: QueryContext):
        """Add a query to the session history."""
        self.queries.append(query_context)
        self.last_active = datetime.now()

    def add_entity(self, entity: Entity):
        """Add a discovered entity to the session."""
        self.entities[entity.entity_id] = entity
        self.last_active = datetime.now()

    def add_hypothesis(self, hypothesis: Hypothesis):
        """Add a hypothesis to the session."""
        self.hypotheses.append(hypothesis)
        self.last_active = datetime.now()

    def add_insight(self, insight: Insight):
        """Add an insight to the session."""
        self.insights.append(insight)
        self.last_active = datetime.now()

    def add_suggestion(self, suggestion: ProactiveSuggestion):
        """Add a proactive suggestion."""
        self.suggestions.append(suggestion)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self.entities.get(entity_id)

    def get_recent_queries(self, limit: int = 5) -> List[QueryContext]:
        """Get the most recent queries."""
        return self.queries[-limit:] if len(self.queries) >= limit else self.queries

    def get_active_hypotheses(self) -> List[Hypothesis]:
        """Get hypotheses that are still being tested or proposed."""
        return [
            h for h in self.hypotheses
            if h.status in [HypothesisStatus.PROPOSED, HypothesisStatus.TESTING]
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the research session."""
        return {
            "session_id": self.session_id,
            "goal": self.research_goal,
            "duration_hours": (datetime.now() - self.created_at).total_seconds() / 3600,
            "total_queries": len(self.queries),
            "entities_discovered": len(self.entities),
            "hypotheses_formed": len(self.hypotheses),
            "insights_generated": len(self.insights),
            "active_hypotheses": len(self.get_active_hypotheses()),
            "pending_suggestions": len([s for s in self.suggestions if not s.related_entities]),
        }
