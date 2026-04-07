"""
Base Agent Abstract Class

Defines the interface that all specialized agents must implement.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


@dataclass
class AgentTask:
    """
    Task assigned to an agent by the orchestrator.
    """
    task_id: str
    query: str
    task_type: str  # e.g., "compound_search", "clinical_trial_lookup"
    parameters: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentContext:
    """
    Context provided to agent for task execution.
    """
    session_id: str
    user_id: str
    research_goal: str
    recent_entities: List[Dict[str, Any]] = field(default_factory=list)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    mcp_performance_feedback: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """
    Result returned by an agent after processing a task.
    """
    task_id: str
    agent_name: str
    success: bool
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    # Execution metadata
    execution_time: float = 0.0
    mcps_used: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)

    # Discovered entities
    entities_discovered: List[Dict[str, Any]] = field(default_factory=list)

    # Source attribution for governance
    source_attribution: List[Dict[str, Any]] = field(default_factory=list)

    # Learning feedback for bidirectional learning
    performance_feedback: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.

    Each agent specializes in a specific domain (chemistry, clinical trials, etc.)
    and knows which MCP servers and tools are best for its domain.
    """

    def __init__(self, agent_name: str, mcp_orchestrator, llm=None):
        """
        Initialize base agent.

        Args:
            agent_name: Name of the agent
            mcp_orchestrator: MCP orchestrator instance
            llm: Language model instance (optional, will use factory if not provided)
        """
        self.agent_name = agent_name
        self.mcp_orchestrator = mcp_orchestrator

        # Initialize LLM using factory if not provided
        if llm is None:
            from utils.llm_factory import get_llm
            self.llm = get_llm()
        else:
            self.llm = llm

        # Agent-specific configuration
        self.capabilities = self._define_capabilities()
        self.preferred_mcps = self._define_preferred_mcps()
        self.keywords = self._define_keywords()

        # Performance tracking
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.avg_execution_time = 0.0

    @abstractmethod
    def _define_capabilities(self) -> List[str]:
        """
        Define agent capabilities.

        Returns:
            List of capability strings
        """
        pass

    @abstractmethod
    def _define_preferred_mcps(self) -> List[str]:
        """
        Define preferred MCP servers for this agent.

        Returns:
            List of MCP server names
        """
        pass

    @abstractmethod
    def _define_keywords(self) -> List[str]:
        """
        Define keywords that indicate this agent should handle the query.

        Returns:
            List of keyword strings
        """
        pass

    def can_handle(self, query: str, keywords: Optional[List[str]] = None) -> float:
        """
        Determine if this agent can handle the query.

        Args:
            query: User query
            keywords: Optional list of extracted keywords

        Returns:
            Confidence score (0-1) for handling this query
        """
        query_lower = query.lower()
        keywords_lower = [k.lower() for k in (keywords or [])]

        # Count matching keywords
        matches = 0
        for keyword in self.keywords:
            if keyword.lower() in query_lower or keyword.lower() in keywords_lower:
                matches += 1

        # Calculate confidence
        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.3
        elif matches == 2:
            return 0.6
        elif matches >= 3:
            return 0.9

        return 0.0

    @abstractmethod
    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """
        Process a task assigned by the orchestrator.

        Args:
            task: Task to process
            context: Context for task execution

        Returns:
            AgentResult with results or error
        """
        pass

    def update_performance(self, result: AgentResult):
        """
        Update agent performance metrics.

        Args:
            result: Agent result to learn from
        """
        if result.success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        # Update average execution time
        total_tasks = self.successful_tasks + self.failed_tasks
        self.avg_execution_time = (
            (self.avg_execution_time * (total_tasks - 1) + result.execution_time) / total_tasks
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get agent performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        total_tasks = self.successful_tasks + self.failed_tasks
        success_rate = self.successful_tasks / total_tasks if total_tasks > 0 else 0.0

        return {
            "agent_name": self.agent_name,
            "total_tasks": total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": success_rate,
            "avg_execution_time": self.avg_execution_time,
            "capabilities": self.capabilities,
            "preferred_mcps": self.preferred_mcps
        }

    # ------------------------------------------------------------------
    # MCP tool helpers — used by subclasses to call real MCP tools
    # ------------------------------------------------------------------

    async def _call_mcp_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Any], bool]:
        """Call an MCP tool through the orchestrator with error handling.

        Returns:
            (result_data, success) — result_data is None on failure.
        """
        if self.mcp_orchestrator is None:
            return None, False

        try:
            ctx = dict(context) if context else {}
            ctx.setdefault("agent_id", self.agent_name)
            result, feedback = await self.mcp_orchestrator.route_tool_call(
                tool_name=tool_name,
                params=params,
                context=ctx,
            )
            return result, feedback.success
        except Exception:
            return None, False

    async def _call_mcp_tools_parallel(
        self,
        calls: List[Tuple[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Optional[Any], bool]]:
        """Call multiple MCP tools in parallel.

        Args:
            calls: List of (tool_name, params) tuples.
        Returns:
            List of (result, success) tuples in the same order.
        """
        tasks = [self._call_mcp_tool(name, params, context) for name, params in calls]
        return await asyncio.gather(*tasks)

    def __repr__(self):
        return f"<{self.agent_name}(capabilities={len(self.capabilities)}, tasks={self.successful_tasks + self.failed_tasks})>"
