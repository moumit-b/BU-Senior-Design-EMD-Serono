"""
Audit Logger

Immutable audit trail for all MCP tool calls and agent actions.
Stores logs in SQLite for 90-day hot storage + compliance retention.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from context.database import DatabaseManager
from context.db_models import AuditLogRecord

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logging system for governance.

    Logs:
    - User interactions
    - Agent actions
    - MCP tool calls (request + response)
    - Data lineage
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        """Initialize audit logger with graceful DB fallback."""
        self._db_available = False
        try:
            self.db_manager = DatabaseManager(db_path)
            self.db_manager.initialize()
            self._db_available = True
        except Exception as e:
            logger.warning("AuditLogger: database unavailable (%s) — running in-memory only", e)
            self.db_manager = None

        # In-memory fallback when DB is unavailable
        self._memory_log: List[Dict[str, Any]] = []

    def log_request(
        self,
        user_id: str,
        session_id: str,
        agent_name: Optional[str],
        mcp_server: str,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Optional[int]:
        """
        Log MCP tool request.

        Returns:
            Audit log ID (or None if DB is unavailable).
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_id": user_id,
            "action_type": "mcp_call",
            "actor": agent_name or "user",
            "mcp_server": mcp_server,
            "tool_name": tool_name,
            "parameters": parameters,
            "result_status": "pending",
        }

        if self._db_available:
            try:
                with self.db_manager.get_session() as session:
                    audit_log = AuditLogRecord(
                        timestamp=datetime.now(),
                        session_id=session_id,
                        user_id=user_id,
                        action_type="mcp_call",
                        actor=agent_name or "user",
                        mcp_server=mcp_server,
                        tool_name=tool_name,
                        parameters_json=parameters,
                        result_status="pending",
                    )
                    session.add(audit_log)
                    session.commit()
                    return audit_log.log_id
            except Exception as e:
                logger.warning("AuditLogger.log_request DB write failed: %s", e)

        # Fallback: in-memory
        idx = len(self._memory_log)
        record["log_id"] = idx
        self._memory_log.append(record)
        return idx

    def log_response(
        self,
        audit_log_id: Optional[int],
        success: bool,
        execution_time: float,
        error: Optional[str] = None,
    ):
        """Log MCP tool response. Gracefully handles None audit_log_id."""
        if audit_log_id is None:
            return

        if self._db_available:
            try:
                with self.db_manager.get_session() as session:
                    audit_log = (
                        session.query(AuditLogRecord)
                        .filter_by(log_id=audit_log_id)
                        .first()
                    )
                    if audit_log:
                        audit_log.result_status = "success" if success else "error"
                        audit_log.execution_time = execution_time
                        session.commit()
                        return
            except Exception as e:
                logger.warning("AuditLogger.log_response DB write failed: %s", e)

        # Fallback: update in-memory record
        if 0 <= audit_log_id < len(self._memory_log):
            self._memory_log[audit_log_id]["result_status"] = "success" if success else "error"
            self._memory_log[audit_log_id]["execution_time"] = execution_time
            if error:
                self._memory_log[audit_log_id]["error"] = error

    def get_audit_trail(self, session_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for a session."""
        if self._db_available:
            try:
                with self.db_manager.get_session() as session:
                    logs = (
                        session.query(AuditLogRecord)
                        .filter_by(session_id=session_id)
                        .order_by(AuditLogRecord.timestamp.desc())
                        .all()
                    )
                    return [
                        {
                            "log_id": log.log_id,
                            "timestamp": log.timestamp.isoformat(),
                            "action_type": log.action_type,
                            "actor": log.actor,
                            "mcp_server": log.mcp_server,
                            "tool_name": log.tool_name,
                            "result_status": log.result_status,
                            "execution_time": log.execution_time,
                        }
                        for log in logs
                    ]
            except Exception as e:
                logger.warning("AuditLogger.get_audit_trail DB read failed: %s", e)

        # Fallback: filter in-memory log
        return [
            r for r in self._memory_log if r.get("session_id") == session_id
        ]

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the most recent audit log entries (across all sessions)."""
        if self._db_available:
            try:
                with self.db_manager.get_session() as session:
                    logs = (
                        session.query(AuditLogRecord)
                        .order_by(AuditLogRecord.timestamp.desc())
                        .limit(limit)
                        .all()
                    )
                    return [
                        {
                            "log_id": log.log_id,
                            "timestamp": log.timestamp.isoformat(),
                            "action_type": log.action_type,
                            "actor": log.actor,
                            "mcp_server": log.mcp_server,
                            "tool_name": log.tool_name,
                            "result_status": log.result_status,
                            "execution_time": log.execution_time,
                        }
                        for log in logs
                    ]
            except Exception as e:
                logger.warning("AuditLogger.get_recent_logs DB read failed: %s", e)

        return self._memory_log[-limit:]
