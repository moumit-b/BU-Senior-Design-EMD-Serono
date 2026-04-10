# Setup Instructions

Complete guide to running the Pharmaceutical Research Intelligence System from scratch on a new machine.

---

## What You Need

- **Python 3.10+** installed
- **Node.js 18+** installed (required for MCP server tools)
- **An Anthropic API key** with Claude Sonnet access — get one at https://console.anthropic.com/

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/moumit-b/BU-Senior-Design-EMD-Serono.git
cd BU-Senior-Design-EMD-Serono
```

---

## Step 2: Run the Installer

From the repo root, run:

```bash
python install.py
```

This single command handles everything:
- Creates a Python virtual environment (`streamlit-app/venv`)
- Installs all Python dependencies
- Runs `npm install` in all 9 Node.js MCP server directories
- Scaffolds a `streamlit-app/.env` file with documented slots for all required keys

> **Note:** `requirements.txt` is pip-only and cannot install Node.js dependencies.
> Always use `install.py` on a new machine — not `pip install -r requirements.txt` alone.

---

## Step 3: Fill In Your API Keys

Open `streamlit-app/.env` (created by the installer) and fill in:

```
# Required — LLM provider
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE

# Required for NCI clinical trials tools (nci_intervention_searcher, nci_biomarker_searcher)
# Free key at: https://clinicaltrialsapi.cancer.gov/
NCI_API_KEY=your_nci_key_here

# Required on corporate/Windows networks with SSL interception (e.g. Merck)
# BIOMCP_DISABLE_SSL=true
```

Optional keys (enable additional features):
```
# Tavily web search in the chat agent — free tier at https://tavily.com
# TAVILY_API_KEY=your_tavily_key_here
```

---

## Step 4: Launch the Application

Activate the virtual environment:

**Windows (Command Prompt):**
```cmd
cd streamlit-app
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
cd streamlit-app
venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
cd streamlit-app
source venv/bin/activate
```

Then start the app:

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**. You should see the sidebar showing **LLM Ready** and **MCPOrchestrator: active** in the Dev Log after the first query.

---

## Step 5: Run a Query

Type a question into the chat input. Try:

- `What is the molecular formula of aspirin?`
- `Explain the mechanism of action of ibuprofen`
- `What are the phases of clinical trials?`

The system routes your query through specialized agents (Chemical, Clinical, Literature, Gene, Data) and returns a synthesized answer.

---

## Step 6: Generate a Competitive Intelligence Report

Use the **Report Panel** (right side of the app) to generate full 18-section EMD-format Competitive Intelligence reports. Enter a drug name, click Generate, and the system will:

1. Dispatch specialized agents in parallel batches across 18 sections
2. Each agent queries real MCP data sources (PubChem, BioMCP, OpenFDA, ClinicalTrials.gov, medRxiv, etc.)
3. Synthesize findings into a structured markdown report
4. Offer a one-click markdown download

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ANTHROPIC_API_KEY not set` | Check that `.env` exists in `streamlit-app/` and the key starts with `sk-ant-` |
| `ModuleNotFoundError` | Make sure venv is activated; re-run `python install.py` |
| `streamlit: command not found` | Run `python -m streamlit run app.py` instead |
| MCP server `Connection closed` at startup | Run `python install.py` — `npm install` likely missing for that server |
| `nci_* tools fail` | Add `NCI_API_KEY` to `.env` (free at clinicaltrialsapi.cancer.gov) |
| SSL certificate errors in biomcp | Add `BIOMCP_DISABLE_SSL=true` to `.env` (common on Merck/corporate networks) |
| WeasyPrint PDF export fails | Install system GTK3 libraries (see `requirements.txt` for platform-specific instructions) |
| Rate limit errors | Wait a moment and retry, or check your Anthropic usage tier |

---

## MCP Servers

The system connects to 9 MCP servers at startup. All are free and require no API keys except where noted:

| Server | Data Source | Requires |
|--------|-------------|----------|
| pubchem | PubChem (NIH) — compound structures, properties | Nothing |
| biomcp | PubMed, ClinicalTrials.gov, OpenFDA, genes, variants | `NCI_API_KEY` for nci_* tools |
| literature | PubMed articles and abstracts | Nothing |
| data_analysis | Local statistics and molecular descriptors | Nothing |
| web_knowledge | Wikipedia, DrugBank, clinical trials, gene info | Nothing |
| medrxiv | medRxiv preprints | Nothing |
| biorxiv | bioRxiv preprints | Nothing |
| opentargets | Open Targets — target identification and drug associations | Nothing |
| stringdb | STRING-db — protein-protein interaction networks | Nothing |

---

## Architecture

| Agent | Domain | MCP Sources |
|-------|--------|-------------|
| ChemicalAgent | Compounds, structures, ADMET | pubchem, biomcp |
| ClinicalAgent | Trials, FDA approvals, adverse events | biomcp |
| LiteratureAgent | PubMed, preprints, citations | literature, medrxiv |
| GeneAgent | Genes, targets, pathways | biomcp |
| DataAgent | Statistics, analysis | data_analysis |
