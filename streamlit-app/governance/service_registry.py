"""
Service Registry

MCP server discovery, health monitoring, and tool schema management.
Dynamic registration from live MCP wrappers with heartbeat tracking.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Default heartbeat timeout — a server with no heartbeat in this window
# is considered unhealthy.
_HEARTBEAT_TIMEOUT = timedelta(minutes=5)


class ServiceRegistry:
    """
    Service registry for MCP servers.

    Features:
    - Dynamic server registration (from live MCP wrappers)
    - Health monitoring with heartbeat timeouts
    - Tool schema caching per server
    - Automatic stale-server detection
    """

    def __init__(self, heartbeat_timeout: Optional[timedelta] = None):
        """Initialize service registry."""
        self.services: Dict[str, Dict[str, Any]] = {}
        self.health_status: Dict[str, bool] = {}
        self.tool_schemas: Dict[str, List[Dict[str, Any]]] = {}
        self.last_heartbeat: Dict[str, datetime] = {}
        self._heartbeat_timeout = heartbeat_timeout or _HEARTBEAT_TIMEOUT

    def register_service(
        self,
        server_name: str,
        endpoint: str,
        tools: List[Dict[str, Any]],
    ):
        """Register (or re-register) an MCP server."""
        self.services[server_name] = {
            "endpoint": endpoint,
            "tools": tools,
            "registered_at": datetime.now(),
        }
        self.tool_schemas[server_name] = tools
        self.health_status[server_name] = True
        self.last_heartbeat[server_name] = datetime.now()
        logger.info("ServiceRegistry: registered %s (%d tools)", server_name, len(tools))

    def deregister_service(self, server_name: str):
        """Remove a server from the registry (e.g. after shutdown)."""
        self.services.pop(server_name, None)
        self.health_status.pop(server_name, None)
        self.tool_schemas.pop(server_name, None)
        self.last_heartbeat.pop(server_name, None)
        logger.info("ServiceRegistry: deregistered %s", server_name)

    def is_healthy(self, server_name: str) -> bool:
        """Check if server is healthy based on status flag and heartbeat freshness."""
        if server_name not in self.health_status:
            return False

        # If heartbeat is stale, mark unhealthy
        last = self.last_heartbeat.get(server_name)
        if last is not None:
            if datetime.now() - last > self._heartbeat_timeout:
                self.health_status[server_name] = False
                return False

        return self.health_status[server_name]

    def mark_unhealthy(self, server_name: str):
        """Explicitly mark a server as unhealthy (e.g. after repeated errors)."""
        self.health_status[server_name] = False

    def update_heartbeat(self, server_name: str):
        """Update server heartbeat and mark it healthy."""
        self.last_heartbeat[server_name] = datetime.now()
        self.health_status[server_name] = True

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from healthy servers."""
        all_tools = []
        for server_name, service in self.services.items():
            if self.is_healthy(server_name):
                for tool in service["tools"]:
                    all_tools.append({
                        "server": server_name,
                        "tool": tool,
                    })
        return all_tools

    def get_tools_for_server(self, server_name: str) -> List[Dict[str, Any]]:
        """Get tools offered by a specific server."""
        return self.tool_schemas.get(server_name, [])

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services."""
        status = {}
        for server in self.services:
            last = self.last_heartbeat.get(server)
            status[server] = {
                "healthy": self.is_healthy(server),
                "last_heartbeat": last.isoformat() if isinstance(last, datetime) else "Never",
                "tool_count": len(self.services[server].get("tools", [])),
            }
        return status

    def get_healthy_servers(self) -> List[str]:
        """Return names of currently healthy servers."""
        return [s for s in self.services if self.is_healthy(s)]

    def get_data_source(self, server_name: str) -> str:
        """Get data source description for a server."""
        data_sources = {
            "pubchem": "PubChem (NIH)",
            "chembl": "ChEMBL (EMBL-EBI)",
            "biomcp": "PubMed, ClinicalTrials.gov, NCI CTS, OpenFDA",
            "semanticscholar": "Semantic Scholar (Allen Institute)",
            "jupyter": "Local Python execution",
            "duckdb": "Local DuckDB",
            "brave": "Brave Search",
            "playwright": "Web automation",
            "medrxiv": "medRxiv (Cold Spring Harbor Laboratory)",
            "biorxiv": "bioRxiv (Cold Spring Harbor Laboratory)",
            "opentargets": "Open Targets Platform (Target-Disease Associations)",
            "stringdb": "STRING (Protein-Protein Interaction Networks)",
        }
        return data_sources.get(server_name, "Unknown")
