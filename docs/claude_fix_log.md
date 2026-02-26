# Fix Log - fix/merck-changes branch

Branch: `fix/merck-changes` (based on `origin/merck_changes`)
Date: 2026-02-23

---

## Issues Found

### 1. Missing Python packages (CRITICAL)
**Symptom**: `langchain-anthropic`, `langchain-openai`, `anthropic`, and `openai` are listed
in `requirements.txt` but were not installed in the venv. App would crash at runtime when
trying to initialize the LLM (lazy import in `utils/llm_factory.py`).

**Root cause**: Packages were added to requirements.txt but never installed in the existing
venv. Anyone running `pip install -r requirements.txt` would also fail on `weasyprint`
(needs system GTK/Cairo) and `chromadb`/`sentence-transformers` (very large, and the feature
using them is disabled via `use_persistent_context: False`).

**Fix**: Installed the 4 core packages. Commented out the 3 optional packages in
`requirements.txt` with clear notes about when/why to install them.

### 2. Outdated .env.example
**Symptom**: `.env.example` still referenced Ollama as the primary LLM provider. The system
was migrated to Anthropic Claude Sonnet 4.5, but `.env.example` was never updated.

**Fix**: Rewrote `.env.example` to show `ANTHROPIC_API_KEY` as the primary required variable,
`AZURE_OPENAI_API_KEY` for Merck mode, and Ollama as legacy/optional.

### 3. Missing .gitignore entries
**Symptom**: `streamlit-app/data/` (runtime SQLite DBs, vector stores), `*.db` files,
`node_modules/` directories, and the Windows `nul` artifact were not in `.gitignore`.

**Fix**: Added entries for all of the above.

### 4. Agent infinite loop during report generation (CRITICAL)
**Symptom**: When generating a competitive intelligence report (complex multi-keyword query)
with MCP tools connected, the agent appears to enter an infinite loop. The UI spinner runs
for 50-100+ seconds before eventually returning a generic "couldn't find a complete answer"
message.

**Root cause**: `MCPAgent.query()` in `agent.py` uses a 10-iteration agentic loop. The LLM
must respond with either `ACTION: tool_name / INPUT: {...}` or `FINAL ANSWER: ...` markers.
Azure OpenAI GPT-4o (and sometimes Claude) often returns a substantive answer *without*
these markers. When this happens:
1. The agent doesn't recognize it as a final answer
2. It appends the response + a nudge message to the conversation
3. It loops again with an ever-growing prompt
4. 10 iterations × 5-10s API latency = 50-100+ seconds of apparent hanging
5. Finally returns a useless "couldn't find answer" message despite having gotten one

**Fix**: Added two safeguards in `agent.py`:
- If the LLM returns a response >200 chars without ACTION/FINAL ANSWER markers, or gives
  2 consecutive responses without tool calls, treat the response as the final answer
- If iterations are exhausted but tool observations exist, return those observations
  instead of a generic error

### 5. BioMCP SSL Certificate Issue (HIGH)
**Symptom**: BioMCP was disabled because it failed to make HTTPS calls on the Merck corporate network. It would throw SSL verification errors when trying to connect to NCBI, clinicaltrials.gov, etc.

**Root cause**: Merck's network uses a proxy that injects a self-signed certificate. BioMCP's HTTP client (using `httpx`) doesn't recognize this certificate by default.

**Fix**:
1. Created `servers/bio/run_biomcp.py` as a wrapper that can manage SSL settings.
2. Created `servers/bio/_biomcp_no_ssl.py` to monkeypatch BioMCP's internal `http_client` and force `verify=False` when requested.
3. Re-enabled `biomcp` in `streamlit-app/config.py`.
4. Users can now set `BIOMCP_DISABLE_SSL=true` in their `.env` to bypass these errors on corporate networks.

### 6. System Unification to Anthropic Models (HIGH)
**Symptom**: Maintaining multiple LLM providers (Azure, Bedrock, Ollama, Anthropic) created architectural complexity and inconsistent tool-calling behavior across different user profiles.

**Root cause**: Different LLMs (especially smaller local ones or different Azure deployments) have varying levels of compliance with the `ACTION/INPUT` format, leading to frequent failures in the research loop.

**Fix**: Consolidated the system to use Anthropic Claude 3.5 Sonnet as the unified research engine for all profiles.
1. Updated `llm_factory.py` to simplify initialization.
2. Updated `config_manager.py` to point the Merck profile to the Anthropic engine.
3. Updated UI and documentation to reflect the single API key requirement (`ANTHROPIC_API_KEY`).
4. Kept Ollama as an optional local fallback for simple testing, but removed it from the primary research path.

---

## What Was NOT Broken

- All 4 MCP servers (pubchem, literature, data_analysis, web_knowledge) start correctly
- All Python module imports succeed (agents, orchestration, models, etc.)
- Streamlit app starts and serves on port 8501
- LLM validation correctly reports "ANTHROPIC_API_KEY not set" when no key is present
- Agent error handling works (ValueError with helpful message when no API key)
- Node dependencies (node_modules) already installed for all MCP servers
- Config manager, config.py, config_merck.py all load correctly

---

## Files Changed

| File | Change |
|------|--------|
| `streamlit-app/requirements.txt` | Comment out optional deps (chromadb, sentence-transformers, weasyprint) |
| `streamlit-app/config.py` | Re-enable BioMCP with SSL fix wrapper |
| `servers/bio/run_biomcp.py` | BioMCP wrapper with SSL handling |
| `servers/bio/_biomcp_no_ssl.py` | BioMCP SSL monkeypatch script |
| `streamlit-app/.env.example` | Update to show Anthropic key as primary, Merck as secondary, and BioMCP toggle |
| `.gitignore` | Add data/, *.db, node_modules/, nul |
| `streamlit-app/agent.py` | Fix agent loop: early-exit on substantive responses without markers |
| `docs/claude_fix_log.md` | This file |

---

## How to Verify Locally

```bash
cd streamlit-app

# 1. Activate venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 2. Install deps (should complete without errors)
pip install -r requirements.txt

# 3. Set up your API key
cp .env.example .env
# Edit .env and replace sk-ant-api03-YOUR-KEY-HERE with your real key

# 4. Launch
streamlit run app.py
# Should open at http://localhost:8501

# 5. Test MCP servers independently (optional)
cd ../servers/pubchem && node index.js    # Should print "running on stdio"
cd ../servers/literature && node index.js
cd ../servers/data_analysis && node index.js
cd ../servers/web_knowledge && node index.js
```

---

## Env Vars / Config Updates Needed

| Variable | Required For | Where to Set |
|----------|-------------|-------------|
| `ANTHROPIC_API_KEY` | Standard config (Claude Sonnet 4.5) | `streamlit-app/.env` |
| `AZURE_OPENAI_API_KEY` | Merck enterprise config | `streamlit-app/.env` |
| `BIOMCP_DISABLE_SSL` | Bypassing SSL errors on corporate networks | `streamlit-app/.env` |
