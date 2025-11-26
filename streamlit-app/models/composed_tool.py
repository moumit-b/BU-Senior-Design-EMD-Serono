"""Models for dynamic tool composition (Novel Feature 2)."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class ToolStepStatus(Enum):
    """Status of a tool step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ToolStep:
    """A single step in a composed tool workflow."""
    step_id: int
    mcp_name: str
    tool_name: str
    input_template: Dict[str, Any]  # Can reference ${step1.field} syntax

    # Execution details
    status: ToolStepStatus = ToolStepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

    # Optional conditions
    run_if: Optional[str] = None  # e.g., "step1.success == True"


@dataclass
class ComposedTool:
    """A composed tool created by combining multiple MCP calls."""

    # Identity
    name: str
    description: str
    created_by: str  # Agent name that created this
    created_at: datetime = field(default_factory=datetime.now)

    # Workflow definition
    steps: List[ToolStep] = field(default_factory=list)

    # Usage tracking
    times_used: int = 0
    times_succeeded: int = 0
    times_failed: int = 0
    total_execution_time: float = 0.0

    # Caching
    cache_results: bool = True
    cache_ttl: timedelta = field(default_factory=lambda: timedelta(days=7))

    # Metadata
    tags: List[str] = field(default_factory=list)
    example_inputs: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this composed tool."""
        if self.times_used == 0:
            return 0.0
        return self.times_succeeded / self.times_used

    @property
    def avg_execution_time(self) -> float:
        """Calculate average execution time."""
        if self.times_used == 0:
            return 0.0
        return self.total_execution_time / self.times_used

    def record_execution(self, success: bool, execution_time: float):
        """Record an execution of this composed tool."""
        self.times_used += 1
        if success:
            self.times_succeeded += 1
        else:
            self.times_failed += 1
        self.total_execution_time += execution_time


@dataclass
class ToolExecutionResult:
    """Result from executing a composed tool."""
    tool_name: str
    success: bool
    execution_time: float
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    final_result: Optional[Any] = None
    error: Optional[str] = None
    steps_executed: int = 0
    steps_failed: int = 0


@dataclass
class ToolCompositionPattern:
    """A learned pattern of tool composition."""
    pattern_name: str
    query_pattern: str  # Regex or description of when to use this
    recommended_steps: List[Dict[str, str]]  # MCP + tool combinations
    confidence: float  # 0-1 score of pattern effectiveness
    times_suggested: int = 0
    times_accepted: int = 0
