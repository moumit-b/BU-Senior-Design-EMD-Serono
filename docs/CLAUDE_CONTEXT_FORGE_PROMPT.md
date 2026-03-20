# Prompt for Claude Code: Context Forge Implementation

**Instructions for the User:** Copy the block below and paste it into your Claude Code terminal.

---

```text
Please create a new clean branch named `feature/context-forge-implementation` and switch to it. 

Your task is to fully implement the IBM Context Forge pattern within our Dual Orchestration architecture. 

I've already conducted a feasibility study, which you can find in `docs/CONTEXT_FORGE_FEASIBILITY.md`, and some preliminary research in `docs/CONTEXT_MANAGEMENT_RESEARCH.md`. The core scaffolding for the governance layer is already present in `streamlit-app/governance/` (including `gateway.py`, `service_registry.py`, `compliance_engine.py`, and `audit_logger.py`).

Your goal is to transition the system from its current "Direct-to-Tool" model (where `MCPOrchestrator` calls MCP wrappers directly) to a "Gateway-Mediated" model, where all tool calls are proxied through the `ContextForgeGateway`.

You have full engineering freedom to implement this however you see fit. You own the architectural decisions for this integration. 

Key objectives to consider:
1. Complete the execution logic in `gateway.py`.
2. Refactor `mcp_orchestrator.py` to route calls through the gateway.
3. Make the `ServiceRegistry` dynamic (e.g., active health monitoring).
4. Implement practical rules in the `ComplianceEngine` (e.g., PII filtering, source attribution).
5. Ensure the `AuditLogger` accurately records requests and responses.
6. Verify that the Dual Orchestration Lab UI (`streamlit-app/pages/2_🧪_Dual_Orchestration_Lab.py`) and the `AgentOrchestrator` correctly interface with the new gateway flow.

Please read the relevant files, make the necessary code changes, and ensure the system runs smoothly. Once you are done, summarize your architectural choices and how they improve the system's compliance and resilience.
```
