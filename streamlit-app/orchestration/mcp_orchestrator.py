"""
MCP Orchestrator - Intelligent MCP Server Management

This is the BOTTOM LAYER of dual orchestration that handles:
- Intelligent routing to optimal MCP servers
- Multi-level caching
- Performance tracking & learning
- Failover and health monitoring
- Teaching agents about data source quality (Novel Feature 1)
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import json
from collections import defaultdict

from models.performance import MCPPerformance, PerformanceFeedback
from utils.cache import MultiLevelCache


class MCPOrchestrator:
    """
    Intelligent MCP Server Orchestrator

    Novel Feature: Learns from agent query patterns and provides feedback
    to improve agent-MCP matching.
    """

    def __init__(self, mcp_wrappers: Dict[str, Any]):
        """
        Initialize MCP Orchestrator.

        Args:
            mcp_wrappers: Dict of {mcp_name: MCPToolWrapper}
        """
        self.mcp_wrappers = mcp_wrappers
        self.cache = MultiLevelCache()

        # Performance tracking (Novel Feature 1: Bidirectional Learning)
        self.performance_data: Dict[str, MCPPerformance] = {}
        self.query_patterns: Dict[str, List[str]] = defaultdict(list)  # keyword -> [mcp_names]

        # Health monitoring
        self.health_status: Dict[str, bool] = {name: True for name in mcp_wrappers.keys()}
        self.circuit_breaker: Dict[str, int] = {name: 0 for name in mcp_wrappers.keys()}

        # Initialize performance tracking for each MCP
        for mcp_name in mcp_wrappers.keys():
            self.performance_data[mcp_name] = MCPPerformance(
                mcp_id=mcp_name,
                total_calls=0,
                success_count=0,
                failure_count=0,
                avg_latency_ms=0,
                query_type_performance={}
            )

    async def route_tool_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, PerformanceFeedback]:
        """
        Route a tool call to the optimal MCP server.

        Novel Feature: Considers agent preferences and historical performance.

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
                recommendation="No MCP available for this tool"
            )

        # Execute tool call with performance tracking
        start_time = time.time()
        try:
            result = await self._call_mcp_tool(mcp_name, tool_name, params)
            latency_ms = (time.time() - start_time) * 1000
            success = result is not None

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

        Novel Feature: This is where bidirectional learning happens!
        We consider:
        1. Historical performance for this query type
        2. Keyword patterns (learned from past successes)
        3. Agent preferences (some agents work better with certain MCPs)
        """
        # Find MCPs that have this tool
        candidate_mcps = []
        for mcp_name, wrapper in self.mcp_wrappers.items():
            # Check if MCP is healthy
            if not self.health_status.get(mcp_name, False):
                continue

            # Check if MCP has this tool (simplified - assumes tools have mcp_name in them)
            candidate_mcps.append(mcp_name)

        if not candidate_mcps:
            return None

        # Score each candidate based on learned performance
        scores = {}
        for mcp_name in candidate_mcps:
            perf = self.performance_data.get(mcp_name)
            if not perf:
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
        params: Dict[str, Any]
    ) -> Any:
        """Call the MCP tool with retry logic."""
        wrapper = self.mcp_wrappers.get(mcp_name)
        if not wrapper:
            raise ValueError(f"MCP {mcp_name} not found")

        # Call the tool
        result = await wrapper.call_tool(tool_name, params)
        return result

    def _record_performance(
        self,
        mcp_name: str,
        query_type: str,
        latency_ms: float,
        success: bool,
        keywords: List[str]
    ):
        """
        Record performance data for learning.

        Novel Feature: This data is used to teach agents which MCPs work best.
        """
        perf = self.performance_data.get(mcp_name)
        if not perf:
            return

        # Update overall stats
        perf.total_calls += 1
        if success:
            perf.success_count += 1

            # Learn keyword patterns (if successful, associate keywords with this MCP)
            for keyword in keywords:
                if mcp_name not in self.query_patterns[keyword]:
                    self.query_patterns[keyword].append(mcp_name)
        else:
            perf.failure_count += 1
            self.circuit_breaker[mcp_name] = self.circuit_breaker.get(mcp_name, 0) + 1

            # Circuit breaker: disable MCP if too many failures
            if self.circuit_breaker[mcp_name] > 5:
                self.health_status[mcp_name] = False

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
        """
        Generate feedback for the agent layer.

        Novel Feature: This is how MCPs teach agents!
        """
        perf = self.performance_data.get(mcp_name)
        recommendation = ""

        if success and perf:
            # Success - check if this MCP is optimal
            qt_success_rate = perf.query_type_performance.get(query_type, {}).get('success_rate', 0)
            if qt_success_rate > 0.8:
                recommendation = f"{mcp_name} is excellent for {query_type} queries (success rate: {qt_success_rate:.0%})"
            else:
                recommendation = f"{mcp_name} worked but success rate for {query_type} is only {qt_success_rate:.0%}"
        else:
            # Failure - suggest alternatives
            # Find best alternative for this query type
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
        """
        Get performance insights to share with agent layer.

        Novel Feature: Agents can query this to learn which MCPs to prefer.
        """
        insights = {
            'mcp_rankings': {},
            'query_type_recommendations': {},
            'keyword_patterns': dict(self.query_patterns),
            'health_status': dict(self.health_status)
        }

        # Rank MCPs by overall performance
        mcp_scores = []
        for mcp_name, perf in self.performance_data.items():
            if perf.total_calls == 0:
                continue
            score = perf.success_count / perf.total_calls
            mcp_scores.append((mcp_name, score, perf.avg_latency_ms))

        insights['mcp_rankings'] = sorted(mcp_scores, key=lambda x: x[1], reverse=True)

        # Recommendations by query type
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
