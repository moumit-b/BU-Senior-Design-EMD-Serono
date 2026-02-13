# Pharmaceutical Research Intelligence System

A multi-agent orchestration system powered by **Claude Sonnet 4.5** for pharmaceutical research. Uses LangChain, LangGraph, and MCP (Model Context Protocol) servers to coordinate five specialized AI agents for chemistry, clinical trials, literature, genetics, and data analysis.

---

## Architecture Overview

```
User Query
    |
    v
Streamlit UI (app.py)
    |
    v
LangGraph Orchestrator (orchestrator_agent.py)
    |--- analyze_query -> extract keywords, determine complexity
    |--- create_plan   -> parallel vs sequential strategy
    |--- assign_agents -> select best agents by confidence score
    |--- execute_tasks -> run agent processes
    |--- synthesize    -> Claude combines all results
    |--- validate      -> governance compliance check
    |
    +---> ChemicalAgent   (PubChem, ChEMBL, BioMCP)
    +---> ClinicalAgent   (BioMCP, OpenFDA)
    +---> LiteratureAgent (BioMCP, Semantic Scholar)
    +---> GeneAgent       (BioMCP, MyGene, MyVariant)
    +---> DataAgent       (Jupyter, DuckDB)
```

All agents and the orchestrator use **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250514`) as their LLM via a centralized factory (`utils/llm_factory.py`).

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for MCP servers)
- **Anthropic API Key** with Claude Sonnet 4.5 access - get one at [console.anthropic.com](https://console.anthropic.com/)

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd BU-Senior-Design-EMD-Serono/streamlit-app
```

### 2. Create a Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` - Web UI framework
- `langchain`, `langchain-anthropic` - Agent framework + Claude integration
- `anthropic` - Anthropic Python SDK
- `langgraph` - Multi-agent orchestration
- `mcp` - MCP server connections
- `biomcp-python` - Biomedical research tools
- And other utilities (see `requirements.txt` for full list)

### 4. Set Your Anthropic API Key

You need a Claude API key from [console.anthropic.com](https://console.anthropic.com/).

**Option A: Create a `.env` file (recommended)**

Create a file named `.env` inside the `streamlit-app/` directory with this content:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

**Option B: Set as environment variable**

Windows (Command Prompt):
```cmd
set ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-api03-YOUR-KEY-HERE"
```

macOS/Linux:
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

### 5. (Optional) Install MCP Servers

The system works without MCP servers in **direct LLM mode** - Claude Sonnet 4.5 answers questions using its own knowledge. To enable MCP tool access for live data:

```bash
# From the repository root (one level up from streamlit-app)
cd ../servers/pubchem && npm install
cd ../servers/literature && npm install
cd ../servers/data_analysis && npm install
cd ../servers/web_knowledge && npm install

# BioMCP (Python-based) - install in your venv
pip install biomcp-python
```

### 6. Launch the Application

**Windows (recommended):**
```cmd
run.bat
```

**Any platform:**
```bash
streamlit run app.py
```

The application opens automatically at **http://localhost:8501**.

---

## Using the Application

### Asking Questions

Type any pharmaceutical research question in the chat input. Examples:

**Chemistry:**
- "What is the molecular formula of aspirin?"
- "Explain the mechanism of action of ibuprofen"
- "What are the ADMET properties of metformin?"

**Clinical Trials:**
- "What are the phases of clinical trials?"
- "Find clinical trials for BRCA gene therapies"

**Genetics:**
- "What is the role of p53 in cancer?"
- "How does CRISPR gene editing work?"
- "Explain the EGFR signaling pathway"

**Multi-Agent Queries (triggers multiple agents):**
- "Analyze the competitive landscape for GLP-1 receptor agonists including clinical trials and gene targets"
- "Find research papers on CRISPR-Cas9 applications in oncology and related drug compounds"

### How Multi-Agent Orchestration Works

1. The orchestrator analyzes your query and extracts keywords
2. It scores each agent's relevance (Chemical, Clinical, Literature, Gene, Data)
3. Selects the best agents (1-3 depending on complexity)
4. Runs agents in parallel or sequentially as needed
5. Claude Sonnet 4.5 synthesizes all agent results into one comprehensive response

Click **"View Agent Reasoning Process"** in any response to see the step-by-step tool usage.

---

## Generating a Full Test Report

### Option 1: Run the System Test

This validates all components end-to-end:

```bash
cd streamlit-app
python test_system.py
```

The test covers:
- Claude Sonnet 4.5 connectivity
- All 5 specialized agents
- LangGraph orchestrator workflow
- Multi-agent synthesis
- Report generation

A markdown report is saved to `streamlit-app/` with timestamped filename.

### Option 2: Programmatic Report

```python
import asyncio
from agents.orchestrator_agent import OrchestratorAgent

async def generate_report():
    orchestrator = OrchestratorAgent(
        mcp_orchestrator=None,
        governance_gateway=None
    )

    result = await orchestrator.process_query(
        query="Analyze aspirin: molecular properties, clinical trials, and gene targets",
        session_id="test-session",
        user_id="test-user"
    )

    print(result["final_answer"])

asyncio.run(generate_report())
```

### Option 3: From the Streamlit UI

1. Open `http://localhost:8501`
2. Enter a complex research query
3. The orchestrator assigns multiple agents and synthesizes results
4. Copy the synthesized response as your report

---

## Project Structure

```
streamlit-app/
├── app.py                          # Main Streamlit entry point
├── agent.py                        # Simple MCP agent with tool calling
├── config.py                       # Configuration (Claude model, MCP servers, features)
├── mcp_tools.py                    # MCP server connection and tool wrapper
├── run.bat                         # Windows startup script
├── requirements.txt                # Python dependencies
├── .env                            # API key (create this - not in git)
│
├── agents/                         # Specialized agent implementations
│   ├── base_agent.py               # Abstract base class
│   ├── chemical_agent.py           # Chemistry & drug compounds
│   ├── clinical_agent.py           # Clinical trials & regulatory
│   ├── gene_agent.py               # Genetics & molecular biology
│   ├── literature_agent.py         # Scientific literature
│   ├── data_agent.py               # Data analysis & statistics
│   └── orchestrator_agent.py       # LangGraph multi-agent orchestrator
│
├── orchestration/                  # Dual orchestration system
│   ├── agent_orchestrator.py       # Top-layer: agent routing & task decomposition
│   ├── mcp_orchestrator.py         # Bottom-layer: MCP server routing
│   ├── performance_kb.py           # Bidirectional learning knowledge base
│   ├── session_manager.py          # Research session memory
│   └── tool_composer.py            # Dynamic tool composition
│
├── reporting/                      # Report generation
│   ├── report_generator.py         # Markdown/PDF report engine
│   └── exporters/                  # Format exporters
│
├── utils/                          # Utilities
│   └── llm_factory.py              # Centralized Claude LLM factory
│
├── governance/                     # Governance & compliance layer
├── context/                        # Persistence layer (SQLite, ChromaDB)
├── models/                         # Data models
└── data/                           # Runtime data storage
```

---

## Configuration Reference

All LLM settings are in `config.py`:

| Setting | Value | Description |
|---------|-------|-------------|
| `CLAUDE_MODEL` | `claude-sonnet-4-5-20250514` | Claude Sonnet 4.5 |
| `CLAUDE_TEMPERATURE` | `0.7` | Response creativity (0-1) |
| `CLAUDE_MAX_TOKENS` | `8192` | Max output tokens per response |
| `LLM_PROVIDER` | `anthropic` | LLM provider |

### MCP Servers (configured in `config.py`)

| Server | Purpose | Agent(s) |
|--------|---------|----------|
| `pubchem` | Chemical compound data | ChemicalAgent |
| `biomcp` | PubMed, clinical trials, variants, genes | All agents |
| `literature` | PubMed articles and citations | LiteratureAgent |
| `data_analysis` | Statistics and molecular descriptors | DataAgent |
| `web_knowledge` | Wikipedia, clinical trials, gene/drug info | All agents |

### Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `use_specialized_agents` | `True` | Enable 5 specialized agents |
| `use_langgraph_orchestrator` | `True` | Enable LangGraph orchestration |
| `enable_reporting` | `True` | Enable report generation |
| `use_persistent_context` | `False` | SQLite/ChromaDB persistence |
| `use_governance_gateway` | `False` | Compliance gateway |

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

- Verify `.env` file exists in the `streamlit-app/` directory (not the repo root)
- Verify the key starts with `sk-ant-`
- Try setting directly: `set ANTHROPIC_API_KEY=sk-ant-...` (Windows) or `export ANTHROPIC_API_KEY=sk-ant-...` (Linux/Mac)
- Restart Streamlit after changing the key

### "MCP servers not available"

This is normal if MCP servers aren't installed. The system gracefully falls back to direct Claude LLM mode. To install, see Step 5 above.

### Import Errors

- Make sure your virtual environment is activated (`venv\Scripts\activate` on Windows)
- Run `pip install -r requirements.txt` again
- Check Python version: `python --version` (needs 3.10+)

### "Streamlit not found"

```bash
pip install streamlit
# Or use:
python -m streamlit run app.py
```

### Rate Limiting

Claude Sonnet 4.5 has API rate limits. If you get rate limit errors:
- Wait a moment and retry
- Reduce query complexity
- Check your Anthropic usage tier at [console.anthropic.com](https://console.anthropic.com/)

---

## License

BU Senior Design project - EMD Serono team.

## Resources

- **Anthropic Console:** https://console.anthropic.com/
- **Claude API Docs:** https://docs.anthropic.com/
- **MCP Documentation:** https://modelcontextprotocol.io/
- **Streamlit:** https://docs.streamlit.io/
- **LangChain:** https://python.langchain.com/
- **LangGraph:** https://langchain-ai.github.io/langgraph/
