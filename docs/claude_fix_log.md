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
| `streamlit-app/.env.example` | Update to show Anthropic key as primary, Merck as secondary |
| `.gitignore` | Add data/, *.db, node_modules/, nul |
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
