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
        "args": ["../servers/pubchem/build/index.js"],
        "description": "PubChem MCP server for chemical compound data"
    }
    # Add more MCP servers here in the future
    # "another_server": {
    #     "command": "python",
    #     "args": ["path/to/server.py"],
    #     "description": "Description of another server"
    # }
}

# Agent settings
AGENT_MAX_ITERATIONS = 10
AGENT_VERBOSE = True
