"""
Configuration for the Streamlit MCP Agent application.
"""

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # Change this to your preferred Ollama model

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
    }
}

# Agent settings
AGENT_MAX_ITERATIONS = 10
AGENT_VERBOSE = True
