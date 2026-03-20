"""
Configuration for the Streamlit MCP Agent application.
"""

import os
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    # Get the directory where config.py is located
    config_dir = Path(__file__).parent
    env_path = config_dir / '.env'

    # Load .env file with explicit path
    load_dotenv(dotenv_path=env_path, override=True)

except ImportError:
    pass
except Exception:
    pass

# === LLM Settings ===
# Using Anthropic Claude Sonnet 4.5 as the primary LLM provider

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-5-20250514"
CLAUDE_TEMPERATURE = 0.7
CLAUDE_MAX_TOKENS = 8192

# LLM Provider selection
LLM_PROVIDER = (os.getenv("LLM_PROVIDER") or os.getenv("PROVIDER") or "anthropic").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
# MCP Server configurations
MCP_SERVERS = {
    "pubchem": {
        "command": "node",
        "args": ["../servers/pubchem/index.js"],
        "description": "PubChem MCP server for chemical compound data"
    },
    "biomcp": {
        "command": "python",
        "args": ["-m", "biomcp", "run"],
        "description": "BioMCP server - Comprehensive biomedical research (PubMed, clinical trials, variants, genes)"
    },
    "literature": {
        "command": "node",
        "args": ["../servers/literature/index.js"],
        "description": "Literature MCP server for PubMed articles, abstracts, and citations"
    },
    "data_analysis": {
        "command": "node",
        "args": ["../servers/data_analysis/index.js"],
        "description": "Data Analysis MCP server for statistics, correlations, sequence analysis, and molecular descriptors"
    },
    "web_knowledge": {
        "command": "node",
        "args": ["../servers/web_knowledge/index.js"],
        "description": "Web/Knowledge MCP server for Wikipedia, clinical trials, gene info, and drug information"
    },
    "medrxiv": {
        "command": "node",
        "args": ["../servers/medrxiv/index.js"],
        "description": "medRxiv MCP server for preprint search and metadata"
    },
    "biorxiv": {
        "command": "node",
        "args": ["../servers/biorxiv/index.js"],
        "description": "bioRxiv MCP server for biology preprint search and metadata"
    },
    "openfda": {
        "command": "node",
        "args": ["../servers/openfda/index.js"],
        "description": "Open FDA MCP for drug approvals, adverse events, recalls, and regulatory data"
    },
    "opentargets": {
        "command": "node",
        "args": ["../servers/opentargets/index.js"],
        "description": "Open Targets Platform MCP for gene-target-disease associations, drug mechanisms, and target validation"
    },
    "omnipathdb": {
        "command": "node",
        "args": ["../servers/omnipathdb/index.js"],
        "description": "OmniPathDB MCP for protein-protein interactions, signaling pathways, and regulatory networks"
    },
    "string": {
        "command": "node",
        "args": ["../servers/string/index.js"],
        "description": "STRING MCP for protein-protein interactions, network neighborhoods, and interaction evidence"
    },
    "brave": {
        "command": "node",
        "args": ["../servers/brave/index.js"],
        "description": "Brave Search MCP for web/news search"
    },
    "playwright": {
        "command": "node",
        "args": ["../servers/playwright/index.js"],
        "description": "Playwright MCP for web automation and dashboard access"
    },
    "chembl": {
        "command": "node",
        "args": ["../servers/chembl/index.js"],
        "description": "ChEMBL MCP server for bioactivity and target data"
    },
    "semanticscholar": {
        "command": "node",
        "args": ["../servers/semanticscholar/index.js"],
        "description": "Semantic Scholar MCP for citations and paper recommendations"
    },
    "jupyter": {
        "command": "node",
        "args": ["../servers/jupyter/index.js"],
        "description": "Jupyter MCP for Python code execution and data analysis"
    },
    "duckdb": {
        "command": "node",
        "args": ["../servers/duckdb/index.js"],
        "description": "DuckDB MCP for SQL analytics on local files"
    }
}

# Persistent Context Layer (Phase 1)
DATABASE_PATH = "data/sessions.db"
VECTOR_STORE_PATH = "data/chroma"

# Feature Flags - Enable/disable new features
FEATURE_FLAGS = {
    "use_persistent_context": False,     # Phase 1: SQLite + ChromaDB (disabled - download timeout issue)
    "use_specialized_agents": True,      # Phase 1: Chemical, Clinical, etc. - WORKING
    "use_governance_gateway": False,     # Phase 2: Context Forge Gateway (optional)
    "use_langgraph_orchestrator": True,  # Phase 3: Orchestrator - REQUIRED for queries
    "use_bidirectional_learning": False, # Phase 4: MCP-Agent learning (future)
    "enable_reporting": True,            # Phase 5: PDF/Markdown reports - WORKING
    "enable_ui_v2": False               # Phase 6: Enhanced UI (future)
}

# Agent settings
AGENT_MAX_ITERATIONS = 10
AGENT_VERBOSE = True

# Additional MCP Servers (from research) - Currently using all in MCP_SERVERS
EXTENDED_MCP_SERVERS = {}

# Governance settings (Phase 2)
GOVERNANCE_CONFIG = {
    "enable_audit_logging": True,
    "audit_retention_days": 90,
    "enable_compliance_checks": True,
    "enable_rate_limiting": True,
    "rate_limit_per_user": 100,  # queries per hour
    "enable_pii_detection": True
}
