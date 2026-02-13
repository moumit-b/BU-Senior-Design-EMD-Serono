# Setup Instructions

Complete guide to running the Pharmaceutical Research Intelligence System from scratch on a new machine.

---

## What You Need

- **Python 3.10+** installed
- **Node.js 18+** installed (only if you want MCP server tools)
- **An Anthropic API key** with Claude Sonnet 4.5 access

Get your API key at: https://console.anthropic.com/

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/moumit-b/BU-Senior-Design-EMD-Serono.git
cd BU-Senior-Design-EMD-Serono
```

---

## Step 2: Set Up the Python Environment

```bash
cd streamlit-app
python -m venv venv
```

Activate the virtual environment:

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs LangChain, Anthropic SDK, Streamlit, LangGraph, and all other dependencies.

---

## Step 4: Add Your Anthropic API Key

Create a file called `.env` inside the `streamlit-app/` folder:

**Windows (Command Prompt):**
```cmd
echo ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE > .env
```

**macOS / Linux:**
```bash
echo "ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE" > .env
```

**Or manually:** create a file named `.env` in `streamlit-app/` with this single line:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Replace `sk-ant-api03-YOUR-KEY-HERE` with your actual key from https://console.anthropic.com/.

---

## Step 5: Launch the Application

**Windows:**
```cmd
run.bat
```

**Any platform:**
```bash
streamlit run app.py
```

The app will open automatically in your browser at **http://localhost:8501**.

You should see:
- Sidebar showing **LLM Ready: claude-sonnet-4-5-20250514**
- A chat input at the bottom of the page

---

## Step 6: Run a Query

Type a question into the chat input. Try one of these:

- `What is the molecular formula of aspirin?`
- `Explain the mechanism of action of ibuprofen`
- `What are the phases of clinical trials?`
- `How does CRISPR gene editing work?`

The system will route your query through the appropriate specialized agents (Chemical, Clinical, Literature, Gene, Data) and return a synthesized answer powered by Claude Sonnet 4.5.

---

## Step 7: Generate a Competitive Intelligence Report

Enter a complex, multi-domain query that triggers multiple agents. For example:

```
Analyze the competitive landscape for GLP-1 receptor agonists in diabetes treatment,
including clinical trial status, gene targets, molecular properties, and recent publications.
```

Or:

```
Generate a competitive intelligence report on PCSK9 inhibitors: compare molecular
properties, review clinical trials for evolocumab and alirocumab, analyze the PCSK9
gene target, and summarize key research publications.
```

The orchestrator will:
1. Analyze the query and extract keywords
2. Assign multiple agents (e.g., Chemical + Clinical + Gene + Literature)
3. Each agent generates a specialized analysis using Claude Sonnet 4.5
4. Claude synthesizes all agent results into a comprehensive report

The final response in the chat is your competitive intelligence report. You can copy it directly from the UI.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ANTHROPIC_API_KEY not set` | Check that `.env` exists in `streamlit-app/` and the key starts with `sk-ant-` |
| `ModuleNotFoundError` | Make sure venv is activated and run `pip install -r requirements.txt` |
| `streamlit: command not found` | Run `python -m streamlit run app.py` instead |
| `MCP servers not available` | Normal - the system works without MCP servers using direct Claude LLM mode |
| Rate limit errors | Wait a moment and retry, or check your Anthropic usage tier |

---

## Architecture

All five specialized agents and the LangGraph orchestrator use **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250514`):

| Agent | Domain | Example Queries |
|-------|--------|-----------------|
| ChemicalAgent | Compounds, structures, ADMET | "molecular weight of caffeine" |
| ClinicalAgent | Trials, FDA, adverse events | "phase 3 trials for pembrolizumab" |
| LiteratureAgent | PubMed, citations, research | "recent papers on CAR-T therapy" |
| GeneAgent | Genes, variants, pathways | "BRCA1 mutations and cancer risk" |
| DataAgent | Statistics, analysis, trends | "compare efficacy data across studies" |
