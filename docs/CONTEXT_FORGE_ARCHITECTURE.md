# Context Forge Architecture: Full System Documentation

**Date:** January 2026
**Status:** Implemented
**Branch:** `feature/context-forge-implementation`

---

## 1. High-Level Summary

The system implements the **IBM Context Forge** pattern within the existing **Dual Orchestration** architecture. Every MCP tool call now flows through a centralized **Context Forge Gateway** that enforces compliance, audit logging, rate limiting, and health monitoring before reaching the actual data source.

**Before (Direct-to-Tool):**
```
User -> Agent Orchestrator -> MCP Orchestrator -> MCP Server (BioMCP, PubChem, etc.)
```

**After (Gateway-Mediated):**
```
User -> Agent Orchestrator -> MCP Orchestrator -> Context Forge Gateway -> MCP Server
                                                        |
                                              +---------+---------+
                                              |         |         |
                                         Compliance  Audit    Rate Limit
                                          Engine     Logger    Limiter
                                              |
                                         Service Registry
```

---

## 2. Full Architecture Graph

```
+===========================================================================+
|                        STREAMLIT UI LAYER                                  |
|                                                                           |
|  +---------------------------+    +-----------------------------------+   |
|  | Dual Orchestration Lab    |    | Governance Dashboard              |   |
|  | (pages/2_*.py)            |    | (pages/governance_dashboard.py)   |   |
|  |                           |    |                                   |   |
|  | - Quick Demo              |    | - Gateway Stats                   |   |
|  | - Learning Dashboard      |    | - Service Health                  |   |
|  | - Tool Composer           |    | - Compliance Violations           |   |
|  | - Research Sessions       |    | - Audit Logs                      |   |
|  +---------------------------+    | - Rate Limiting                   |   |
|               |                   +-----------------------------------+   |
|               |                                    |                      |
+===========================================================================+
                |                                    |
                v                                    v
+===========================================================================+
|                     ORCHESTRATION LAYER                                    |
|                                                                           |
|  +---------------------------+                                            |
|  | Agent Orchestrator        |  (TOP LAYER)                               |
|  | (agent_orchestrator.py)   |                                            |
|  |                           |                                            |
|  | - Query Analysis          |                                            |
|  | - Task Decomposition      |                                            |
|  | - Agent Selection         |                                            |
|  | - RequestContext injection |  <-- NEW: passes user_id, session_id,     |
|  | - Bidirectional Learning  |      agent_name into every call            |
|  +-------------+-------------+                                            |
|                |                                                          |
|                v                                                          |
|  +---------------------------+                                            |
|  | MCP Orchestrator          |  (BOTTOM LAYER)                            |
|  | (mcp_orchestrator.py)     |                                            |
|  |                           |                                            |
|  | - Intelligent Routing     |                                            |
|  | - Performance Tracking    |                                            |
|  | - Circuit Breaker         |                                            |
|  | - Multi-level Cache       |                                            |
|  | - set_gateway()           |  <-- NEW: attaches Gateway                 |
|  | - _call_mcp_tool()        |  <-- CHANGED: routes through Gateway       |
|  +-------------+-------------+                                            |
|                |                                                          |
+===========================================================================+
                |
                v
+===========================================================================+
|                  GOVERNANCE LAYER (Context Forge)                          |
|                                                                           |
|  +-------------------------------------------------------------------+   |
|  | ContextForgeGateway  (governance/gateway.py)                       |   |
|  |                                                                    |   |
|  |  call_tool(server, tool, params, RequestContext) -> ToolResponse   |   |
|  |                                                                    |   |
|  |  FLOW:                                                             |   |
|  |  1. Rate Limiter        ->  check_rate_limit(user, server)        |   |
|  |  2. Compliance Engine   ->  validate_request(server, tool, params) |   |
|  |  3. Service Registry    ->  is_healthy(server)                     |   |
|  |  4. Audit Logger        ->  log_request(...)                       |   |
|  |  5. MCP Wrapper         ->  call_tool(tool, params)               |   |
|  |  6. Compliance Engine   ->  validate_response(result)             |   |
|  |  7. Audit Logger        ->  log_response(...)                      |   |
|  |  8. Source Attribution   ->  attach data lineage                   |   |
|  +-------------------------------------------------------------------+   |
|                                                                           |
|  +-----------------+  +-----------------+  +----------+  +------------+   |
|  | ServiceRegistry |  | ComplianceEngine|  | AuditLog |  | RateLimiter|   |
|  |                 |  |                 |  |          |  |            |   |
|  | - register()    |  | - PII/PHI check |  | - SQLite |  | - per-user |   |
|  | - heartbeat()   |  | - prohibited    |  | - memory |  | - per-MCP  |   |
|  | - is_healthy()  |  |   terms         |  |   fallbk |  | - burst    |   |
|  | - deregister()  |  | - domain constr.|  |          |  |            |   |
|  | - tool schemas  |  | - response scan |  |          |  |            |   |
|  +-----------------+  +-----------------+  +----------+  +------------+   |
|                                                                           |
+===========================================================================+
                |
                v
+===========================================================================+
|                       MCP SERVER LAYER                                    |
|                                                                           |
|  +----------+  +----------+  +----------+  +----------+  +----------+    |
|  |  BioMCP  |  | PubChem  |  |  ChEMBL  |  |  Brave   |  | Jupyter  |    |
|  | (PubMed, |  |  (NIH)   |  | (EMBL-   |  | (Search) |  | (Python) |    |
|  |  ClinTrials)|          |  |   EBI)   |  |          |  |          |    |
|  +----------+  +----------+  +----------+  +----------+  +----------+    |
|                                                                           |
+===========================================================================+
```

---

## 3. Step-by-Step Request Flow (Detailed)

Here is what happens when a user types "Find inhibitors of BRCA1" in the Dual Orchestration Lab:

### Step 1: User Input (UI Layer)
The Streamlit UI captures the query and detects the query type as `INHIBITOR_SEARCH`.  It assigns the query to the **Clinical Agent** and recommends the **biomcp** MCP server.

### Step 2: RequestContext Construction
The UI (or the `AgentOrchestrator`) constructs a `RequestContext` containing:
- `user_id`: `"demo_user"`
- `session_id`: The active Streamlit session
- `agent_name`: `"Clinical Agent"`
- `query_text`: `"Find inhibitors of BRCA1"`

### Step 3: Gateway call_tool() Entry
The request enters `ContextForgeGateway.call_tool()` with:
- `server = "biomcp"`
- `tool = "search_pubmed"`
- `parameters = {"query": "Find inhibitors of BRCA1"}`
- `context = RequestContext(...)`

### Step 4: Rate Limiting (RateLimiter)
The `RateLimiter` checks whether `demo_user` has exceeded 100 requests/hour for the `biomcp` server.  If the limit is exceeded, the call is rejected immediately with `ToolResponse(success=False, error="Rate limit exceeded")`.

### Step 5: Pre-Validation (ComplianceEngine)
The `ComplianceEngine.validate_request()` scans the parameters for:
- **PII/PHI patterns**: SSNs, credit cards, emails, MRNs, DOBs, patient IDs
- **Prohibited terms**: "internal pipeline", "proprietary", "confidential", "trade secret", "under NDA"
- **Domain constraints**: (if configured) checks that the tool is authorized for the server

If any check fails, the call is blocked and logged as a compliance violation.

### Step 6: Health Check (ServiceRegistry)
The `ServiceRegistry.is_healthy("biomcp")` verifies:
- The server is registered
- Its last heartbeat is within the 5-minute timeout window
- Its health flag is `True`

If the server is stale or marked unhealthy, the call is rejected.

### Step 7: Audit Log (Request)
The `AuditLogger.log_request()` writes an immutable record to the SQLite database:
```
{
    timestamp: "2026-01-21T14:30:22",
    session_id: "abc-123",
    user_id: "demo_user",
    action_type: "mcp_call",
    actor: "Clinical Agent",
    mcp_server: "biomcp",
    tool_name: "search_pubmed",
    parameters_json: {"query": "Find inhibitors of BRCA1"},
    result_status: "pending"
}
```

### Step 8: Tool Execution (MCPToolWrapper)
The gateway calls `wrapper.call_tool("search_pubmed", {"query": "..."})` on the real BioMCP server via the MCP stdio protocol.  The wrapper returns the raw result string.

The heartbeat for `biomcp` is refreshed on the `ServiceRegistry`.

### Step 9: Post-Validation (ComplianceEngine)
The `ComplianceEngine.validate_response()` scans the response for PII/PHI leakage.  If any pattern matches, the result is **redacted** and the response is marked with `compliance_passed = False`.

### Step 10: Source Attribution
A source-attribution block is attached to the response:
```json
{
    "mcp_server": "biomcp",
    "tool_name": "search_pubmed",
    "timestamp": "2026-01-21T14:30:23",
    "data_source": "PubMed, ClinicalTrials.gov, NCI CTS, OpenFDA"
}
```

### Step 11: Audit Log (Response)
The `AuditLogger.log_response()` updates the original record:
```
result_status: "success"
execution_time: 1.23
```

### Step 12: Return to Caller
The `ToolResponse` is returned up the stack:
```
ToolResponse(
    success=True,
    result="<PubMed search results...>",
    execution_time=1.23,
    mcp_server="biomcp",
    tool_name="search_pubmed",
    compliance_passed=True,
    source_attribution=[{...}],
    audit_log_id=42
)
```

---

## 4. Component Details

### 4.1 ContextForgeGateway (`governance/gateway.py`)

The central proxy.  Key design decisions:
- **Stateless proxy**: The gateway holds no query state — all context comes from `RequestContext`.
- **Graceful degradation**: If the audit DB is unavailable, logging falls back to in-memory.  If no MCP wrapper is registered, a stub response is returned.
- **Statistics tracking**: `get_gateway_stats()` exposes total calls, successes, failures, compliance blocks, and server health for the dashboard.

### 4.2 ServiceRegistry (`governance/service_registry.py`)

Dynamic MCP server tracking:
- **register_service()**: Called by `gateway.register_mcp_wrappers()` when MCP connections are established.
- **heartbeat timeout**: Servers with no heartbeat in 5 minutes are automatically marked unhealthy.
- **update_heartbeat()**: Called on every successful tool execution to prove the server is alive.
- **deregister_service()**: Cleanly removes a server (e.g., after shutdown).
- **Tool schema caching**: Each server's tool list is cached for fast `get_all_tools()` queries.

### 4.3 ComplianceEngine (`governance/compliance_engine.py`)

Dual-stage validation:

**Pre-execution (outgoing request):**
| Rule | What it checks |
|------|---------------|
| PII: SSN | `\d{3}-\d{2}-\d{4}` |
| PII: Credit Card | 13-16 digit sequences |
| PII: Email | Standard email pattern |
| PHI: MRN | `MRN:\d{6,10}` |
| PHI: DOB | `DOB:\d{1,2}/\d{1,2}/\d{2,4}` |
| PHI: Patient ID | `PAT-\d{4,}` |
| Prohibited Terms | "internal pipeline", "proprietary", "confidential", "trade secret", "under NDA" |
| Domain Constraints | Tool allow-lists per server (configurable) |

**Post-execution (incoming response):**
- Same PII/PHI patterns applied to outgoing data
- Empty response check
- Violations are logged with timestamp, stage, server, tool, and reason

### 4.4 AuditLogger (`governance/audit_logger.py`)

Immutable audit trail:
- **Primary storage**: SQLite via SQLAlchemy (the `AuditLogRecord` model)
- **Fallback**: In-memory list when DB is unavailable
- **log_request()**: Creates a "pending" record before execution
- **log_response()**: Updates the record with success/error and execution time
- **get_audit_trail()**: Session-scoped query
- **get_recent_logs()**: Cross-session query for the governance dashboard

### 4.5 RateLimiter (`governance/rate_limiter.py`)

Simple sliding-window rate limiter:
- Default: 100 requests per user per hour
- Tracks per-user and per-server counts
- Auto-cleans stale entries older than 1 hour

---

## 5. Files Changed

| File | Change |
|------|--------|
| `governance/gateway.py` | Replaced placeholder `_execute_tool_call` with real MCP wrapper delegation. Added `register_mcp_wrappers()`, `get_gateway_stats()`, statistics tracking, logging. |
| `governance/service_registry.py` | Added `deregister_service()`, `mark_unhealthy()`, `get_healthy_servers()`, `get_tools_for_server()`, configurable heartbeat timeout, logging. |
| `governance/compliance_engine.py` | Added PHI patterns (MRN, DOB, Patient ID), prohibited terms ("trade secret", "under NDA"), domain constraints, response PII scanning, violation logging with `get_violations()`. |
| `governance/audit_logger.py` | Added graceful DB fallback (in-memory), null-safe `log_response()`, `get_recent_logs()` for dashboard, ordered audit trail. |
| `orchestration/mcp_orchestrator.py` | Added `set_gateway()` method. `_call_mcp_tool()` now routes through the Gateway when attached, constructing `RequestContext` from the context dict. Falls back to direct wrapper if no gateway. |
| `orchestration/agent_orchestrator.py` | Added `user_id` and `session_id` fields. All context dicts now include governance fields (`user_id`, `session_id`, `query_text`) forwarded to the Gateway. |
| `pages/2_*.py` (Dual Orchestration Lab) | Creates `ContextForgeGateway` on init, registers wrappers on MCP connect, routes Quick Demo through gateway, displays governance metadata (compliance, audit_id, source), shows Gateway Status expander. |
| `pages/governance_dashboard.py` | Complete rewrite: live gateway stats, service health, compliance violations, audit logs, rate limiting — all reading from the shared gateway instance. |

---

## 6. Architectural Decisions

### Decision 1: Gateway as a Proxy, Not a Service
The Gateway runs in-process as a Python object, not as a separate FastAPI microservice. This avoids the operational complexity of inter-process communication while still providing all governance benefits. For enterprise scale-out, the Gateway can be extracted to a standalone service without changing the interface.

### Decision 2: Backward Compatibility via `set_gateway()`
Rather than making the Gateway a hard dependency, `MCPOrchestrator._call_mcp_tool()` checks for an attached gateway.  If none is set, it falls back to direct wrapper calls. This means:
- The main `app.py` (LangChain agent) continues to work unchanged
- The Dual Orchestration Lab opts in to governance explicitly
- Existing tests don't break

### Decision 3: In-Memory Audit Fallback
The `AuditLogger` attempts to use SQLite but gracefully degrades to an in-memory list.  This prevents the entire system from failing if the database path is unwritable (e.g., during CI runs or first-time setup).

### Decision 4: Compliance as a Configuration
PII patterns, prohibited terms, and domain constraints are defined as data (lists/dicts), not hard-coded logic. This makes it straightforward for the EMD Serono compliance team to update rules without modifying business logic.

### Decision 5: Source Attribution on Every Response
Every `ToolResponse` includes a `source_attribution` array documenting which MCP server, tool, and underlying data source (e.g., "PubMed, ClinicalTrials.gov") produced the result.  This provides complete **data lineage** for regulatory audits.

---

## 7. How This Improves the System

| Dimension | Before | After |
|-----------|--------|-------|
| **Compliance** | No automated checks | PII/PHI scanning on every request and response |
| **Audit Trail** | Session-based logs only | Immutable SQLite records with tool, actor, time, and status |
| **Health Monitoring** | Basic circuit breaker | Heartbeat-based registry with automatic stale-server detection |
| **Rate Limiting** | None | Per-user, per-server sliding-window limits |
| **Data Lineage** | Not tracked | Source attribution on every response |
| **Resilience** | Direct call failure = crash | Gateway returns structured error; fallback paths exist |
| **Observability** | No dashboard | Full governance dashboard with live stats |

---

## 8. Quick Start: Running the System

```bash
# 1. Switch to the feature branch
git checkout feature/context-forge-implementation

# 2. Navigate to the Streamlit app
cd streamlit-app

# 3. Activate your virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Run the Streamlit app
streamlit run app.py

# 5. Open the Dual Orchestration Lab page
#    Click "Connect to MCPs" to register servers with the Gateway
#    Execute a query to see governance in action

# 6. Open the Governance Dashboard page
#    View audit logs, compliance violations, and service health
```

---

## 9. Glossary

| Term | Definition |
|------|-----------|
| **Context Forge** | IBM architectural pattern for centralized MCP governance |
| **Gateway** | The `ContextForgeGateway` proxy that mediates all tool calls |
| **RequestContext** | Data class carrying user, session, and agent identity for governance |
| **ToolResponse** | Data class wrapping MCP results with compliance and attribution metadata |
| **ServiceRegistry** | Dynamic catalog of available MCP servers with health tracking |
| **ComplianceEngine** | Rule engine for PII/PHI detection and data-leakage prevention |
| **AuditLogger** | Immutable record of every tool call for regulatory compliance |
| **Dual Orchestration** | The two-layer architecture: Agent Orchestrator (top) + MCP Orchestrator (bottom) |
| **Bidirectional Learning** | Novel feature where MCPs and Agents teach each other about performance |
