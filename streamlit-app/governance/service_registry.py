"""
Service Registry

MCP server discovery, health monitoring, and tool schema management.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta


class ServiceRegistry:
    """
    Service registry for MCP servers.
    
    Features:
    - Server registration
    - Health monitoring
    - Tool schema caching
    - Automatic stale server removal
    """

    def __init__(self):
        """Initialize service registry."""
        self.services = {}
        self.health_status = {}
        self.tool_schemas = {}
        self.last_heartbeat = {}

    def register_service(
        self,
        server_name: str,
        endpoint: str,
        tools: List[Dict[str, Any]]
    ):
        """Register an MCP server."""
        self.services[server_name] = {
            "endpoint": endpoint,
            "tools": tools,
            "registered_at": datetime.now()
        }
        self.health_status[server_name] = True
        self.last_heartbeat[server_name] = datetime.now()

    def is_healthy(self, server_name: str) -> bool:
        """Check if server is healthy."""
        if server_name not in self.health_status:
            return False
        
        # Check if heartbeat is recent (last 5 minutes)
        if server_name in self.last_heartbeat:
            time_since_heartbeat = datetime.now() - self.last_heartbeat[server_name]
            if time_since_heartbeat > timedelta(minutes=5):
                self.health_status[server_name] = False
                return False
        
        return self.health_status[server_name]

    def update_heartbeat(self, server_name: str):
        """Update server heartbeat."""
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
                        "tool": tool
                    })
        return all_tools

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services."""
        return {
            server: {
                "healthy": self.is_healthy(server),
                "last_heartbeat": self.last_heartbeat.get(server, "Never").isoformat()
                    if isinstance(self.last_heartbeat.get(server), datetime) else "Never"
            }
            for server in self.services.keys()
        }

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
            "playwright": "Web automation"
        }
        return data_sources.get(server_name, "Unknown")
