"""
MCP Orchestrator - Intelligent MCP Server Management

This is the BOTTOM LAYER of dual orchestration that handles:
- Intelligent routing to optimal MCP servers
- Multi-level caching
- Performance tracking & learning
- Failover and health monitoring
- Teaching agents about data source quality (Novel Feature 1)

All tool calls are now mediated through the Context Forge Gateway for
governance, audit, and compliance (IBM Context Forge pattern).
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from collections import defaultdict

from models.performance import PerformanceFeedback
from utils.cache import MultiLevelCache


def _is_error_result(result: Any) -> bool:
    """Detect error strings returned by MCPToolWrapper.call_tool().

    call_tool() catches all exceptions and returns strings like
    "Error calling tool foo: ..." or "Error: MCP session not initialized".
    These must not be treated as successful data.
    """
    if isinstance(result, str):
        return result.startswith("Error ") or result.startswith("Error:")
    return False


# ---------------------------------------------------------------------------
# Internal performance tracker (lightweight, matches orchestrator's usage)
# ---------------------------------------------------------------------------

@dataclass
class _MCPTracker:
    """Internal performance tracking for a single MCP server."""
    mcp_name: str
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    query_type_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class MCPOrchestrator:
    """
    Intelligent MCP Server Orchestrator

    Novel Feature: Learns from agent query patterns and provides feedback
    to improve agent-MCP matching.

    Gateway Integration: All tool execution now flows through the
    ContextForgeGateway when one is attached (see ``set_gateway``).
    """

    def __init__(self, mcp_wrappers: Dict[str, Any]):
        """
        Initialize MCP Orchestrator.

        Args:
            mcp_wrappers: Dict of {mcp_name: MCPToolWrapper}
        """
        self.mcp_wrappers = mcp_wrappers
        self.cache = MultiLevelCache()

        # Context Forge Gateway (injected after construction)
        self._gateway = None

        # Performance tracking (Novel Feature 1: Bidirectional Learning)
        self.performance_data: Dict[str, _MCPTracker] = {}
        self.query_patterns: Dict[str, List[str]] = defaultdict(list)  # keyword -> [mcp_names]

        # Health monitoring
        self.health_status: Dict[str, bool] = {name: True for name in mcp_wrappers.keys()}
        self.circuit_breaker: Dict[str, int] = {name: 0 for name in mcp_wrappers.keys()}
        self._circuit_tripped_at: Dict[str, Optional[float]] = {name: None for name in mcp_wrappers.keys()}

        # Initialize performance tracking for each MCP
        for mcp_name in mcp_wrappers.keys():
            self.performance_data[mcp_name] = _MCPTracker(mcp_name=mcp_name)

        # Build tool_name -> [server_names] index from wrapper tool caches
        self._tool_to_servers: Dict[str, List[str]] = {}
        for server_name, wrapper in mcp_wrappers.items():
            for mcp_tool in getattr(wrapper, "_tools_cache", []):
                tool_name = getattr(mcp_tool, "name", str(mcp_tool))
                self._tool_to_servers.setdefault(tool_name, []).append(server_name)

    def set_gateway(self, gateway):
        """Attach a ContextForgeGateway to mediate all tool calls."""
        self._gateway = gateway

    # ------------------------------------------------------------------
    # Tool discovery helpers
    # ------------------------------------------------------------------

    def get_available_tools_for_server(self, server_name: str) -> List[str]:
        """Return tool names available on a specific server."""
        return [t for t, servers in self._tool_to_servers.items() if server_name in servers]

    def get_all_tool_names(self) -> List[str]:
        """Return all tool names across all connected servers."""
        return list(self._tool_to_servers.keys())

    # ------------------------------------------------------------------
    # Core routing
    # ------------------------------------------------------------------

    async def route_tool_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, PerformanceFeedback]:
        """
        Route a tool call to the optimal MCP server.

        Args:
            tool_name: Name of the tool to call
            params: Tool parameters
            context: Optional context including agent_id, query_type, keywords

        Returns:
            Tuple of (result, performance_feedback)
        """
        context = context or {}
        agent_id = context.get('agent_id', 'unknown')
        query_type = context.get('query_type', 'general')
        keywords = context.get('keywords', [])

        # Check L1 cache first
        cache_key = self._make_cache_key(tool_name, params)
        cached_result = self.cache.get(cache_key, level=1)
        if cached_result is not None:
            return cached_result, PerformanceFeedback(
                source='cache',
                latency_ms=0,
                success=True,
                recommendation="Cache hit - no MCP call needed"
            )

        # Select optimal MCP based on learning
        mcp_name = self._select_optimal_mcp(tool_name, query_type, keywords, agent_id)

        if not mcp_name:
            return None, PerformanceFeedback(
                source='error',
                latency_ms=0,
                success=False,
                recommendation=f"No MCP server found with tool '{tool_name}'"
            )

        # Execute tool call with performance tracking
        start_time = time.time()
        try:
            result = await self._call_mcp_tool(mcp_name, tool_name, params, context)
            latency_ms = (time.time() - start_time) * 1000
            success = result is not None and not _is_error_result(result)

            # Record performance
            self._record_performance(mcp_name, query_type, latency_ms, success, keywords)

            # Cache result
            if success:
                self.cache.set(cache_key, result, level=1, ttl=60)

            # Generate feedback for agent layer
            feedback = self._generate_feedback(mcp_name, query_type, latency_ms, success)

            return result, feedback

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_performance(mcp_name, query_type, latency_ms, False, keywords)

            feedback = PerformanceFeedback(
                source=mcp_name,
                latency_ms=latency_ms,
                success=False,
                recommendation=f"Error: {str(e)}. Consider alternative MCP."
            )

            return None, feedback

    def _select_optimal_mcp(
        self,
        tool_name: str,
        query_type: str,
        keywords: List[str],
        agent_id: str
    ) -> Optional[str]:
        """
        Select the optimal MCP based on learned patterns.

        Only considers servers that actually have the requested tool.
        """
        # Only consider servers that actually expose this tool AND are healthy
        candidate_servers = self._tool_to_servers.get(tool_name, [])
        candidate_mcps = []
        for s in candidate_servers:
            if self.health_status.get(s, False):
                candidate_mcps.append(s)
            else:
                # Auto-reset circuit breaker after 120s cooldown
                tripped_at = self._circuit_tripped_at.get(s)
                if tripped_at is not None and time.time() - tripped_at > 120:
                    self.reset_circuit_breaker(s)
                    candidate_mcps.append(s)

        if not candidate_mcps:
            return None

        # If only one candidate, return it directly
        if len(candidate_mcps) == 1:
            return candidate_mcps[0]

        # Score each candidate based on learned performance
        scores = {}
        for mcp_name in candidate_mcps:
            perf = self.performance_data.get(mcp_name)
            if not perf or perf.total_calls == 0:
                scores[mcp_name] = 0.5  # Neutral score for unknown MCP
                continue

            # Base score: success rate
            base_score = perf.success_count / max(perf.total_calls, 1)

            # Bonus for query type match
            query_type_perf = perf.query_type_performance.get(query_type, {})
            if query_type_perf:
                base_score += 0.2 * (query_type_perf.get('success_rate', 0))

            # Bonus for keyword match (learned pattern)
            for keyword in keywords:
                if mcp_name in self.query_patterns.get(keyword, []):
                    base_score += 0.1

            # Penalty for high latency
            if perf.avg_latency_ms > 5000:  # >5s is slow
                base_score -= 0.2

            scores[mcp_name] = base_score

        # Return MCP with highest score
        return max(scores.items(), key=lambda x: x[1])[0] if scores else candidate_mcps[0]

    async def _call_mcp_tool(
        self,
        mcp_name: str,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Call the MCP tool — routed through the ContextForgeGateway when available.
        """
        # --- Gateway-mediated path (IBM Context Forge) ---
        if self._gateway is not None:
            from governance.gateway import RequestContext

            ctx = context or {}
            request_context = RequestContext(
                user_id=ctx.get("user_id", "system"),
                session_id=ctx.get("session_id", "default"),
                agent_name=ctx.get("agent_id"),
                query_text=ctx.get("query_text"),
            )

            tool_response = await self._gateway.call_tool(
                server=mcp_name,
                tool=tool_name,
                parameters=params,
                context=request_context,
            )

            if not tool_response.success:
                raise RuntimeError(
                    f"Gateway call failed ({mcp_name}/{tool_name}): {tool_response.error}"
                )
            return tool_response.result

        # --- Direct path (fallback / legacy) ---
        wrapper = self.mcp_wrappers.get(mcp_name)
        if not wrapper:
            raise ValueError(f"MCP {mcp_name} not found")

        # Use call_tool_safe to handle cross-event-loop scenarios
        # (e.g., report generation runs on a different loop than MCP sessions)
        result = await wrapper.call_tool_safe(tool_name, params)
        return result

    def _record_performance(
        self,
        mcp_name: str,
        query_type: str,
        latency_ms: float,
        success: bool,
        keywords: List[str]
    ):
        """Record performance data for learning."""
        perf = self.performance_data.get(mcp_name)
        if not perf:
            return

        perf.total_calls += 1
        if success:
            perf.success_count += 1
            for keyword in keywords:
                if mcp_name not in self.query_patterns[keyword]:
                    self.query_patterns[keyword].append(mcp_name)
        else:
            perf.failure_count += 1
            self.circuit_breaker[mcp_name] = self.circuit_breaker.get(mcp_name, 0) + 1
            if self.circuit_breaker[mcp_name] > 20:
                self.health_status[mcp_name] = False
                self._circuit_tripped_at[mcp_name] = time.time()

        # Update running average latency
        perf.avg_latency_ms = (
            (perf.avg_latency_ms * (perf.total_calls - 1) + latency_ms) / perf.total_calls
        )

        # Update query type specific performance
        if query_type not in perf.query_type_performance:
            perf.query_type_performance[query_type] = {
                'count': 0,
                'success_count': 0,
                'avg_latency': 0
            }

        qt_perf = perf.query_type_performance[query_type]
        qt_perf['count'] += 1
        if success:
            qt_perf['success_count'] += 1
        qt_perf['success_rate'] = qt_perf['success_count'] / qt_perf['count']
        qt_perf['avg_latency'] = (
            (qt_perf['avg_latency'] * (qt_perf['count'] - 1) + latency_ms) / qt_perf['count']
        )

    def _generate_feedback(
        self,
        mcp_name: str,
        query_type: str,
        latency_ms: float,
        success: bool
    ) -> PerformanceFeedback:
        """Generate feedback for the agent layer."""
        perf = self.performance_data.get(mcp_name)
        recommendation = ""

        if success and perf:
            qt_success_rate = perf.query_type_performance.get(query_type, {}).get('success_rate', 0)
            if qt_success_rate > 0.8:
                recommendation = f"{mcp_name} is excellent for {query_type} queries (success rate: {qt_success_rate:.0%})"
            else:
                recommendation = f"{mcp_name} worked but success rate for {query_type} is only {qt_success_rate:.0%}"
        else:
            best_alt = None
            best_rate = 0
            for other_mcp, other_perf in self.performance_data.items():
                if other_mcp == mcp_name:
                    continue
                alt_rate = other_perf.query_type_performance.get(query_type, {}).get('success_rate', 0)
                if alt_rate > best_rate:
                    best_rate = alt_rate
                    best_alt = other_mcp

            if best_alt:
                recommendation = f"{mcp_name} failed. Try {best_alt} instead (success rate: {best_rate:.0%} for {query_type})"
            else:
                recommendation = f"{mcp_name} failed. No better alternative found."

        return PerformanceFeedback(
            source=mcp_name,
            latency_ms=latency_ms,
            success=success,
            recommendation=recommendation,
            query_type_performance=perf.query_type_performance.get(query_type, {}) if perf else {}
        )

    def get_performance_insights(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance insights to share with agent layer."""
        insights = {
            'mcp_rankings': {},
            'query_type_recommendations': {},
            'keyword_patterns': dict(self.query_patterns),
            'health_status': dict(self.health_status),
            'tool_index': {t: s for t, s in self._tool_to_servers.items()},
        }

        mcp_scores = []
        for mcp_name, perf in self.performance_data.items():
            if perf.total_calls == 0:
                continue
            score = perf.success_count / perf.total_calls
            mcp_scores.append((mcp_name, score, perf.avg_latency_ms))

        insights['mcp_rankings'] = sorted(mcp_scores, key=lambda x: x[1], reverse=True)

        query_types = set()
        for perf in self.performance_data.values():
            query_types.update(perf.query_type_performance.keys())

        for qt in query_types:
            best_mcp = None
            best_rate = 0
            for mcp_name, perf in self.performance_data.items():
                rate = perf.query_type_performance.get(qt, {}).get('success_rate', 0)
                if rate > best_rate:
                    best_rate = rate
                    best_mcp = mcp_name

            if best_mcp:
                insights['query_type_recommendations'][qt] = {
                    'recommended_mcp': best_mcp,
                    'success_rate': best_rate
                }

        return insights

    def _make_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate cache key from tool call."""
        param_str = json.dumps(params, sort_keys=True)
        return f"{tool_name}:{param_str}"

    def reset_circuit_breaker(self, mcp_name: str):
        """Reset circuit breaker for an MCP (e.g., after maintenance)."""
        self.circuit_breaker[mcp_name] = 0
        self.health_status[mcp_name] = True

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        return self.cache.get_stats()
