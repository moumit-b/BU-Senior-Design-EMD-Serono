"""Performance tracking models for bidirectional learning."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class QueryType(Enum):
    """Types of queries for performance categorization."""
    CHEMICAL_SEARCH = "chemical_search"
    INHIBITOR_SEARCH = "inhibitor_search"
    CLINICAL_TRIAL = "clinical_trial"
    LITERATURE_SEARCH = "literature_search"
    GENE_LOOKUP = "gene_lookup"
    PROTEIN_INFO = "protein_info"
    GENERAL = "general"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""
    success: bool
    response_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    cache_hit: bool = False


@dataclass
class MCPPerformance:
    """Performance tracking for an MCP server."""
    mcp_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0

    # Performance by query type
    performance_by_type: Dict[QueryType, List[PerformanceMetrics]] = field(default_factory=dict)

    # Recent performance history (last 100 calls)
    recent_metrics: List[PerformanceMetrics] = field(default_factory=list)

    def record_call(self, query_type: QueryType, metrics: PerformanceMetrics):
        """Record a call to this MCP server."""
        self.total_calls += 1
        if metrics.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        self.total_response_time += metrics.response_time_seconds

        if metrics.cache_hit:
            self.cache_hits += 1

        # Track by query type
        if query_type not in self.performance_by_type:
            self.performance_by_type[query_type] = []
        self.performance_by_type[query_type].append(metrics)

        # Keep last 100 in recent metrics
        self.recent_metrics.append(metrics)
        if len(self.recent_metrics) > 100:
            self.recent_metrics.pop(0)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if self.total_calls == 0:
            return 0.0
        return self.total_response_time / self.total_calls

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_calls == 0:
            return 0.0
        return self.cache_hits / self.total_calls

    def get_success_rate_for_type(self, query_type: QueryType) -> float:
        """Get success rate for a specific query type."""
        if query_type not in self.performance_by_type:
            return 0.0

        metrics = self.performance_by_type[query_type]
        if not metrics:
            return 0.0

        successes = sum(1 for m in metrics if m.success)
        return successes / len(metrics)

    def get_avg_time_for_type(self, query_type: QueryType) -> float:
        """Get average response time for a specific query type."""
        if query_type not in self.performance_by_type:
            return 0.0

        metrics = self.performance_by_type[query_type]
        if not metrics:
            return 0.0

        total_time = sum(m.response_time_seconds for m in metrics)
        return total_time / len(metrics)


@dataclass
class PerformanceFeedback:
    """Feedback from MCP layer to Agent layer (Novel Feature #1: Bidirectional Learning)."""
    source: str  # MCP name or "cache" or "error"
    latency_ms: float
    success: bool
    recommendation: str  # Human-readable recommendation for agents
    query_type_performance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPerformance:
    """Performance tracking for an agent."""
    agent_name: str
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_execution_time: float = 0.0

    # Preferred MCPs learned through experience
    preferred_mcps: Dict[QueryType, str] = field(default_factory=dict)

    # MCP usage patterns
    mcp_usage_count: Dict[str, int] = field(default_factory=dict)
    mcp_success_count: Dict[str, int] = field(default_factory=dict)

    def record_query(self, success: bool, execution_time: float):
        """Record a query execution."""
        self.total_queries += 1
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        self.total_execution_time += execution_time

    def record_mcp_usage(self, mcp_name: str, success: bool):
        """Record MCP usage by this agent."""
        if mcp_name not in self.mcp_usage_count:
            self.mcp_usage_count[mcp_name] = 0
            self.mcp_success_count[mcp_name] = 0

        self.mcp_usage_count[mcp_name] += 1
        if success:
            self.mcp_success_count[mcp_name] += 1

    def learn_mcp_preference(self, query_type: QueryType, mcp_name: str):
        """Learn which MCP works best for a query type."""
        self.preferred_mcps[query_type] = mcp_name

    def get_preferred_mcp(self, query_type: QueryType) -> Optional[str]:
        """Get learned preference for MCP given query type."""
        return self.preferred_mcps.get(query_type)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries

    @property
    def avg_execution_time(self) -> float:
        """Calculate average execution time."""
        if self.total_queries == 0:
            return 0.0
        return self.total_execution_time / self.total_queries

    def get_mcp_success_rate(self, mcp_name: str) -> float:
        """Get success rate when using a specific MCP."""
        if mcp_name not in self.mcp_usage_count:
            return 0.0

        usage = self.mcp_usage_count[mcp_name]
        if usage == 0:
            return 0.0

        return self.mcp_success_count[mcp_name] / usage
