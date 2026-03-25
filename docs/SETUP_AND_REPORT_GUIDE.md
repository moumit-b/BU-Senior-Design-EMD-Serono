# Setup & Report Generation Guide

Complete guide for running the Pharmaceutical Research Platform with Context Forge governance on any machine.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment A: Merck Network (Anthropic API)](#environment-a-merck-network-anthropic-api)
3. [Environment B: Local Machine (Ollama + qwen3:235b-thinking)](#environment-b-local-machine-ollama)
4. [Running the Application](#running-the-application)
5. [Generating a Research Report](#generating-a-research-report)
6. [Context Forge Governance](#context-forge-governance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### All Environments

```bash
# Clone the repository
git clone https://github.com/moumit-b/BU-Senior-Design-EMD-Serono.git
cd BU-Senior-Design-EMD-Serono

# Switch to the Context Forge branch
git checkout feature/context-forge-implementation

# Navigate to the Streamlit app
cd streamlit-app

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Runtime |
| Node.js | 18+ | MCP servers (PubChem, Literature, etc.) |
| npm | 9+ | MCP server dependencies |
| Git | 2.30+ | Version control |

### Install MCP Server Dependencies

```bash
# From the repo root
cd servers/pubchem && npm install && cd ../..
cd servers/literature && npm install && cd ../..
cd servers/data_analysis && npm install && cd ../..
cd servers/web_knowledge && npm install && cd ../..
```

---

## Environment A: Merck Network (Anthropic API)

This configuration uses Anthropic Claude models via API key. Use this when you have an Anthropic API key (whether on Merck network or any machine with internet access).

### Step 1: Set Up Environment Variables

Create a `.env` file in the `streamlit-app/` directory:

```bash
# streamlit-app/.env

# --- Anthropic (Standard Profile) ---
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE

# --- LLM Provider ---
LLM_PROVIDER=anthropic
```

### Step 2: Verify Configuration

```bash
cd streamlit-app
python -c "
from config_manager import config_manager
data = config_manager.load_configuration('standard')
print(f'Profile: {data[\"profile\"].display_name}')
print(f'Provider: {data.get(\"llm_provider\")}')
print(f'Model: {data.get(\"claude_model\")}')
print(f'API Key Set: {bool(data.get(\"anthropic_api_key\"))}')
"
```

Expected output:
```
Profile: Standard Configuration
Provider: anthropic
Model: claude-sonnet-4-5-20250514
API Key Set: True
```

### Step 3: Run the Application

```bash
streamlit run app.py
```

Select **"Standard Configuration"** from the sidebar dropdown.

### Merck Enterprise Profile (Azure/Bedrock)

If you have access to Merck's Azure OpenAI endpoint:

```bash
# streamlit-app/.env
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_API_KEY=your-azure-key
```

Select **"Merck Enterprise Configuration"** from the sidebar.

---

## Environment B: Local Machine (Ollama)

This configuration runs entirely locally with no API key required. Uses Ollama to serve the `qwen3:235b-thinking` model.

### Step 1: Install Ollama

Download and install from: https://ollama.com

Verify installation:
```bash
ollama --version
```

### Step 2: Pull the Model

```bash
# Pull qwen3:235b-thinking (large model - requires significant RAM/VRAM)
ollama pull qwen3:235b-thinking

# Alternative smaller models if hardware is limited:
# ollama pull qwen3:8b
# ollama pull llama3.2
# ollama pull deepseek-r1:8b
```

**Hardware Requirements for qwen3:235b-thinking:**
- RAM: 128GB+ recommended (model is ~140GB)
- If using GPU: Multiple GPUs with 48GB+ VRAM each
- Disk: 150GB+ free space for model weights

**For smaller hardware**, override the model in `.env`:
```bash
# streamlit-app/.env
OLLAMA_MODEL=qwen3:8b
# or
OLLAMA_MODEL=llama3.2
```

### Step 3: Start Ollama Server

```bash
# Start Ollama (if not already running as a service)
ollama serve
```

Verify it's running:
```bash
curl http://localhost:11434/api/tags
```

### Step 4: Configure Environment

Create or update `streamlit-app/.env`:

```bash
# streamlit-app/.env

# --- Ollama Configuration ---
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:235b-thinking
OLLAMA_TIMEOUT=600
```

### Step 5: Verify Configuration

```bash
cd streamlit-app
python -c "
from config_manager import config_manager
data = config_manager.load_configuration('ollama')
print(f'Profile: {data[\"profile\"].display_name}')
print(f'Provider: {data.get(\"llm_provider\")}')
print(f'Model: {data.get(\"ollama_model\")}')
print(f'Base URL: {data.get(\"ollama_base_url\")}')
"
```

Expected output:
```
Profile: Local Ollama Configuration
Provider: ollama
Model: qwen3:235b-thinking
Base URL: http://localhost:11434
```

### Step 6: Run the Application

```bash
streamlit run app.py
```

Select **"Local Ollama Configuration"** from the sidebar dropdown.

---

## Running the Application

### Start Command

```bash
cd streamlit-app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### Sidebar Configuration

The sidebar shows three configuration profiles:

| Profile | LLM Provider | API Key Required |
|---------|-------------|-----------------|
| Standard Configuration | Anthropic Claude | Yes (`ANTHROPIC_API_KEY`) |
| Merck Enterprise | Azure OpenAI / Bedrock | Yes (`AZURE_OPENAI_API_KEY`) |
| Local Ollama | Ollama (local) | No |

### Verifying MCP Connections

After the app loads, expand **"Available Tools"** to see connected MCP servers:
- `pubchem` - Chemical compound data
- `biomcp` - Biomedical research (PubMed, clinical trials)
- `literature` - PubMed articles and citations
- `data_analysis` - Statistics and correlations
- `web_knowledge` - Wikipedia, clinical trials, genes

### Context Forge Governance

Expand **"Context Forge Governance"** to see live governance metrics:
- Total Calls / Successful / Compliance Blocks / Governed Servers

For full governance dashboard, navigate to the **Governance Dashboard** page.

---

## Generating a Research Report

### Method 1: Interactive Chat Query

1. Open the app at `http://localhost:8501`
2. Select your configuration profile from the sidebar
3. In the chat input, type a research query, for example:

**Chemical Research:**
```
What is the molecular formula of aspirin and what are its key pharmacological properties?
```

**Clinical Trial Research:**
```
Find Phase 3 clinical trials for BRCA1 inhibitors and summarize their outcomes
```

**Competitive Intelligence:**
```
Compare the efficacy of PARP inhibitors (Olaparib, Rucaparib, Niraparib) for ovarian cancer treatment
```

4. The agent will:
   - Route the query to the appropriate specialized agent
   - Call relevant MCP servers through the Context Forge Gateway
   - Synthesize results into a comprehensive response
   - All calls are audited and compliance-checked

5. View the **Agent Reasoning Process** expander to see intermediate tool calls

### Method 2: Dual Orchestration Lab (Advanced)

For more detailed reports with bidirectional learning:

1. Navigate to **Dual Orchestration Lab** page
2. Click **"Connect to MCPs"** to establish governed connections
3. Use preset scenarios or custom queries:
   - **Scenario 1:** Intelligent Query Routing (single-agent)
   - **Scenario 2:** Multi-Step Workflow (multi-agent)
   - **Scenario 3:** Research Session (multi-turn context)
4. View the **Learning Dashboard** tab for performance insights
5. Check the **Governance Dashboard** page for audit logs

### Method 3: Multi-Turn Research Session

For comprehensive reports that build on previous context:

1. Go to **Dual Orchestration Lab** > **Research Sessions** tab
2. Click **"New Session"** and set a research goal
3. Ask a sequence of related queries:
   ```
   Query 1: "What is BRCA1?"
   Query 2: "Find BRCA1 inhibitors"
   Query 3: "Compare their clinical trial outcomes"
   Query 4: "What are the safety profiles?"
   ```
4. The session maintains context across queries
5. Each query builds on discoveries from previous ones

### Exporting Results

Currently results are displayed in the Streamlit UI. To export:

1. **Copy from UI:** Select and copy the response text from the chat
2. **Markdown Export:** The responses are formatted in Markdown - paste into any Markdown editor
3. **Audit Trail:** Check the Governance Dashboard for a complete log of all queries and tool calls
4. **Session Data:** Research sessions are persisted in SQLite (`data/sessions.db`)

---

## Context Forge Governance

### What It Does

Every MCP tool call flows through the Context Forge Gateway:

```
User Query
  -> Agent Orchestrator (selects specialized agent)
    -> MCP Orchestrator (selects optimal MCP server)
      -> Context Forge Gateway
        -> Rate Limiter (100 req/hr per user)
        -> Compliance Engine (PII/PHI detection)
        -> Service Registry (health check)
        -> Audit Logger (immutable trail)
        -> MCP Server (actual tool call)
        -> Post-validation (response compliance)
        -> Source Attribution (data lineage)
      <- Governed Response
```

### Governance Dashboard

Navigate to the **Governance Dashboard** page to see:
- **Total Calls / Success Rate / Compliance Blocks** - Top-level metrics
- **Service Health** - Real-time health of each MCP server
- **Compliance Violations** - Any PII/PHI detection events
- **Audit Logs** - Complete immutable log of all tool calls
- **Rate Limiting** - Per-user request counts and remaining quota

### Compliance Rules

The system automatically detects and blocks:
- **PII:** Social Security Numbers, credit card numbers, email addresses
- **PHI:** Medical Record Numbers, dates of birth, patient IDs
- **Prohibited Terms:** "internal pipeline", "proprietary", "confidential", "trade secret", "under NDA"

---

## Troubleshooting

### Anthropic API Issues

```
Error: ANTHROPIC_API_KEY not set
```
**Fix:** Ensure `.env` file exists in `streamlit-app/` with valid key.

### Ollama Connection Issues

```
Error: Connection refused http://localhost:11434
```
**Fix:** Run `ollama serve` in a separate terminal.

```
Error: model 'qwen3:235b-thinking' not found
```
**Fix:** Run `ollama pull qwen3:235b-thinking` first. Or set a smaller model in `.env`:
```
OLLAMA_MODEL=llama3.2
```

### Ollama Timeout

```
Error: Tool timed out after 60 seconds
```
**Fix:** Large models need more time. Set `OLLAMA_TIMEOUT=600` in `.env`.

### MCP Server Connection Failures

```
MCP servers not available
```
**Fix:** Ensure Node.js is installed and MCP server dependencies are set up:
```bash
cd servers/pubchem && npm install
cd servers/literature && npm install
```

### Missing Python Packages

```
ImportError: langchain-ollama is required
```
**Fix:**
```bash
pip install -r requirements.txt
```

### Port Already in Use

```
Address already in use (port 8501)
```
**Fix:**
```bash
streamlit run app.py --server.port 8502
```
