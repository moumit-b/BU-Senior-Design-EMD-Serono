"""
Context Forge Gateway

Central gateway implementing IBM Context Forge pattern.
All MCP tool calls flow through this gateway for governance.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from .audit_logger import AuditLogger
from .compliance_engine import ComplianceEngine
from .service_registry import ServiceRegistry
from .rate_limiter import RateLimiter


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
        
        # Initialize services
        self._initialize_services()

    def _initialize_services(self):
        """Initialize all gateway services."""
        # Register known MCP servers
        # In production, this would discover servers dynamically
        pass

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
        5. Execute tool call
        6. Post-validation
        7. Log result
        8. Return with attribution
        
        Args:
            server: MCP server name
            tool: Tool name
            parameters: Tool parameters
            context: Request context
            
        Returns:
            ToolResponse with results
        """
        start_time = time.time()
        response = ToolResponse(
            success=False,
            mcp_server=server,
            tool_name=tool
        )

        try:
            # 1. Rate limiting
            if not self.rate_limiter.check_rate_limit(context.user_id, server):
                response.error = "Rate limit exceeded"
                return response

            # 2. Pre-validation
            compliance_result = self.compliance_engine.validate_request(
                server, tool, parameters, context
            )
            if not compliance_result["passed"]:
                response.error = compliance_result["reason"]
                response.compliance_passed = False
                return response

            # 3. Check service health
            if not self.service_registry.is_healthy(server):
                response.error = f"Service {server} is unhealthy"
                return response

            # 4. Audit log (request)
            audit_log_id = self.audit_logger.log_request(
                user_id=context.user_id,
                session_id=context.session_id,
                agent_name=context.agent_name,
                mcp_server=server,
                tool_name=tool,
                parameters=parameters
            )

            # 5. Execute tool call (simulated for now)
            # In production, this would call actual MCP server
            result = await self._execute_tool_call(server, tool, parameters)
            
            response.success = True
            response.result = result
            response.audit_log_id = audit_log_id

            # 6. Post-validation
            post_validation = self.compliance_engine.validate_response(result)
            response.compliance_passed = post_validation["passed"]

            # 7. Source attribution
            response.source_attribution = [{
                "mcp_server": server,
                "tool_name": tool,
                "timestamp": datetime.now().isoformat(),
                "data_source": self.service_registry.get_data_source(server)
            }]

        except Exception as e:
            response.error = str(e)
            response.success = False

        finally:
            response.execution_time = time.time() - start_time
            
            # Log result
            self.audit_logger.log_response(
                audit_log_id=response.audit_log_id,
                success=response.success,
                execution_time=response.execution_time,
                error=response.error
            )

        return response

    async def _execute_tool_call(self, server: str, tool: str, parameters: Dict[str, Any]) -> Any:
        """Execute actual MCP tool call (placeholder)."""
        # In production, this calls the actual MCP server
        return {
            "status": "success",
            "data": f"Result from {server}.{tool}",
            "parameters": parameters
        }

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get current tool registry (fresh context).
        
        Returns:
            List of available tools with schemas
        """
        return self.service_registry.get_all_tools()

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all services.
        
        Returns:
            Health status dictionary
        """
        return self.service_registry.get_health_status()
