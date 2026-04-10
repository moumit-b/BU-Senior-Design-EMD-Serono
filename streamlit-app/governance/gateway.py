"""
Context Forge Gateway

Central gateway implementing IBM Context Forge pattern.
All MCP tool calls flow through this gateway for governance.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from .audit_logger import AuditLogger
from .compliance_engine import ComplianceEngine
from .service_registry import ServiceRegistry
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class RequestContext:
    """Context for a tool request."""
    user_id: str
    session_id: str
    agent_name: Optional[str] = None
    query_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResponse:
    """Response from MCP tool call."""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    mcp_server: str = ""
    tool_name: str = ""
    audit_log_id: Optional[int] = None
    compliance_passed: bool = True
    source_attribution: List[Dict[str, Any]] = field(default_factory=list)


class ContextForgeGateway:
    """
    Central gateway for all MCP server communication.

    Implements IBM Context Forge pattern:
    - Service Discovery: Dynamic tool registry
    - Health Monitoring: Heartbeat checks
    - Audit Logging: Complete audit trail
    - Compliance: Pre/post validation
    - Rate Limiting: Usage quotas
    """

    def __init__(self, db_path: str = "data/sessions.db"):
        """Initialize Context Forge Gateway."""
        self.service_registry = ServiceRegistry()
        self.audit_logger = AuditLogger(db_path)
        self.compliance_engine = ComplianceEngine()
        self.rate_limiter = RateLimiter()

        # MCP wrapper references — populated by register_mcp_wrappers()
        self._mcp_wrappers: Dict[str, Any] = {}

        # Gateway-level statistics
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "compliance_blocks": 0,
            "rate_limit_blocks": 0,
        }

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------

    def register_mcp_wrappers(self, wrappers: Dict[str, Any]):
        """
        Register live MCP wrappers and their tools with the ServiceRegistry.

        Args:
            wrappers: Dict of {server_name: MCPToolWrapper} — each wrapper
                      must already be connected.
        """
        self._mcp_wrappers = wrappers

        for server_name, wrapper in wrappers.items():
            # Build a tool list from the wrapper's cached tool definitions
            tools = []
            for mcp_tool in getattr(wrapper, "_tools_cache", []):
                tools.append({
                    "name": getattr(mcp_tool, "name", str(mcp_tool)),
                    "description": getattr(mcp_tool, "description", ""),
                })

            endpoint = wrapper.server_config.get("command", "stdio")
            self.service_registry.register_service(server_name, endpoint, tools)
            logger.info("Gateway registered MCP server: %s (%d tools)", server_name, len(tools))

    # ------------------------------------------------------------------
    # Core governance flow
    # ------------------------------------------------------------------

    async def call_tool(
        self,
        server: str,
        tool: str,
        parameters: Dict[str, Any],
        context: RequestContext
    ) -> ToolResponse:
        """
        Proxy MCP tool call through governance layer.

        Flow:
        1. Check rate limits
        2. Pre-validation (compliance)
        3. Check service health
        4. Log audit entry
        5. Execute tool call via real MCP wrapper
        6. Post-validation
        7. Log result
        8. Return with source attribution
        """
        start_time = time.time()
        self.stats["total_calls"] += 1

        response = ToolResponse(
            success=False,
            result=None,
            mcp_server=server,
            tool_name=tool,
        )

        try:
            # 1. Rate limiting
            if not self.rate_limiter.check_rate_limit(context.user_id, server):
                response.error = "Rate limit exceeded"
                self.stats["rate_limit_blocks"] += 1
                return response

            # 2. Pre-validation (compliance)
            compliance_result = self.compliance_engine.validate_request(
                server, tool, parameters, context
            )
            if not compliance_result["passed"]:
                response.error = compliance_result["reason"]
                response.compliance_passed = False
                self.stats["compliance_blocks"] += 1
                return response

            # 3. Check service health
            # Refresh the heartbeat before the health check so the heartbeat
            # timeout doesn't create a chicken-and-egg: servers need calls to
            # stay healthy, but unhealthy servers would be rejected here.
            if server in self._mcp_wrappers:
                self.service_registry.update_heartbeat(server)
            if not self.service_registry.is_healthy(server):
                response.error = f"Service '{server}' is unavailable or unhealthy"
                self.stats["failed_calls"] += 1
                return response

            # 4. Audit log (request)
            audit_log_id = None
            try:
                audit_log_id = self.audit_logger.log_request(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    agent_name=context.agent_name,
                    mcp_server=server,
                    tool_name=tool,
                    parameters=parameters,
                )
            except Exception as audit_err:
                logger.warning("Audit log request failed (non-fatal): %s", audit_err)

            # 5. Execute tool call via the real MCP wrapper
            result = await self._execute_tool_call(server, tool, parameters)

            # Detect failure conditions — call_tool() returns error strings
            # instead of raising, and _execute_tool_call() returns stub dicts
            # when no wrapper is registered.
            is_stub = isinstance(result, dict) and result.get("status") == "stub"
            is_error_str = isinstance(result, str) and (
                result.startswith("Error ") or result.startswith("Error:")
            )
            if is_stub or is_error_str:
                response.success = False
                response.result = result
                response.error = (
                    result if is_error_str else result.get("data", "Stub response — no live MCP connection")
                )
                self.stats["failed_calls"] += 1
                return response

            response.success = True
            response.result = result
            response.audit_log_id = audit_log_id
            self.stats["successful_calls"] += 1

            # 6. Post-validation
            post_validation = self.compliance_engine.validate_response(result)
            response.compliance_passed = post_validation["passed"]
            if not post_validation["passed"]:
                response.result = "[REDACTED — compliance post-check failed]"
                response.error = post_validation.get("reason", "Post-validation failed")

            # 7. Source attribution
            response.source_attribution = [{
                "mcp_server": server,
                "tool_name": tool,
                "timestamp": datetime.now().isoformat(),
                "data_source": self.service_registry.get_data_source(server),
            }]

        except Exception as e:
            response.error = str(e)
            response.success = False
            self.stats["failed_calls"] += 1
            logger.error("Gateway call_tool error: %s", e, exc_info=True)

        finally:
            response.execution_time = time.time() - start_time

            # Log result (best-effort)
            try:
                if response.audit_log_id is not None:
                    self.audit_logger.log_response(
                        audit_log_id=response.audit_log_id,
                        success=response.success,
                        execution_time=response.execution_time,
                        error=response.error,
                    )
            except Exception as audit_err:
                logger.warning("Audit log response failed (non-fatal): %s", audit_err)

        return response

    async def _execute_tool_call(
        self, server: str, tool: str, parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute the tool call on the real MCP server via the registered wrapper.

        Falls back to a stub response when no wrapper is registered for the
        requested server (e.g. during unit tests or when the MCP is offline).
        """
        wrapper = self._mcp_wrappers.get(server)
        if wrapper is None:
            logger.warning("No MCP wrapper for server '%s' — returning stub.", server)
            return {
                "status": "stub",
                "data": f"No live connection to {server}",
                "server": server,
                "tool": tool,
            }

        # Refresh the heartbeat so ServiceRegistry knows this server is alive
        self.service_registry.update_heartbeat(server)

        # Delegate to the MCPToolWrapper — use call_tool_safe to handle
        # cross-event-loop scenarios (report generation runs on a separate loop)
        result = await wrapper.call_tool_safe(tool, parameters)
        return result

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get current tool registry (only from healthy servers)."""
        return self.service_registry.get_all_tools()

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all registered services."""
        return self.service_registry.get_health_status()

    def get_gateway_stats(self) -> Dict[str, Any]:
        """Return gateway-level statistics for the dashboard."""
        return {
            **self.stats,
            "registered_servers": len(self._mcp_wrappers),
            "healthy_servers": sum(
                1 for s in self._mcp_wrappers
                if self.service_registry.is_healthy(s)
            ),
        }
