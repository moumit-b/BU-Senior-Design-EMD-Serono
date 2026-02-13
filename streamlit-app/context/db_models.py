"""
SQLAlchemy Data Models

ORM models for persistent storage of research sessions, entities, queries,
hypotheses, and insights.
"""

import json
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Boolean,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.ext.hybrid import hybrid_property


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class SessionRecord(Base):
    """Research session table."""
    __tablename__ = "sessions"

    # Identity
    session_id = Column(String(100), primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_active = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Research context
    research_goal = Column(Text, default="")
    topic_area = Column(String(100), nullable=True)

    # Session metadata
    metadata_json = Column(JSON, default=dict)

    # Relationships
    entities = relationship("EntityRecord", back_populates="session", cascade="all, delete-orphan")
    queries = relationship("QueryRecord", back_populates="session", cascade="all, delete-orphan")
    hypotheses = relationship("HypothesisRecord", back_populates="session", cascade="all, delete-orphan")
    insights = relationship("InsightRecord", back_populates="session", cascade="all, delete-orphan")
    suggestions = relationship("SuggestionRecord", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.session_id}, user={self.user_id}, goal={self.research_goal[:30]})>"


class EntityRecord(Base):
    """Entity table for drugs, genes, proteins, etc."""
    __tablename__ = "entities"

    # Identity
    entity_id = Column(String(100), primary_key=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # drug, gene, protein, etc.
    name = Column(String(255), nullable=False)
    discovered_at = Column(DateTime, default=datetime.now, nullable=False)
    source_mcp = Column(String(100), nullable=True)

    # Entity data stored as JSON for flexibility
    entity_data_json = Column(JSON, default=dict)

    # Relationship
    session = relationship("SessionRecord", back_populates="entities")

    def __repr__(self):
        return f"<Entity(id={self.entity_id}, type={self.entity_type}, name={self.name})>"


class QueryRecord(Base):
    """Query history table with lineage."""
    __tablename__ = "queries"

    # Identity
    query_id = Column(String(100), primary_key=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # Lineage
    parent_query_id = Column(String(100), nullable=True)
    related_entities_json = Column(JSON, default=list)  # List of entity IDs

    # Execution details
    agents_used_json = Column(JSON, default=list)  # List of agent names
    mcps_used_json = Column(JSON, default=list)  # List of MCP server names
    execution_time = Column(Float, nullable=True)

    # Results
    entities_discovered_json = Column(JSON, default=list)  # New entity IDs
    insights_generated_json = Column(JSON, default=list)  # Insight IDs

    # Relationship
    session = relationship("SessionRecord", back_populates="queries")

    def __repr__(self):
        return f"<Query(id={self.query_id}, text={self.query_text[:30]})>"


class HypothesisRecord(Base):
    """Hypothesis table."""
    __tablename__ = "hypotheses"

    # Identity
    hypothesis_id = Column(String(100), primary_key=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    statement = Column(Text, nullable=False)
    proposed_by = Column(String(100), nullable=False)

    # Status
    proposed_at = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(50), default="proposed")  # proposed, testing, supported, rejected, inconclusive
    confidence = Column(Float, default=0.5)

    # Evidence
    supporting_evidence_json = Column(JSON, default=list)
    contradicting_evidence_json = Column(JSON, default=list)

    # Related entities
    related_entities_json = Column(JSON, default=list)

    # Relationship
    session = relationship("SessionRecord", back_populates="hypotheses")

    def __repr__(self):
        return f"<Hypothesis(id={self.hypothesis_id}, status={self.status})>"


class InsightRecord(Base):
    """Insight table."""
    __tablename__ = "insights"

    # Identity
    insight_id = Column(String(100), primary_key=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    insight_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    discovered_by = Column(String(100), nullable=False)

    # Metadata
    discovered_at = Column(DateTime, default=datetime.now, nullable=False)
    confidence = Column(Float, default=0.5)

    # Related data
    related_entities_json = Column(JSON, default=list)
    supporting_data_json = Column(JSON, default=dict)

    # Relationship
    session = relationship("SessionRecord", back_populates="insights")

    def __repr__(self):
        return f"<Insight(id={self.insight_id}, type={self.insight_type})>"


class SuggestionRecord(Base):
    """Proactive suggestion table."""
    __tablename__ = "suggestions"

    # Identity
    suggestion_id = Column(String(100), primary_key=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    suggestion_text = Column(Text, nullable=False)
    suggested_at = Column(DateTime, default=datetime.now, nullable=False)
    priority = Column(Integer, default=1)

    # Metadata
    rationale = Column(Text, default="")
    related_entities_json = Column(JSON, default=list)

    # Relationship
    session = relationship("SessionRecord", back_populates="suggestions")

    def __repr__(self):
        return f"<Suggestion(id={self.suggestion_id}, priority={self.priority})>"


class AuditLogRecord(Base):
    """Audit log table for governance."""
    __tablename__ = "audit_logs"

    # Identity
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # Context
    session_id = Column(String(100), nullable=True, index=True)
    user_id = Column(String(100), nullable=True, index=True)

    # Action details
    action_type = Column(String(50), nullable=False)  # query, mcp_call, agent_action
    actor = Column(String(100), nullable=False)  # agent name or "user"

    # MCP details (if applicable)
    mcp_server = Column(String(100), nullable=True)
    tool_name = Column(String(100), nullable=True)

    # Parameters and results
    parameters_json = Column(JSON, nullable=True)
    result_status = Column(String(50), nullable=True)  # success, error
    execution_time = Column(Float, nullable=True)

    # Data lineage
    source_attribution_json = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.log_id}, action={self.action_type}, actor={self.actor})>"


class PerformancePatternRecord(Base):
    """Performance pattern table for bidirectional learning."""
    __tablename__ = "performance_patterns"

    # Identity
    pattern_id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Pattern type
    pattern_type = Column(String(50), nullable=False)  # agent_learning, mcp_learning, cross_layer

    # Context
    agent_name = Column(String(100), nullable=True)
    mcp_server = Column(String(100), nullable=True)
    query_type = Column(String(100), nullable=True)

    # Pattern data
    pattern_data_json = Column(JSON, nullable=False)

    # Performance metrics
    success_rate = Column(Float, nullable=True)
    avg_execution_time = Column(Float, nullable=True)
    usage_count = Column(Integer, default=1)

    def __repr__(self):
        return f"<Pattern(id={self.pattern_id}, type={self.pattern_type})>"
