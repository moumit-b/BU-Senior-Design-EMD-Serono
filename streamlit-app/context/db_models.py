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


# ---------------------------------------------------------------------------
# New tables: auth, chat history, reports, tool metrics, vector embeddings
# ---------------------------------------------------------------------------

import uuid as _uuid

try:
    from pgvector.sqlalchemy import Vector as _PGVector
    _PGVECTOR_AVAILABLE = True
except ImportError:
    _PGVector = None
    _PGVECTOR_AVAILABLE = False

from sqlalchemy import UniqueConstraint


class UserRecord(Base):
    """User authentication table."""
    __tablename__ = "users"

    user_id = Column(String(100), primary_key=True, default=lambda: str(_uuid.uuid4()))
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(64), nullable=False)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    chat_sessions = relationship("ChatSessionRecord", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("ReportRecord", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.user_id}, username={self.username})>"


class ChatSessionRecord(Base):
    """Persistent chat session (one conversation thread per session)."""
    __tablename__ = "chat_sessions"

    chat_session_id = Column(String(100), primary_key=True, default=lambda: str(_uuid.uuid4()))
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(255), default="New Conversation", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    config_name = Column(String(50), default="standard", nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    user = relationship("UserRecord", back_populates="chat_sessions")
    messages = relationship("ChatMessageRecord", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessageRecord.sequence_number")
    reports = relationship("ReportRecord", back_populates="chat_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.chat_session_id}, title={self.title})>"


class ChatMessageRecord(Base):
    """Individual message within a chat session."""
    __tablename__ = "chat_messages"

    message_id = Column(String(100), primary_key=True, default=lambda: str(_uuid.uuid4()))
    chat_session_id = Column(String(100), ForeignKey("chat_sessions.chat_session_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    steps_json = Column(JSON, nullable=True)  # intermediate agent reasoning steps
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    sequence_number = Column(Integer, nullable=False, default=0)

    session = relationship("ChatSessionRecord", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.message_id}, role={self.role}, seq={self.sequence_number})>"


class ReportRecord(Base):
    """Generated reports linked to a chat session."""
    __tablename__ = "reports"

    report_id = Column(String(100), primary_key=True, default=lambda: str(_uuid.uuid4()))
    chat_session_id = Column(String(100), ForeignKey("chat_sessions.chat_session_id"), nullable=False, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    drug_name = Column(String(255), nullable=False, index=True)
    report_type = Column(String(100), nullable=False)
    content_md = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    chat_session = relationship("ChatSessionRecord", back_populates="reports")
    user = relationship("UserRecord", back_populates="reports")

    def __repr__(self):
        return f"<Report(id={self.report_id}, drug={self.drug_name})>"


class ReportVerificationRecord(Base):
    """Hallucination check results linked to a generated report."""
    __tablename__ = "report_verifications"

    verification_id = Column(String(100), primary_key=True, default=lambda: str(_uuid.uuid4()))
    report_id = Column(String(100), ForeignKey("reports.report_id"), nullable=False, index=True, unique=True)
    total_identifiers = Column(Integer, default=0, nullable=False)
    verified_count = Column(Integer, default=0, nullable=False)
    unverified_count = Column(Integer, default=0, nullable=False)
    hallucination_rate = Column(Float, default=0.0, nullable=False)  # unverified / total
    details_json = Column(JSON, nullable=True)  # full verify_report() output
    verified_at = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<ReportVerification(report={self.report_id}, rate={self.hallucination_rate:.0%})>"


class ToolMetricRecord(Base):
    """Persistent tool call metrics (per tool-agent pair)."""
    __tablename__ = "tool_metrics"

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(200), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    mcp_server = Column(String(100), nullable=True)
    call_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    total_execution_time_ms = Column(Float, default=0.0, nullable=False)
    last_called_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("tool_name", "agent_name", name="uq_tool_agent"),
    )

    def __repr__(self):
        return f"<ToolMetric(tool={self.tool_name}, agent={self.agent_name}, calls={self.call_count})>"


class ChatEmbeddingRecord(Base):
    """Vector embeddings for chat messages (enables semantic search over chat history)."""
    __tablename__ = "chat_embeddings"

    embedding_id = Column(String(100), primary_key=True, default=lambda: str(_uuid.uuid4()))
    chat_session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    # Vector(384) for PostgreSQL + pgvector, Text (JSON) for SQLite fallback
    embedding = Column(_PGVector(384) if _PGVECTOR_AVAILABLE else Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<ChatEmbedding(id={self.embedding_id}, session={self.chat_session_id})>"
