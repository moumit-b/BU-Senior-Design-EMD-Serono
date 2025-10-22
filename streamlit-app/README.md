# Streamlit MCP Agent - Chemical Compound Query Tool

A prototype Streamlit application that demonstrates AI agent architecture using Ollama (local LLM) to query MCP (Model Context Protocol) servers for chemical compound information from PubChem.

## Features

- **Custom ReAct-Style Agent**: Implements reasoning and action loop for intelligent tool use
- **Local LLM with Ollama**: Runs completely locally using Llama 3.2 - no API keys required
- **MCP Server Integration**: Connects to MCP servers via stdio protocol (currently PubChem)
- **Interactive Chat Interface**: User-friendly Streamlit UI for natural language queries
- **Reasoning Transparency**: View the agent's thought process and tool execution steps
- **Extensible Architecture**: Easy to add new MCP servers and tools

## Architecture

```
┌─────────────────────────────────┐
│      Streamlit Web UI           │  ← User Interface
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Custom ReAct Agent (Python)   │  ← Reasoning Loop
│   - Prompt Engineering          │
│   - Action Parsing              │
│   - Tool Orchestration          │
└────────────┬────────────────────┘
             │
             ├──────────────────────┐
             ▼                      ▼
┌──────────────────────┐  ┌─────────────────────┐
│   Ollama LLM         │  │  MCP Tool Wrapper   │  ← Async Tool Manager
│   (llama3.2)         │  │  (Python)           │
│   Local Inference    │  └──────────┬──────────┘
└──────────────────────┘             │
                                     ▼
                          ┌─────────────────────┐
                          │  PubChem MCP Server │  ← Node.js Process
                          │  (stdio protocol)   │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │  PubChem REST API   │  ← External Data Source
                          │  (ncbi.nlm.nih.gov) │
                          └─────────────────────┘
```

## Tech Stack

### Frontend & Application
- **Streamlit** (1.32.0+) - Web UI framework for Python
- **Python** (3.11.9+) - Core application language

### AI & Agent Framework
- **Ollama** (0.12.6) - Local LLM runtime
- **Llama 3.2** (2.0 GB model) - Language model for agent reasoning
- **Custom ReAct Agent** - Hand-built agent implementation (no LangChain agent dependencies)

### Integration Layer
- **LangChain Core** (1.0.1) - Tool abstractions only
- **LangChain Ollama** (0.1.0+) - Ollama LLM integration
- **MCP SDK (Python)** (0.9.0) - MCP client implementation

### MCP Server
- **Node.js** (v20.16.0) - Server runtime
- **@modelcontextprotocol/sdk** (1.20.0) - MCP server framework
- **Stdio Transport** - Process communication protocol

### External APIs
- **PubChem PUG REST API** - Chemical compound database

## Available Tools

The PubChem MCP server provides two tools:

### 1. `search_compounds_by_name`
Search for chemical compounds by name and retrieve their PubChem CIDs (Compound IDs).

**Parameters:**
- `name` (string, required) - Compound name (e.g., "caffeine")
- `max_results` (number, optional) - Maximum results to return (default: 5)

**Returns:** List of CIDs and metadata

### 2. `get_compound_properties`
Retrieve detailed properties for a specific compound by CID.

**Parameters:**
- `cid` (number, required) - PubChem Compound ID

**Returns:** JSON with:
- `MolecularFormula` - Chemical formula
- `MolecularWeight` - Molecular weight in g/mol
- `IUPACName` - IUPAC systematic name
- `IsomericSMILES` - SMILES notation
- `InChI` - InChI identifier
- `InChIKey` - InChI hash key
- `Link` - PubChem compound page URL

## Prerequisites

### 1. Python Environment
- **Python 3.9+** required (tested on Python 3.11.9)

### 2. Node.js (for PubChem MCP Server)
- **Node.js v16+** required (tested on v20.16.0)

**Verify installation:**
```bash
node --version
npm --version
```

### 3. Ollama Setup

**Install Ollama:**
1. Download from: https://ollama.com/download
2. Follow installation instructions for your OS
3. **Important (Windows):** After installation, you may need to:
   - Restart your PowerShell/terminal to pick up PATH changes, OR
   - Use this command to refresh PATH in current session:
     ```powershell
     $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
     ```

**Pull the Llama 3.2 model:**
```bash
ollama pull llama3.2
```

**Verify model is installed:**
```bash
ollama list
# Should show: llama3.2:latest
```

**Note:** Ollama server usually auto-starts after installation. If needed, manually start with:
```bash
ollama serve
```

## Installation

### Step 1: Clone and Navigate
```bash
cd streamlit-app
```

### Step 2: Create Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `streamlit>=1.32.0` - Web UI framework
- `langchain>=1.0.0` - Tool abstractions (core only)
- `langchain-community>=0.0.20` - Community integrations
- `langchain-ollama>=0.1.0` - Ollama LLM wrapper
- `mcp>=0.9.0` - MCP SDK for Python
- `httpx>=0.25.0` - HTTP client for MCP
- `python-dotenv>=1.0.0` - Environment variable management
- `pydantic>=2.0.0` - Data validation

### Step 4: Setup PubChem MCP Server

The PubChem server is already created and Node.js dependencies are installed. No build step required - the server runs directly from `index.js`.

**Verify server file exists:**
```bash
ls ../servers/pubchem/index.js
```

**Test the server (optional):**
```bash
cd ../servers/pubchem
node index.js
# Should output: "PubChem MCP server running on stdio"
# Press Ctrl+C to exit
cd ../../streamlit-app
```

## Configuration

### `config.py`

All settings are configured in `streamlit-app/config.py`:

```python
# Ollama Settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # Change to use different model

# MCP Server Configuration
MCP_SERVERS = {
    "pubchem": {
        "command": "node",
        "args": ["../servers/pubchem/index.js"],  # Direct path, no build needed
        "description": "PubChem MCP server for chemical compound data"
    }
}

# Agent Settings
AGENT_MAX_ITERATIONS = 10  # Maximum reasoning/action cycles
AGENT_VERBOSE = True       # Print agent logs to console
```

## Running the Demo

### Quick Start

1. **Ensure you're in the streamlit-app directory with virtual environment activated:**
   ```bash
   cd streamlit-app
   venv\Scripts\activate  # Windows
   # OR
   source venv/bin/activate  # macOS/Linux
   ```

2. **Verify Ollama is running and model is available:**
   ```bash
   ollama list
   # Should show: llama3.2:latest
   ```

3. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

4. **Access the web interface:**
   - The app will automatically open at: `http://localhost:8501`
   - Or manually navigate to the URL shown in terminal

### Startup Messages

When the app starts, you should see:
```
Connecting to MCP server: pubchem...
✓ Connected to pubchem, loaded 2 tools
```

If you see errors, check the [Troubleshooting](#troubleshooting) section.

## Usage

### Example Queries

Try these natural language questions:

**Basic Properties:**
- "What is the molecular formula of aspirin?"
- "What is the molecular weight of caffeine?"
- "Tell me about glucose"

**Detailed Information:**
- "Find information about acetaminophen"
- "What are the properties of ethanol?"
- "Search for information about ibuprofen"

**Multi-step Reasoning:**
- "Compare the molecular weights of caffeine and aspirin"
- "What is the IUPAC name of caffeine and what does it mean?"

### Understanding Agent Reasoning

The agent uses a ReAct (Reasoning + Acting) loop:

1. **Thought**: Agent reasons about what to do next
2. **Action**: Agent decides to use a tool (e.g., search_compounds_by_name)
3. **Observation**: Agent receives tool results
4. **Repeat**: Continue until final answer is reached

**To view the reasoning process:**
- Click "🔍 View Agent Reasoning Process" in any chat response
- See each action taken and observation received
- Understand the agent's decision-making process

### Example Interaction

**User:** "What is the molecular weight of caffeine?"

**Agent Process:**
1. **ACTION:** search_compounds_by_name
   - **INPUT:** `{"name": "caffeine"}`
   - **OBSERVATION:** Found CID 2519
2. **ACTION:** get_compound_properties
   - **INPUT:** `{"cid": 2519}`
   - **OBSERVATION:** Retrieved properties including MolecularWeight: 194.19
3. **FINAL ANSWER:** "The molecular weight of caffeine is 194.19 g/mol."

## Adding More MCP Servers

The architecture supports multiple MCP servers running simultaneously.

### Step 1: Add Your MCP Server

Place your server in the `servers/` directory:
```
servers/
├── pubchem/          # Existing
│   ├── index.js
│   └── package.json
└── your-server/      # New
    ├── server.py     # Or server.js
    └── requirements.txt
```

### Step 2: Update Configuration

Add to `config.py`:
```python
MCP_SERVERS = {
    "pubchem": {
        "command": "node",
        "args": ["../servers/pubchem/index.js"],
        "description": "PubChem MCP server for chemical compound data"
    },
    "your_server": {
        "command": "python",  # or "node", etc.
        "args": ["../servers/your-server/server.py"],
        "description": "Your custom MCP server"
    }
}
```

### Step 3: Restart Streamlit

All servers are loaded on startup. The agent automatically has access to all tools from all servers.

## Project Structure

```
streamlit-app/
├── app.py              # Main Streamlit application & UI
├── agent.py            # Custom ReAct agent implementation
├── mcp_tools.py        # MCP server connection & tool wrapping
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── venv/               # Virtual environment (created during setup)

../servers/
└── pubchem/
    ├── index.js        # PubChem MCP server implementation
    ├── package.json    # Node.js dependencies
    └── node_modules/   # Installed Node packages
```

## How It Works

### Agent Implementation

Unlike typical LangChain agents, this uses a **custom ReAct implementation** to avoid compatibility issues with LangChain's evolving agent APIs.

**Key Components:**

1. **Prompt Engineering** (`agent.py:_create_prompt`)
   - Instructs LLM on available tools
   - Defines ACTION/INPUT/OBSERVATION format
   - Requests structured responses

2. **Action Parsing** (`agent.py:_parse_action`)
   - Extracts tool name and parameters from LLM response
   - Handles JSON parsing with fallbacks

3. **Tool Execution Loop** (`agent.py:query`)
   - Iterates up to `AGENT_MAX_ITERATIONS` times
   - Executes tools and provides observations back to LLM
   - Continues until LLM provides FINAL ANSWER

4. **MCP Integration** (`mcp_tools.py`)
   - Manages async MCP server connections
   - Wraps MCP tools as LangChain Tool objects
   - Handles stdio transport and result parsing

### MCP Server Communication

The PubChem server uses the **stdio transport protocol**:
- Python spawns Node.js process
- Communication via stdin/stdout
- JSON-RPC message format
- Asynchronous request/response

## Troubleshooting

### "Failed to connect to Ollama"

**Symptoms:**
- Error message about Ollama connection
- Agent fails to initialize

**Solutions:**
1. Check if Ollama is running:
   ```bash
   ollama list  # Should not error
   ```
2. Start Ollama if needed:
   ```bash
   ollama serve
   ```
3. Verify model is installed:
   ```bash
   ollama list
   # Should show: llama3.2:latest
   ```
4. Check config.py has correct base URL:
   ```python
   OLLAMA_BASE_URL = "http://localhost:11434"
   ```

### "Failed to connect to MCP server: pubchem"

**Symptoms:**
- `✗ Failed to connect to pubchem`
- "Connection closed" error
- "No tools were loaded from MCP servers"

**Solutions:**

1. **Test server directly:**
   ```bash
   cd servers/pubchem
   node index.js
   # Should output: "PubChem MCP server running on stdio"
   ```

   If you see errors:
   - Check Node.js is installed: `node --version`
   - Ensure dependencies are installed: `npm install`
   - Verify `index.js` exists

2. **Check config.py path:**
   ```python
   # Should be:
   "args": ["../servers/pubchem/index.js"]
   # NOT:
   "args": ["../servers/pubchem/build/index.js"]  # ❌ Wrong
   ```

3. **Check Python MCP SDK version:**
   ```bash
   pip show mcp
   # Should show version 0.9.0 or compatible
   ```

### "No tools were loaded from MCP servers"

**Symptoms:**
- Warning message in Streamlit
- No tools available in dropdown
- Agent cannot execute actions

**Solutions:**
1. Check terminal output for connection errors
2. Verify MCP server is in correct path
3. Test server independently (see above)
4. Check Python virtual environment is activated

### Agent Gives Incorrect/Incomplete Answers

**Symptoms:**
- Agent reaches max iterations
- Wrong information returned
- Agent gets stuck in loop

**Solutions:**

1. **Try a larger model:**
   ```bash
   ollama pull llama3  # Larger, more capable
   ```
   Update `config.py`:
   ```python
   OLLAMA_MODEL = "llama3"
   ```

2. **Increase iteration limit:**
   ```python
   AGENT_MAX_ITERATIONS = 20  # In config.py
   ```

3. **Check reasoning process:**
   - Click "View Agent Reasoning Process"
   - See where agent gets confused
   - May need to rephrase question

4. **Verify data availability:**
   - Some compounds may not exist in PubChem
   - Try a well-known compound first (e.g., "aspirin")

### "ollama: command not found" (Windows)

**Symptoms:**
- PowerShell can't find `ollama` command
- Recently installed Ollama

**Solution:**
Restart PowerShell or refresh PATH:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
ollama --version  # Should now work
```

## Performance Notes

- **First Query Delay:** Initial query may be slower due to:
  - MCP server startup (~1-2 seconds)
  - First LLM inference (model loading)
  - Subsequent queries are faster

- **LLM Inference Time:** Each agent iteration takes ~2-10 seconds depending on:
  - Model size (llama3.2 is faster than llama3)
  - Hardware (GPU vs CPU)
  - Complexity of reasoning

- **Expected Query Time:** Typical queries complete in:
  - Simple properties: 10-20 seconds (2-3 agent iterations)
  - Complex queries: 20-40 seconds (4-6 iterations)

## Known Limitations

1. **LangChain Version Compatibility:**
   - Built for LangChain 1.0+
   - Uses custom agent to avoid deprecated APIs
   - May need updates for future LangChain versions

2. **Single Conversation Context:**
   - No conversation memory between queries
   - Each query is independent
   - Future: Add conversation history

3. **Ollama Local Only:**
   - Requires local Ollama installation
   - Cannot use cloud LLM APIs (OpenAI, Anthropic)
   - Future: Add support for remote LLMs

4. **Text-Only Output:**
   - No visualization of chemical structures
   - No rendering of 2D/3D molecular diagrams
   - Future: Add chemical structure rendering

## Future Enhancements

Planned improvements:

- [ ] **Conversation Memory** - Remember previous queries in session
- [ ] **Multi-MCP Demo** - Add second MCP server (e.g., Wikipedia, Weather)
- [ ] **Chemical Structure Visualization** - Render 2D molecular structures
- [ ] **Export Functionality** - Download query results as JSON/CSV
- [ ] **Batch Queries** - Query multiple compounds at once
- [ ] **Result Caching** - Cache PubChem API responses
- [ ] **Cloud LLM Support** - Option to use OpenAI/Anthropic APIs
- [ ] **Advanced Agent Patterns** - Tool chaining, parallel execution
- [ ] **Unit Tests** - Test coverage for agent and MCP integration
- [ ] **Docker Deployment** - Containerized deployment option

## License

This is a prototype/demo application for the BU Senior Design project.

## Contributing

This project is part of BU Senior Design EMD Serono team. For questions or contributions, please contact the project team.

## Resources

- **MCP Documentation:** https://modelcontextprotocol.io/
- **Ollama:** https://ollama.com/
- **PubChem API:** https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
- **Streamlit:** https://docs.streamlit.io/
- **LangChain:** https://python.langchain.com/

## Acknowledgments

- **PubChem** for providing free chemical compound data API
- **Ollama** for local LLM runtime
- **Anthropic** for Model Context Protocol specification
- **Meta** for Llama models
