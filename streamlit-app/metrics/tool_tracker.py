"""
Tool Metrics Tracker

Persistently records tool call counts, success rates, and latencies
for every agent-tool pair. Data is stored in the tool_metrics database
table and survives application restarts.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ToolMetricsTracker:
    """
    Thread-safe tracker for MCP tool call metrics.

    Usage:
        tracker = ToolMetricsTracker(db_manager)
        tracker.record_call("search_compounds", "ChemicalAgent", "pubchem", True, 320.5)
        metrics = tracker.get_all_metrics()
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def record_call(
        self,
        tool_name: str,
        agent_name: str,
        mcp_server: str,
        success: bool,
        execution_time_ms: float,
    ) -> None:
        """
        Upsert a tool call record (increment counts atomically).

        Safe to call from multiple threads — uses select-for-update pattern.
        Silently ignores DB errors so metrics never break the main flow.
        """
        try:
            from context.db_models import ToolMetricRecord
            with self.db.get_session() as session:
                record = (
                    session.query(ToolMetricRecord)
                    .filter_by(tool_name=tool_name, agent_name=agent_name)
                    .with_for_update()
                    .first()
                )
                if record:
                    record.call_count += 1
                    record.success_count += 1 if success else 0
                    record.failure_count += 0 if success else 1
                    record.total_execution_time_ms += execution_time_ms
                    record.last_called_at = datetime.now()
                else:
                    record = ToolMetricRecord(
                        tool_name=tool_name,
                        agent_name=agent_name,
                        mcp_server=mcp_server or "unknown",
                        call_count=1,
                        success_count=1 if success else 0,
                        failure_count=0 if success else 1,
                        total_execution_time_ms=execution_time_ms,
                        last_called_at=datetime.now(),
                    )
                    session.add(record)
        except Exception as e:
            logger.debug(f"ToolMetricsTracker.record_call silenced error: {e}")

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Return all tool metric rows as a list of dicts."""
        try:
            from context.db_models import ToolMetricRecord
            with self.db.get_session() as session:
                records = (
                    session.query(ToolMetricRecord)
                    .order_by(ToolMetricRecord.call_count.desc())
                    .all()
                )
                return [_row_to_dict(r) for r in records]
        except Exception as e:
            logger.warning(f"ToolMetricsTracker.get_all_metrics error: {e}")
            return []

    def get_metrics_by_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """Return metrics filtered by agent name."""
        try:
            from context.db_models import ToolMetricRecord
            with self.db.get_session() as session:
                records = (
                    session.query(ToolMetricRecord)
                    .filter_by(agent_name=agent_name)
                    .order_by(ToolMetricRecord.call_count.desc())
                    .all()
                )
                return [_row_to_dict(r) for r in records]
        except Exception as e:
            logger.warning(f"ToolMetricsTracker.get_metrics_by_agent error: {e}")
            return []

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregate totals across all tools."""
        metrics = self.get_all_metrics()
        if not metrics:
            return {
                "total_calls": 0,
                "total_successes": 0,
                "total_failures": 0,
                "unique_tools": 0,
                "unique_agents": 0,
                "overall_success_rate": 0.0,
            }
        total_calls = sum(m["call_count"] for m in metrics)
        total_successes = sum(m["success_count"] for m in metrics)
        return {
            "total_calls": total_calls,
            "total_successes": total_successes,
            "total_failures": sum(m["failure_count"] for m in metrics),
            "unique_tools": len({m["tool_name"] for m in metrics}),
            "unique_agents": len({m["agent_name"] for m in metrics}),
            "overall_success_rate": round(total_successes / total_calls * 100, 1) if total_calls else 0.0,
        }


def _row_to_dict(r) -> Dict[str, Any]:
    calls = r.call_count or 1
    avg_ms = round(r.total_execution_time_ms / calls, 1)
    success_rate = round((r.success_count / calls) * 100, 1) if calls else 0.0
    return {
        "tool_name": r.tool_name,
        "agent_name": r.agent_name,
        "mcp_server": r.mcp_server or "—",
        "call_count": r.call_count,
        "success_count": r.success_count,
        "failure_count": r.failure_count,
        "success_rate": success_rate,
        "avg_latency_ms": avg_ms,
        "last_called_at": r.last_called_at.strftime("%Y-%m-%d %H:%M") if r.last_called_at else "—",
    }
