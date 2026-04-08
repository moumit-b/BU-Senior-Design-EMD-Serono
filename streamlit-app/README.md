# Pharmaceutical Research Intelligence System

A multi-agent orchestration system for pharmaceutical research powered by **Model Context Protocol (MCP)** servers and **Claude Sonnet 4.5**. Specialized AI agents gather real data from biomedical databases (PubMed, ClinicalTrials.gov, Open Targets, PubChem, STRING-db, medRxiv, bioRxiv), then synthesize expert analysis. All MCP tool calls flow through the **Context Forge Gateway** for governance, audit logging, compliance, and rate limiting.

---

## Architecture Overview

The system has two primary execution paths: **Chat** (interactive Q&A) and **Report Generation** (structured EMD-format reports). Both share the same MCP infrastructure and specialized agents.

### Chat Path (Interactive Q&A)

```
User Query
    |
    v
Streamlit UI (app.py)
    |
    v
MCPAgent (agent.py) — LangChain tool-calling loop
    |
    +---> MCP Tools (via LangChain StructuredTool wrappers)
    |         |
    |         v
    |     Context Forge Gateway (governance/gateway.py)
    |         |
    |         v
    |     MCP Servers: BioMCP, PubChem, Literature, Open Targets,
    |                  STRING-db, medRxiv, bioRxiv
    |
    v
Claude Sonnet 4.5 synthesizes tool results into response
```

### Report Generation Path (Multi-Agent Orchestration)

```
User clicks "Generate Report" in Report Panel
    |
    v
report_panel.py retrieves MCPOrchestrator from session state
    |
    v
ReportAgent (agents/report_agent.py)
    |
    |--- Creates 5 specialized agent instances (shared MCP orchestrator + LLM)
    |--- Maps 18 EMD sections to relevant agents
    |--- Dispatches ALL 18 sections in parallel (asyncio.gather)
    |
    |   For each section (e.g., Section 9: Competitive Landscape):
    |       |
    |       v
    |   _gather_agent_data() — dispatches to mapped agents IN PARALLEL
    |       |
    |       +---> ClinicalAgent.process()
    |       |         |--- _call_mcp_tools_parallel():
    |       |         |       trial_searcher, openfda_adverse_searcher,
    |       |         |       openfda_approval_searcher, openfda_label_searcher,
    |       |         |       nci_intervention_searcher, disease_getter
    |       |         |--- LLM synthesizes MCP data into expert analysis
    |       |         +---> AgentResult { mcp_data, mcps_used, answer }
    |       |
    |       +---> ChemicalAgent.process()
    |       |         |--- _call_mcp_tools_parallel():
    |       |         |       search_compounds_by_name, drug_getter,
    |       |         |       openfda_label_searcher
    |       |         +---> AgentResult { mcp_data, mcps_used, answer }
    |       |
    |       +---> LiteratureAgent.process()
    |                 |--- _call_mcp_tools_parallel():
    |                 |       article_searcher, search_pubmed,
    |                 |       search_medrxiv_preprints, search_biorxiv_preprints
    |                 +---> AgentResult { mcp_data, mcps_used, answer }
    |       |
    |       v
    |   _synthesize_section() — LLM writes section using:
    |       - Real MCP data from all agents
    |       - Agent expert analyses
    |       - EMD template structure
    |       - Conversation context
    |
    v
_compile_report() — stitches 18 sections into final EMD-formatted document
    |
    v
Downloadable Markdown Report
```

### MCP Tool Execution Flow (All Paths)

```
Agent._call_mcp_tools_parallel([(tool1, params), (tool2, params), ...])
    |
    v
asyncio.gather() — parallel execution
    |
    v
BaseAgent._call_mcp_tool(tool_name, params)
    |
    v
MCPOrchestrator.route_tool_call(tool_name, params, context)
    |--- L1 cache check (avoids duplicate calls)
    |--- _select_optimal_mcp() — routes to server that has the tool
    |        Uses _tool_to_servers index (built at construction)
    |        Filters by health status, selects by performance score
    |--- _call_mcp_tool() — executes via gateway or direct
    |        |
    |        v
    |    Context Forge Gateway (if enabled)
    |        |--- Rate limiting
    |        |--- Compliance check
    |        |--- Audit logging
    |        v
    |    MCPToolWrapper.call_tool(tool_name, params)
    |        |
    |        v
    |    MCP Server (biomcp, pubchem, opentargets, etc.)
    |
    v
(result, PerformanceFeedback) — recorded for adaptive routing
```

---

## Specialized Agents and Their MCP Tools

Each agent calls real MCP tools in parallel, then synthesizes the data with LLM:

| Agent | MCP Servers | Tools | Domain |
|-------|------------|-------|--------|
| **ChemicalAgent** | PubChem, BioMCP | `search_compounds_by_name`, `drug_getter`, `openfda_label_searcher` | Compounds, molecular properties, drug safety |
| **ClinicalAgent** | BioMCP | `trial_searcher`, `openfda_adverse_searcher`, `openfda_approval_searcher`, `openfda_label_searcher`, `nci_intervention_searcher`, `disease_getter` | Clinical trials, FDA data, regulatory |
| **GeneAgent** | BioMCP, Open Targets, STRING-db | `gene_getter`, `search_opentargets`, `get_protein_interactions`, `nci_biomarker_searcher`, `variant_searcher` | Genes, variants, protein interactions, biomarkers |
| **LiteratureAgent** | BioMCP, Literature, medRxiv, bioRxiv | `article_searcher`, `search_pubmed`, `search_medrxiv_preprints`, `search_biorxiv_preprints` | Publications, preprints, citations |
| **DataAgent** | (LLM-only) | Statistical analysis prompts | Data analysis, statistics |
| **ReportAgent** | All (via delegation) | Orchestrates all agents above | EMD-format report generation |

### 3-Phase Agent Pattern

Every specialized agent follows the same pattern:

1. **Phase 1 — Gather**: Call MCP tools in parallel via `_call_mcp_tools_parallel()`
2. **Phase 2 — Synthesize**: Feed real MCP data into LLM for expert analysis
3. **Phase 3 — Fallback**: If orchestrator is None or all tools fail, produce LLM-only output

---

## Report Generation

### EMD Biopharma R&D Format

Reports follow the **EMD Biopharma R&D Competitive Intelligence** template (`docs/EMD_report_format.md`) with 18 sections:

| Section | Title | Agents Used |
|---------|-------|-------------|
| 1 | Executive Summary & 6R Framework | Clinical, Gene |
| 2 | Target & Biomarker Information | Gene, Chemical |
| 3 | Molecular Pathways & Mechanism | Gene |
| 4 | Tumor Microenvironment & Mutation Profile | Gene |
| 5 | Biomarker Landscape | Gene, Clinical |
| 6 | Target Prevalence | Gene |
| 7 | Assay Landscape | Chemical |
| 8 | Regulatory & Commercial Overview | Clinical |
| **9** | **Competitive Landscape** | **Clinical, Chemical, Literature** |
| 10 | Vendors & External Partners | Chemical |
| 11 | Target Landscape & Development Trends | Clinical, Gene |
| 12 | Target Characteristics (Molecular Data) | Gene |
| 13 | Scientific Textual Insights | Literature |
| 14 | Experimental Materials Availability | Chemical |
| 15 | Key Opinion Leaders | Literature |
| 16 | Patent Landscape | Chemical, Clinical |
| **17** | **Risks, Gaps & Recommended Next Steps** | **Clinical, Gene, Literature** |
| 18 | References & Appendices | Literature |

### How Report Generation Works

1. User discusses a drug/target in chat (e.g., "Tell me about Pembrolizumab")
2. The Report Panel auto-detects the drug from conversation via `drug_extractor.py`
3. User clicks **"Generate Report"**
4. `ReportAgent` creates 5 specialized agent instances sharing the live `MCPOrchestrator`
5. All 18 sections are dispatched **in parallel** via `asyncio.gather()`
6. Each section dispatches to 1-3 agents (also in parallel)
7. Each agent calls 3-6 MCP tools (also in parallel)
8. Real MCP data + agent analyses are synthesized by LLM into EMD-formatted sections
9. All sections are compiled into a downloadable Markdown report

### ReportAgent is Self-Contained

`ReportAgent` extends `BaseAgent` and can be exported to any application:

```python
from agents.report_agent import ReportAgent
from agents.base_agent import AgentTask, AgentContext

report_agent = ReportAgent(
    mcp_orchestrator=your_orchestrator,  # MCPOrchestrator instance
    config_data=your_config,             # LLM configuration
)

task = AgentTask(
    task_id="report_001",
    query="Generate CI report for Pembrolizumab",
    task_type="report_generation",
    parameters={
        "drug_name": "Pembrolizumab",
        "report_type": "competitive_intelligence",
    },
)

context = AgentContext(
    session_id="session_001",
    user_id="analyst_001",
    research_goal="Competitive intelligence on Pembrolizumab",
)

result = await report_agent.process(task, context)
report_markdown = result.result_data["report"]
```

---

## Context Forge Gateway (Governance)

All MCP tool calls are mediated through the Context Forge Gateway:

- **Rate Limiting**: Prevents API overload on MCP servers
- **Compliance Checks**: Validates tool calls against policy rules
- **Audit Logging**: Records every tool call with timestamps, parameters, results
- **Health Monitoring**: Tracks MCP server availability and response times
- **Performance Tracking**: Enables adaptive routing (MCPOrchestrator learns which servers are fastest)

The gateway is initialized in `app.py` and attached to the `MCPOrchestrator`, which is stored in `st.session_state` and shared with all agents.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for MCP servers)
- **Anthropic API Key** with Claude Sonnet 4.5 access — get one at [console.anthropic.com](https://console.anthropic.com/)

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

### 4. Set Your Anthropic API Key

Create a `.env` file inside `streamlit-app/`:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Or set as environment variable:
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE    # Linux/Mac
set ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE       # Windows CMD
$env:ANTHROPIC_API_KEY = "sk-ant-api03-YOUR-KEY-HERE"  # PowerShell
```

### 5. (Optional) Install MCP Servers

The system works without MCP servers in **direct LLM mode**. To enable MCP tool access for live data:

```bash
# From the repository root (one level up from streamlit-app)
cd ../servers/pubchem && npm install
cd ../servers/literature && npm install
cd ../servers/data_analysis && npm install
cd ../servers/web_knowledge && npm install

# BioMCP (Python-based)
pip install biomcp-python
```

### 6. Launch the Application

**Windows:**
```cmd
run.bat
```

**Any platform:**
```bash
streamlit run app.py
```

Opens at **http://localhost:8501**.

---

## Using the Application

### Chat (Left Panel)

Type any pharmaceutical research question:

- "What is the molecular formula of aspirin?"
- "Find clinical trials for BRCA gene therapies"
- "Analyze the competitive landscape for GLP-1 receptor agonists"

The system calls relevant MCP tools and synthesizes results.

### Report Generation (Right Panel)

1. Chat about a drug or target (e.g., "Tell me about revuforj")
2. The Report Panel auto-detects the subject
3. Select report type (Competitive Intelligence)
4. Click **"Generate Report"**
5. Download the EMD-formatted Markdown report

---

## Project Structure

```
streamlit-app/
├── app.py                          # Streamlit entry point + MCPOrchestrator init
├── agent.py                        # MCPAgent (LangChain chat tool-calling)
├── config.py                       # Model, MCP server, feature flag config
├── config_manager.py               # Multi-profile configuration manager
├── mcp_tools.py                    # MCP server connections + MCPToolWrapper
├── run.bat                         # Windows startup script
├── requirements.txt                # Python dependencies
├── .env                            # API keys (create this - not in git)
│
├── agents/                         # Specialized agents (3-phase MCP pattern)
│   ├── base_agent.py               # Abstract base + MCP helper methods
│   ├── chemical_agent.py           # PubChem, BioMCP tools
│   ├── clinical_agent.py           # BioMCP clinical/regulatory tools
│   ├── gene_agent.py               # BioMCP, Open Targets, STRING-db tools
│   ├── literature_agent.py         # BioMCP, Literature, medRxiv, bioRxiv tools
│   ├── data_agent.py               # Statistical analysis (LLM-only)
│   ├── report_agent.py             # Multi-agent report orchestrator (18 sections)
│   └── orchestrator_agent.py       # LangGraph multi-agent orchestrator (chat)
│
├── orchestration/                  # MCP routing and orchestration
│   ├── mcp_orchestrator.py         # Tool-to-server routing, caching, performance
│   ├── agent_orchestrator.py       # Agent routing & task decomposition
│   ├── performance_kb.py           # Bidirectional learning knowledge base
│   ├── session_manager.py          # Research session memory
│   └── tool_composer.py            # Dynamic tool composition
│
├── ui/                             # UI components
│   └── report_panel.py             # Report generation panel (right column)
│
├── reporting/                      # Report utilities
│   ├── drug_extractor.py           # Drug/target detection from conversation
│   └── chat_report_generator.py    # Legacy single-prompt generator (fallback)
│
├── governance/                     # Context Forge Gateway
│   └── gateway.py                  # Rate limiting, compliance, audit, health
│
├── utils/                          # Utilities
│   ├── llm_factory.py              # Centralized LLM factory (multi-provider)
│   └── tavily_tool.py              # Tavily web search integration
│
├── models/                         # Data models (performance, sessions)
├── context/                        # Persistence layer (SQLite, ChromaDB)
├── docs/                           # Documentation
│   └── EMD_report_format.md        # 18-section EMD report template
└── data/                           # Runtime data storage
```

---

## MCP Servers Reference

| Server | Tools | Purpose |
|--------|-------|---------|
| `biomcp` | `article_searcher`, `trial_searcher`, `gene_getter`, `drug_getter`, `variant_searcher`, `disease_getter`, `openfda_*`, `nci_*` | Core biomedical data (22 tools) |
| `pubchem` | `search_compounds_by_name`, `get_compound_properties` | Chemical compound data |
| `literature` | `search_pubmed`, `get_pubmed_abstract`, `search_by_doi` | PubMed literature |
| `opentargets` | `search_opentargets`, `get_target_associations`, `get_disease_associations` | Target-disease associations |
| `stringdb` | `get_protein_interactions`, `get_interaction_partners` | Protein interaction networks |
| `medrxiv` | `search_medrxiv_preprints`, `get_medrxiv_paper`, `get_recent_medrxiv` | Medical preprints |
| `biorxiv` | `search_biorxiv_preprints`, `get_biorxiv_paper`, `get_recent_biorxiv` | Biology preprints |

---

## Configuration Profiles

The system supports multiple LLM configurations via `config_manager.py`:

| Profile | Provider | Model | Use Case |
|---------|----------|-------|----------|
| **Standard** | Anthropic | Claude Sonnet 4.5 | Open-source development |
| **Merck Enterprise** | Azure OpenAI / AWS Bedrock | GPT-4o / Claude 3.5 | Enterprise deployment |
| **Ollama** | Local | qwen3:235b-thinking | Offline/local development |

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Verify `.env` file exists in `streamlit-app/` (not repo root)
- Key should start with `sk-ant-`
- Restart Streamlit after changing

### "MCP servers not available"
Normal if MCP servers aren't installed. Falls back to direct LLM mode.

### Rate Limiting
Claude Sonnet 4.5 has API rate limits. Wait and retry, or check your tier at [console.anthropic.com](https://console.anthropic.com/).

---

## License

BU Senior Design project — EMD Serono team.

## Resources

- **Anthropic Console:** https://console.anthropic.com/
- **Claude API Docs:** https://docs.anthropic.com/
- **MCP Documentation:** https://modelcontextprotocol.io/
- **Streamlit:** https://docs.streamlit.io/
- **LangChain:** https://python.langchain.com/
- **LangGraph:** https://langchain-ai.github.io/langgraph/
