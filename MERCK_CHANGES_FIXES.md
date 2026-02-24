# Changes Applied to merck_changes Branch

**Branch**: `fix/merck-changes` (PR target: `merck_changes`)
**Date**: 2026-02-23
**Author**: Moumit Bhattacharjee (fixes applied with Claude Code)

---

## Summary

This branch contains fixes for issues found on the `merck_changes` branch that prevented
the application from running correctly. All fixes are minimal and do not change intended
product behavior.

---

## Issues Fixed

### 1. Missing Core Python Dependencies (CRITICAL)

`langchain-anthropic`, `langchain-openai`, `anthropic`, and `openai` were listed in
`requirements.txt` but not installable due to `weasyprint` (requires system GTK/Cairo),
`chromadb`, and `sentence-transformers` (large optional deps) blocking `pip install`.

**What changed**: `streamlit-app/requirements.txt`
- Commented out optional packages (`chromadb`, `sentence-transformers`, `weasyprint`)
  with notes explaining when they are needed
- Core dependencies remain required and install cleanly

### 2. Agent Infinite Loop During Report Generation (CRITICAL)

When generating a competitive intelligence report with MCP tools connected, the agent
appeared to hang for 50-100+ seconds. The root cause was that Azure OpenAI GPT-4o
(and sometimes Claude) returns substantive answers without the exact `ACTION:`/`FINAL ANSWER:`
markers the agent expects. The agent would loop all 10 iterations, each time appending more
text to the prompt.

**What changed**: `streamlit-app/agent.py`
- Added early-exit: if the LLM gives a response >200 chars without tool-call markers,
  or gives 2 consecutive responses without tool calls, treat it as the final answer
- Added fallback: if iterations are exhausted but tool observations exist, return those
  observations instead of a generic error message

### 3. Outdated .env.example (MEDIUM)

The `.env.example` still referenced Ollama as the primary LLM, even though the system
was migrated to Anthropic Claude / Azure OpenAI.

**What changed**: `streamlit-app/.env.example`
- `ANTHROPIC_API_KEY` is now shown as the primary required variable
- `AZURE_OPENAI_API_KEY` is documented for Merck enterprise mode
- Ollama moved to legacy/optional section

### 4. Incomplete .gitignore (LOW)

Missing entries for runtime data files, `node_modules`, and Windows artifacts.

**What changed**: `.gitignore`
- Added `streamlit-app/data/`, `*.db`, `node_modules/`, `nul`

---

## Files Changed (full list)

| File | Description |
|------|-------------|
| `streamlit-app/agent.py` | Fix agent loop: early-exit on substantive LLM responses |
| `streamlit-app/requirements.txt` | Comment out optional deps that block pip install |
| `streamlit-app/.env.example` | Update to reflect Anthropic/Azure as primary configs |
| `.gitignore` | Add runtime data, node_modules, Windows artifacts |
| `docs/claude_fix_log.md` | Detailed fix log with root cause analysis |
| `MERCK_CHANGES_FIXES.md` | This file |

---

## What Was Verified Working (No Changes Needed)

- All 4 MCP servers (pubchem, literature, data_analysis, web_knowledge) start correctly
- `config_merck.py` loads properly and validates API keys
- `AzureChatOpenAI` client is correctly instantiated with Merck endpoint/deployment
- LangGraph orchestrator (`agents/orchestrator_agent.py`) imports and initializes
- All 5 specialized agents (chemical, clinical, literature, gene, data) import correctly
- Streamlit app starts on port 8501
- Configuration switching between Standard and Merck Enterprise works
- SSL workaround for literature MCP server is in place

---

## How to Verify (Merck Enterprise Mode)

```bash
# 1. Clone and checkout this branch
git clone https://github.com/moumit-b/BU-Senior-Design-EMD-Serono.git
cd BU-Senior-Design-EMD-Serono
git checkout fix/merck-changes

# 2. Set up Python environment
cd streamlit-app
python -m venv venv
venv\Scripts\activate              # Windows
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Edit .env and set:
#   AZURE_OPENAI_API_KEY=your-actual-azure-key

# 4. Launch
streamlit run app.py

# 5. In the sidebar, select "Merck Enterprise Configuration"
# 6. Verify sidebar shows: LLM Ready, Provider: Azure OpenAI / AWS Bedrock
# 7. Enter a query like:
#    "Generate a competitive intelligence report on PCSK9 inhibitors"
# 8. The agent should respond within ~10-15 seconds (not loop for 60+)
```

---

## Environment Variables

| Variable | Config Mode | Required | Notes |
|----------|------------|----------|-------|
| `ANTHROPIC_API_KEY` | Standard | Yes | Get at console.anthropic.com |
| `AZURE_OPENAI_API_KEY` | Merck Enterprise | Yes | Merck Azure OpenAI key |
| `AZURE_API_KEY` | Merck Enterprise | Alt | Alternative env var name |

---

## Commits on this Branch

```
55b3384 Fix: prevent agent tool-call loop from spinning on non-compliant LLM output
fd85697 Chore: add .gitignore entries for runtime data and node_modules
9a48207 Fix: update .env.example to match current Anthropic/Merck config
86505f6 Fix: comment out optional deps that break pip install
```

Each commit is small, focused, and independently reviewable.
