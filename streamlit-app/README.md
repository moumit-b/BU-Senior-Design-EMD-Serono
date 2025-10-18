# Streamlit MCP Agent - Chemical Compound Query Tool

A prototype Streamlit application that uses a LangChain agent powered by Ollama (local LLM) to query MCP servers for chemical compound information.

## Features

- **LangChain Agent Framework**: Uses ReAct agent pattern for reasoning and tool use
- **Local LLM with Ollama**: No API keys required, runs completely locally
- **MCP Server Integration**: Connects to MCP servers (currently PubChem)
- **Interactive Chat Interface**: Streamlit-based UI for asking questions
- **Reasoning Transparency**: View the agent's thought process and tool calls

## Architecture

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangChain      │
│  Agent          │
└────────┬────────┘
         │
         ├──────────────┐
         ▼              ▼
┌──────────────┐  ┌──────────────┐
│ Ollama LLM   │  │  MCP Tools   │
└──────────────┘  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ MCP Servers  │
                  │  (PubChem)   │
                  └──────────────┘
```

## Prerequisites

### 1. Ollama Setup

Ollama must be installed and running locally.

**Install Ollama:**
- Download from: https://ollama.ai/download
- Follow installation instructions for your OS

**Pull a model:**
```bash
# Recommended: Llama 3.2 (default in config.py)
ollama pull llama3.2

# Alternative models:
# ollama pull llama3
# ollama pull mistral
# ollama pull codellama
```

**Start Ollama server:**
```bash
ollama serve
```

The server should be running at `http://localhost:11434`

### 2. Node.js Setup (for PubChem MCP Server)

The PubChem MCP server runs on Node.js. Make sure you have Node.js installed.

**Verify Node.js installation:**
```bash
node --version
npm --version
```

### 3. Python Environment

Python 3.9 or higher is required.

## Installation

### 1. Clone the repository and navigate to the streamlit-app directory:

```bash
cd streamlit-app
```

### 2. Create a virtual environment:

```bash
# Using venv
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

### 3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 4. Build the PubChem MCP Server

Navigate to the PubChem server directory and build it:

```bash
cd ../servers/pubchem
npm install
npm run build
cd ../../streamlit-app
```

## Configuration

### `config.py`

Main configuration file for the application.

**Ollama Settings:**
```python
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # Change to your preferred model
```

**MCP Server Configuration:**
```python
MCP_SERVERS = {
    "pubchem": {
        "command": "node",
        "args": ["../servers/pubchem/build/index.js"],
        "description": "PubChem MCP server for chemical compound data"
    }
}
```

**Agent Settings:**
```python
AGENT_MAX_ITERATIONS = 10  # Maximum reasoning steps
AGENT_VERBOSE = True       # Show detailed agent logs
```

## Running the Application

### 1. Ensure Ollama is running:

```bash
ollama serve
```

### 2. Start the Streamlit app:

```bash
streamlit run app.py
```

### 3. Open your browser:

The app should automatically open at `http://localhost:8501`

## Usage

### Example Queries

- "What is the molecular formula of aspirin?"
- "Tell me about caffeine"
- "What is the molecular weight of ethanol?"
- "Find information about glucose"
- "What are the properties of acetaminophen?"

### Understanding Agent Reasoning

Click on "🔍 View Agent Reasoning Process" in the chat to see:
- **Actions**: What tool the agent decided to use and why
- **Observations**: The results returned from the MCP server
- **Thought Process**: The agent's step-by-step reasoning

## Adding More MCP Servers

To add additional MCP servers beyond PubChem:

### Step 1: Create or Install the MCP Server

Place your MCP server in the `servers/` directory. For example:
```
servers/
├── pubchem/
└── your-new-server/
```

### Step 2: Update `config.py`

Add your server to the `MCP_SERVERS` dictionary:

```python
MCP_SERVERS = {
    "pubchem": {
        "command": "node",
        "args": ["../servers/pubchem/build/index.js"],
        "description": "PubChem MCP server for chemical compound data"
    },
    "your_server_name": {
        "command": "python",  # or "node", etc.
        "args": ["../servers/your-new-server/server.py"],
        "description": "Description of what your server does"
    }
}
```

### Step 3: Restart the Application

The new MCP server will be automatically loaded on restart. Tools from the new server will be available to the agent.

### Server Configuration Fields

- **command**: The command to run the server (`python`, `node`, etc.)
- **args**: List of arguments to pass to the command (usually the path to the server script)
- **description**: Human-readable description of what the server provides

## Project Structure

```
streamlit-app/
├── app.py              # Main Streamlit application
├── agent.py            # LangChain agent setup and logic
├── mcp_tools.py        # MCP server connection and tool wrapping
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Troubleshooting

### "Failed to connect to Ollama"
- Ensure Ollama is running: `ollama serve`
- Check that the base URL in `config.py` is correct
- Verify the model is installed: `ollama list`

### "Failed to connect to MCP server: pubchem"
- Build the PubChem server: `cd ../servers/pubchem && npm run build`
- Check that Node.js is installed: `node --version`
- Verify the path in `config.py` is correct

### "No tools were loaded from MCP servers"
- Check MCP server logs for errors
- Verify server command and args are correct in `config.py`
- Ensure servers are properly built

### Agent gives incorrect or incomplete answers
- Try a different Ollama model (e.g., `ollama pull llama3`)
- Increase `AGENT_MAX_ITERATIONS` in `config.py`
- Check the reasoning process to see where the agent gets stuck

## Dependencies

Key dependencies:
- **streamlit**: Web UI framework
- **langchain**: Agent framework
- **langchain-ollama**: Ollama integration for LangChain
- **mcp**: MCP SDK for Python
- **httpx**: HTTP client for MCP connections

See `requirements.txt` for full list.

## Future Enhancements

Potential improvements for this prototype:
- [ ] Add support for multiple simultaneous MCP servers
- [ ] Implement conversation memory/history persistence
- [ ] Add export functionality for queries and results
- [ ] Support for image/structure rendering of compounds
- [ ] Add caching for frequently queried compounds
- [ ] Implement batch query functionality
- [ ] Add support for cloud-based LLMs (OpenAI, Anthropic)
- [ ] Create custom tools beyond MCP servers

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
