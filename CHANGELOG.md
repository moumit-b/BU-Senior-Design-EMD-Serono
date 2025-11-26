# Changelog

## [2025-11-26] - Production Ready: Event Loop Fix & Documentation

### Fixed
- ✅ **Persistent Event Loop Architecture**
  - Resolved "Attempted to exit cancel scope in a different task" error
  - Implemented background thread with dedicated asyncio event loop
  - All MCP operations (connect + tool calls) now use same event loop
  - Thread-safe execution via `run_coroutine_threadsafe()`

- ✅ **QueryType Enum Error**
  - Fixed `AttributeError: GENE_SEARCH`
  - Changed to correct enum value `QueryType.GENE_LOOKUP`

- ✅ **PubChem Tool Call Success**
  - Query preprocessing now extracts compound names correctly
  - Tool calls successfully return real data from PubChem
  - Verified: "tylenol" query returns CID 1983

### Added
- ✅ **Comprehensive Installation Guide** (`docs/INSTALLATION.md`)
  - Step-by-step setup from cloning repo to running app
  - Prerequisites, dependencies, troubleshooting
  - Works on any machine

- ✅ **Error Detection & Reporting**
  - Improved error handling in MCP tool wrapper
  - Full exception tracebacks for debugging
  - Demo now properly detects and displays tool call failures

### Changed
- **Documentation Organization**
  - Created `INSTALLATION.md` as primary setup guide
  - Updated `DEMO_QUICKSTART.md` to reference installation
  - Updated `DUAL_ORCHESTRATION_ARCHITECTURE.md` with implementation details
  - Refreshed `docs/README.md` navigation
  - Status updated: "Production Demo Ready"

### Technical Details

**Persistent Event Loop Pattern:**
```python
class MCPEventLoop:
    def start(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

    def run_coroutine(self, coro, timeout=30):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(timeout=timeout)
```

**Benefits:**
- Eliminates event loop mismatch errors
- Compatible with Streamlit's sync execution model
- Enables real MCP tool calls to succeed

---

## [2025-11-26] - Dual Orchestration Implementation & Repo Organization

### Added
- ✅ **Multi-Agent Architecture**
  - Implemented specialized agents (Chemical Agent, Clinical Agent)
  - Added Agent Orchestrator for intelligent query routing
  - Created dual-layer orchestration (Agent Layer + MCP Layer)

- ✅ **Real MCP Integration**
  - One-click MCP connection in demo
  - Real-time connection status monitoring
  - Graceful fallback to simulated mode
  - Successfully connected to 4/5 MCPs (PubChem, Literature, Data Analysis, Web Knowledge)

- ✅ **Bidirectional Learning Visualization**
  - MCP Layer → Agent Layer feedback display
  - Agent Layer → MCP Layer learning tracking
  - Per-agent performance metrics
  - Per-MCP performance metrics

- ✅ **Query Preprocessing**
  - Natural language to MCP format conversion
  - Compound name extraction for PubChem
  - MCP-specific parameter handling

- ✅ **Repository Organization**
  - Created `docs/` folder for architecture and demo documentation
  - Created `progress/` folder for internal progress tracking (gitignored)
  - Added comprehensive READMEs for navigation
  - Created `.gitignore` for proper git management
  - Added `REPO_ORGANIZATION.md` for structure reference

### Fixed
- ✅ **PubChem Tool Call Error**
  - Fixed incorrect tool name (`search_compound` → `search_compounds_by_name`)
  - Fixed parameter key (`query` → `name`)
  - Added query preprocessing to extract compound names

- ✅ **Circular Import Issue**
  - Resolved naming conflict between local `mcp/` folder and MCP SDK package
  - Renamed conflicting folder to `mcp_old_backup/`

- ✅ **Missing Multi-Agent Architecture**
  - Transformed single-layer MCP routing to true dual orchestration
  - Added agent specialization and assignment logic

### Changed
- **Demo Page UI**
  - Now shows Agent Orchestrator → Agent → MCP Orchestrator flow
  - Displays architecture flow diagram for each query
  - Separated Agent Layer and MCP Layer performance metrics
  - Added per-agent learning displays

- **Learning Dashboard**
  - Split into Agent Layer Performance and MCP Layer Performance sections
  - Added "Active Agents" metric
  - Shows real vs simulated execution tracking
  - Per-agent learning expandable sections

### Documentation
- Moved all architecture docs to `docs/` folder
- Moved progress tracking to `progress/` folder (gitignored)
- Created navigation READMEs
- Added `REPO_ORGANIZATION.md` for structure reference
- Updated `DEMO_QUICKSTART.md` with latest features

### Files Reorganized

**Moved to `docs/`:**
- DUAL_ORCHESTRATION_ARCHITECTURE.md
- DUAL_ORCHESTRATION_README.md
- DUAL_ORCHESTRATION_IMPLEMENTATION.md
- DEMO_PLAN.md
- DEMO_QUICKSTART.md
- QUICKSTART_DEMO_GUIDE.md
- QUICKSTART_DUAL_ORCHESTRATION.md

**Moved to `progress/` (gitignored):**
- IMPLEMENTATION_STATUS.md
- REAL_MCP_INTEGRATION_SUMMARY.md

**Created:**
- docs/README.md
- progress/README.md
- REPO_ORGANIZATION.md
- .gitignore
- CHANGELOG.md (this file)

### Technical Details

**Architecture:**
```
User Query
  ↓
Agent Orchestrator (analyzes & assigns to specialist)
  ↓
Specialized Agent (Chemical Agent OR Clinical Agent)
  ↓
MCP Orchestrator (routes to optimal MCP)
  ↓
MCP Server (PubChem, BioMCP, Literature, etc.)
```

**Agent Specialization:**
- **Chemical Agent:** Handles chemistry queries → Routes to PubChem
- **Clinical Agent:** Handles biomedical queries → Routes to BioMCP/Literature

**MCP Connection Status:**
- ✓ PubChem (2 tools)
- ✓ Literature (5 tools)
- ✓ Data Analysis (6 tools)
- ✓ Web Knowledge (8 tools)
- ✗ BioMCP (connection timeout - graceful fallback working)

### Known Issues
- BioMCP connection times out during initial connection (>10s)
- System gracefully falls back to simulated mode when BioMCP unavailable

### Next Steps
See `progress/IMPLEMENTATION_STATUS.md` for:
- Planned enhancements
- Feature roadmap
- Development priorities

---

## Previous Changes

Prior to repository organization, see individual documentation files in `docs/` for historical context.
