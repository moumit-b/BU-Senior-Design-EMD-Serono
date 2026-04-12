# Setup Instructions

Complete guide to running the Pharma Research Intelligence System on a new machine.

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10 or 3.11 recommended | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | bundled with Node | `npm --version` |
| Git | any recent | `git --version` |

> **Python 3.12+ users:** Some packages (`chromadb`, older `langchain`) may have minor compatibility issues. Python 3.11 is the most stable choice for this project.

### macOS (especially M1/M2/M3)

Install Node.js and system libraries via Homebrew:

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js
brew install node

# Required for WeasyPrint PDF export
brew install pango cairo gdk-pixbuf libffi

# Add Homebrew to your PATH if not already (Apple Silicon only)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Windows

- Download Python from [python.org](https://www.python.org/downloads/) — check **"Add to PATH"** during install
- Download Node.js LTS from [nodejs.org](https://nodejs.org/)
- For PDF export: install [GTK3 for Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) and reboot

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/moumit-b/BU-Senior-Design-EMD-Serono.git
cd BU-Senior-Design-EMD-Serono
```

---

## Step 2: Run the One-Shot Installer

From the repo root:

```bash
# Windows
python install.py

# macOS / Linux
python3 install.py
```

This handles everything automatically:
1. Checks Python and Node.js versions
2. Creates `streamlit-app/venv` (Python virtual environment)
3. Upgrades pip
4. Installs all Python packages from `requirements.txt`
5. Installs `uv`/`uvx` (required for BioContext KB MCP server)
6. Runs `npm install` in all 9 MCP server directories
7. Builds TypeScript servers (`pubchem-augmented`)
8. Creates `streamlit-app/.env` with documented API key slots

> **Always use `install.py` on a new machine** rather than `pip install -r requirements.txt` alone — it also handles the Node.js MCP servers, which `pip` cannot.

---

## Install Time Warning: PyTorch and sentence-transformers

`sentence-transformers` (used for semantic chat history search) depends on **PyTorch (`torch`)**, which is a large download — typically **800 MB–2 GB** depending on platform and whether CUDA is included. Installation can take **5–20 minutes** on a normal internet connection. This is expected; do not interrupt it.

**Platform-specific notes:**

### macOS Apple Silicon (M1 / M2 / M3)

PyTorch has native ARM support, but it **must be installed inside a venv** pointing to the correct architecture. If you install outside a venv and your Python is x86_64 (e.g., installed via an old Rosetta Homebrew), torch will install the wrong binary and fail at import time.

To verify before running the installer:

```bash
python3 -c "import platform; print(platform.machine())"
# Should print: arm64  (not x86_64)
```

If it prints `x86_64` on an M-series Mac, you have a Rosetta Python. Install a native ARM Python:

```bash
brew install python@3.11
# Then use /opt/homebrew/bin/python3.11 instead of python3
```

After installing, verify torch works:

```bash
cd streamlit-app
source venv/bin/activate
python -c "import torch; print(torch.__version__)"
```

If this fails with a segfault or import error on Apple Silicon, try installing the MPS-compatible wheel manually:

```bash
pip install torch torchvision torchaudio
```

### Windows (CPU-only, no CUDA)

The installer installs the default `torch` CPU wheel, which is the largest single package (~800 MB). This is expected. If you want to reduce install time on machines without a GPU, you can skip CUDA by adding this to a `pip.conf` before installing:

```ini
[global]
extra-index-url = https://download.pytorch.org/whl/cpu
```

Or install torch separately before running `install.py`:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
python install.py
```

The installer will see torch already installed and skip it.

### Linux

Same as Windows — CPU wheel installs fine. If you have an NVIDIA GPU and want acceleration, install the CUDA wheel manually before running `install.py`:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
python3 install.py
```

---

## Virtual Environment: Why It Matters

**Always install inside a venv.** The installer creates one automatically at `streamlit-app/venv`. Running without a venv causes:

- Dependency conflicts with system Python packages
- On macOS: torch may install the wrong architecture binary
- On Windows: `weasyprint` GTK bindings may conflict with system-level DLLs
- Risk of breaking other Python projects on the same machine

**If you accidentally installed outside a venv:**

```bash
# Delete the broken install and start clean
rm -rf streamlit-app/venv       # macOS/Linux
rmdir /s streamlit-app\venv     # Windows

python3 install.py              # re-run the installer
```

---

## Step 3: Fill In Your API Keys

The installer creates `streamlit-app/.env`. Open it and fill in:

```bash
# Required — Anthropic Claude (primary LLM)
# Get a key at: https://console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-api03-...

# Required for NCI clinical trial tools (nci_intervention_searcher, nci_biomarker_searcher)
# Free key at: https://clinicaltrialsapi.cancer.gov/
NCI_API_KEY=your_nci_key_here

# Optional — Supabase for persistent cross-device chat history and reports
# Without this, the app uses a local SQLite file (streamlit-app/data/sessions.db)
# SUPABASE_DB_URL=postgresql://...
# SUPABASE_URL=https://....supabase.co
# SUPABASE_KEY=eyJ...
```

Optional extras:

```bash
# Tavily web search — free tier at https://tavily.com
# Enables the web_search tool in the chat agent
# TAVILY_API_KEY=tvly-...

# Corporate/Merck network — SSL interception fix for BioMCP
# BIOMCP_DISABLE_SSL=true
```

---

## Step 4: Launch the App

Activate the venv and start Streamlit:

**macOS / Linux:**
```bash
cd streamlit-app
source venv/bin/activate
streamlit run app.py
```

**Windows (Command Prompt):**
```cmd
cd streamlit-app
venv\Scripts\activate
streamlit run app.py
```

**Windows (PowerShell):**
```powershell
cd streamlit-app
venv\Scripts\Activate.ps1
streamlit run app.py
```

The app opens at **http://localhost:8501**.

> **First-run note:** BioContext KB downloads packages via `uvx` on its first connection. The app may take up to 3 minutes to finish initializing on first boot. Subsequent starts are near-instant.

---

## Step 5: Try It Out

1. **Log in** — create an account on the login screen (stored in Supabase or local SQLite)
2. **Ask a question** in the chat, e.g.:
   - `What are the approved indications for pembrolizumab?`
   - `Tell me about Revuforj's mechanism of action`
3. **Ask a follow-up** — the agent retains conversation context:
   - `What's the generic name?`
   - `What clinical trials are currently active?`
4. **Generate a CI report** — go to the Reports tab, click "Generate Report"
5. **Download** — use the `.md` or `.pdf` download buttons

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ANTHROPIC_API_KEY not set` | Check `.env` exists in `streamlit-app/` and key starts with `sk-ant-` |
| `ModuleNotFoundError` | Venv not activated — run `source venv/bin/activate` (mac) or `venv\Scripts\activate` (Windows) |
| `streamlit: command not found` | Run `python -m streamlit run app.py` instead |
| `torch` install hangs or takes forever | Expected — PyTorch is 800 MB–2 GB. Wait it out. See install time warning above |
| `torch` import segfaults on M-series Mac | Wrong Python architecture — see Apple Silicon section above |
| MCP server `Connection closed` at startup | Run `python install.py` — `npm install` is likely missing for that server |
| `nci_* tools fail / 401 error` | Add `NCI_API_KEY` to `.env` (free at clinicaltrialsapi.cancer.gov) |
| SSL certificate errors in biomcp | Add `BIOMCP_DISABLE_SSL=true` to `.env` (common on Merck/corporate networks) |
| WeasyPrint PDF export fails on macOS | Run `brew install pango cairo gdk-pixbuf libffi` |
| WeasyPrint PDF export fails on Windows | Install GTK3 from github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer and reboot |
| WeasyPrint PDF export fails on Linux | Run `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0` |
| `psycopg2` install fails on macOS | Run `brew install postgresql` first, or use `psycopg2-binary` (already in requirements.txt) |
| ChromaDB import error on Python 3.12 | Use Python 3.11 — `brew install python@3.11` on Mac |
| Port 8501 in use | Run `streamlit run app.py --server.port 8502` |
| Reports show in wrong session | Fixed in latest code — update to latest commit on `mb-major-ui+agent-updates` |

---

## Platform-Specific Checklists

### macOS (Apple Silicon — M1/M2/M3)

- [ ] Python installed via Homebrew (`brew install python@3.11`) — **not** via pyenv x86 or old Rosetta install
- [ ] `python3 -c "import platform; print(platform.machine())"` prints `arm64`
- [ ] `brew install pango cairo gdk-pixbuf libffi` done (WeasyPrint)
- [ ] `brew install node` done (Node.js 18+)
- [ ] Running inside `streamlit-app/venv`

### macOS (Intel)

- [ ] Python 3.10 or 3.11 from python.org or Homebrew
- [ ] `brew install pango cairo gdk-pixbuf libffi` done (WeasyPrint)
- [ ] `brew install node` done
- [ ] Running inside `streamlit-app/venv`

### Windows 10/11

- [ ] Python 3.10–3.11 from python.org, "Add to PATH" checked
- [ ] Node.js LTS from nodejs.org
- [ ] GTK3 installed and **machine rebooted** (WeasyPrint PDF)
- [ ] Running inside `streamlit-app/venv` (not system Python)
- [ ] Using Windows Terminal or PowerShell (not classic cmd.exe) for best experience

### Linux (Ubuntu/Debian)

- [ ] `sudo apt install python3.11 python3.11-venv python3-pip` (or similar)
- [ ] `sudo apt install nodejs npm` (verify `node --version` >= 18)
- [ ] `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0` (WeasyPrint)
- [ ] Running inside `streamlit-app/venv`

---

## MCP Servers Reference

All 9 servers are free to use (no API keys except where noted):

| Server | Data Source | Notes |
|--------|-------------|-------|
| `pubchem-augmented` | PubChem (NIH) | TypeScript — requires build step (handled by installer) |
| `biomcp` | PubMed, ClinicalTrials.gov, OpenFDA, genes | Requires `NCI_API_KEY` for nci_* tools |
| `literature` | PubMed articles | — |
| `data_analysis` | Local statistics, molecular descriptors | — |
| `web_knowledge` | Wikipedia, DrugBank, drug info | — |
| `medrxiv` | medRxiv preprints | — |
| `biorxiv` | bioRxiv preprints | — |
| `opentargets` | Open Targets (target-disease associations) | — |
| `stringdb` | STRING-db (protein interactions) | — |

---

## Architecture Overview

```
streamlit-app/
├── app.py                  # Main Streamlit app (auth, chat, tabs)
├── agent.py                # MCPAgent — tool-calling loop with history
├── agents/                 # Specialized agents (Chemical, Clinical, etc.)
├── context/                # Database, session state, vector store
│   ├── database.py         # DatabaseManager (Supabase + SQLite fallback)
│   ├── db_models.py        # SQLAlchemy ORM models
│   └── chat_vector_store.py# Semantic chat search (ChromaDB + sentence-transformers)
├── ui/
│   ├── report_panel.py     # Reports tab: generation, past reports, downloads
│   └── chat_history.py     # Sidebar: session list, new/load conversation
├── reporting/
│   └── exporters/
│       └── pdf_exporter.py # WeasyPrint-based PDF export
├── governance/             # Context Forge Gateway, audit logger
├── requirements.txt        # Python dependencies
└── .env                    # API keys (not committed)

servers/                    # Node.js MCP servers (9 total)
install.py                  # One-shot cross-platform installer
```

For Merck/corporate network users, see **[MERCK_STARTUP_GUIDE.md](MERCK_STARTUP_GUIDE.md)**.
