"""
Audit Logger

Immutable audit trail for all MCP tool calls and agent actions.
Stores logs in SQLite for 90-day hot storage + compliance retention.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from context.database import DatabaseManager
from context.db_models import AuditLogRecord


class AuditLogger:
    """
    Audit logging system for governance.
    
    Logs:
    - User interactions
    - Agent actions
    - MCP tool calls
    - Data lineage
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        """Initialize audit logger."""
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize()

    def log_request(
        self,
        user_id: str,
        session_id: str,
        agent_name: Optional[str],
        mcp_server: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> int:
        """
        Log MCP tool request.
        
        Returns:
            Audit log ID
        """
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
                result_status="pending"
            )
            session.add(audit_log)
            session.commit()
            return audit_log.log_id

    def log_response(
        self,
        audit_log_id: int,
        success: bool,
        execution_time: float,
        error: Optional[str] = None
    ):
        """Log MCP tool response."""
        with self.db_manager.get_session() as session:
            audit_log = session.query(AuditLogRecord).filter_by(log_id=audit_log_id).first()
            if audit_log:
                audit_log.result_status = "success" if success else "error"
                audit_log.execution_time = execution_time
                session.commit()

    def get_audit_trail(self, session_id: str) -> list:
        """Get audit trail for a session."""
        with self.db_manager.get_session() as session:
            logs = session.query(AuditLogRecord).filter_by(session_id=session_id).all()
            return [
                {
                    "log_id": log.log_id,
                    "timestamp": log.timestamp.isoformat(),
                    "action_type": log.action_type,
                    "actor": log.actor,
                    "mcp_server": log.mcp_server,
                    "tool_name": log.tool_name,
                    "result_status": log.result_status,
                    "execution_time": log.execution_time
                }
                for log in logs
            ]
