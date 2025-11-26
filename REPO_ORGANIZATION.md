# Repository Organization

## Folder Structure

```
BU-Senior-Design-EMD-Serono/
├── docs/                    # Architecture & demo documentation
│   ├── README.md           # Documentation index
│   ├── DUAL_ORCHESTRATION_ARCHITECTURE.md
│   ├── DUAL_ORCHESTRATION_README.md
│   ├── DUAL_ORCHESTRATION_IMPLEMENTATION.md
│   ├── DEMO_PLAN.md
│   ├── DEMO_QUICKSTART.md
│   └── QUICKSTART_*.md
│
├── progress/               # Progress tracking (gitignored)
│   ├── README.md
│   ├── IMPLEMENTATION_STATUS.md
│   └── REAL_MCP_INTEGRATION_SUMMARY.md
│
├── streamlit-app/          # Main application
│   ├── app.py             # Main Streamlit app
│   ├── pages/             # Multi-page app
│   │   └── 2_🧪_Dual_Orchestration_Lab.py  # Demo page
│   ├── orchestration/     # Orchestration layer
│   │   ├── mcp_orchestrator.py
│   │   ├── agent_orchestrator.py
│   │   ├── performance_kb.py
│   │   ├── tool_composer.py
│   │   └── session_manager.py
│   ├── models/            # Data models
│   ├── agents/            # Agent implementations
│   ├── utils/             # Utilities
│   ├── mcp_tools.py       # MCP tool wrappers
│   └── config.py          # Configuration
│
├── servers/               # MCP servers
│   ├── pubchem/
│   ├── bio/
│   ├── literature/
│   ├── data_analysis/
│   └── web_knowledge/
│
└── results/               # Output results (gitignored)
```

## Quick Navigation

### 📚 Documentation
**Location:** `docs/`

All architecture documentation, design documents, and demo guides.

**Start here:** [docs/README.md](docs/README.md)

### 🚀 Getting Started
1. Read [docs/DEMO_QUICKSTART.md](docs/DEMO_QUICKSTART.md)
2. Run the demo: `cd streamlit-app && venv/Scripts/python.exe -m streamlit run app.py`
3. Navigate to "🧪 Dual Orchestration Lab"

### 🏗️ Architecture
**Core Concepts:**
- Dual orchestration (Agent layer + MCP layer)
- Bidirectional learning
- Multi-agent specialization

**Read:** [docs/DUAL_ORCHESTRATION_ARCHITECTURE.md](docs/DUAL_ORCHESTRATION_ARCHITECTURE.md)

### 🔬 Development
**Code Organization:**
- `streamlit-app/orchestration/` - Orchestration logic
- `streamlit-app/agents/` - Agent implementations
- `streamlit-app/models/` - Data models
- `servers/` - MCP server implementations

## File Purposes

### Root Level Files
- **REPO_ORGANIZATION.md** (this file) - Repository structure guide
- **.gitignore** - Git ignore rules
- **README.md** - Project overview (if exists)

### Documentation (`docs/`)

#### Architecture
- **DUAL_ORCHESTRATION_ARCHITECTURE.md** - Technical architecture specification
  - Dual layer design
  - Bidirectional learning mechanics
  - Novel features implementation

- **DUAL_ORCHESTRATION_README.md** - User guide
  - Installation and setup
  - How to use features
  - Expansion guides
  - Use cases

- **DUAL_ORCHESTRATION_IMPLEMENTATION.md** - Implementation details
  - Multi-agent architecture
  - Agent specialization
  - Dual orchestration flow
  - Code examples

#### Demo Guides
- **DEMO_QUICKSTART.md** - Quick start for running demo
  - Setup instructions
  - Demo walkthrough
  - 5-minute supervisor demo script

- **DEMO_PLAN.md** - Original demo planning
  - Vision and design
  - Feature mockups
  - Implementation phases

- **QUICKSTART_*.md** - Various quick start guides
  - Different aspects of the system
  - Scenario-specific guides

### Progress Tracking (`progress/` - gitignored)

- **IMPLEMENTATION_STATUS.md** - Current status tracking
  - Completed features
  - In-progress work
  - Next steps

- **REAL_MCP_INTEGRATION_SUMMARY.md** - MCP integration summary
  - What was implemented
  - Issues fixed
  - Testing notes

## Organization Principles

### 1. Documentation (`docs/`)
✅ **Committed to git**
✅ **User-facing**
✅ **Stable/reviewed content**

Contains:
- Architecture specs
- User guides
- Demo walkthroughs
- Design documents

### 2. Progress Tracking (`progress/`)
❌ **NOT committed (in .gitignore)**
❌ **Internal use only**
❌ **Work-in-progress notes**

Contains:
- Development status
- Internal notes
- Implementation summaries
- Work tracking

### 3. Code (`streamlit-app/`, `servers/`)
✅ **Committed to git**
✅ **Production code**

Organized by:
- Feature (orchestration, agents, models)
- Layer (MCP servers, orchestration, UI)

## Best Practices

### Adding New Documentation
1. **Architecture/Design docs** → `docs/`
2. **Progress notes** → `progress/` (gitignored)
3. **Code documentation** → Inline comments + docstrings

### Finding Information
- **"How do I use X?"** → `docs/DUAL_ORCHESTRATION_README.md`
- **"How does X work?"** → `docs/DUAL_ORCHESTRATION_ARCHITECTURE.md`
- **"How do I demo this?"** → `docs/DEMO_QUICKSTART.md`
- **"What's the current status?"** → `progress/IMPLEMENTATION_STATUS.md`

### Updating Documentation
- **Major feature added** → Update `docs/DUAL_ORCHESTRATION_ARCHITECTURE.md` and `docs/DUAL_ORCHESTRATION_README.md`
- **Demo flow changed** → Update `docs/DEMO_QUICKSTART.md`
- **Progress update** → Update `progress/IMPLEMENTATION_STATUS.md`

## Git Strategy

### Committed
- All `docs/` folder
- All code in `streamlit-app/` and `servers/`
- `.gitignore`
- `REPO_ORGANIZATION.md`

### Not Committed (.gitignore)
- `progress/` - Internal tracking
- `results/` - Output data
- `__pycache__/` - Python cache
- `venv/` - Virtual environment
- `.streamlit/` - Streamlit config
- `mcp_old_backup/` - Old backup files

## Quick Reference

| Need | Location |
|------|----------|
| Setup instructions | `docs/DEMO_QUICKSTART.md` |
| Architecture overview | `docs/DUAL_ORCHESTRATION_ARCHITECTURE.md` |
| Feature guide | `docs/DUAL_ORCHESTRATION_README.md` |
| Demo walkthrough | `docs/DEMO_QUICKSTART.md` |
| Implementation status | `progress/IMPLEMENTATION_STATUS.md` |
| Main app | `streamlit-app/app.py` |
| Demo page | `streamlit-app/pages/2_🧪_Dual_Orchestration_Lab.py` |
| Orchestration code | `streamlit-app/orchestration/` |
| MCP servers | `servers/` |

---

**Last Updated:** 2025-11-26
**Organization Version:** 1.0
