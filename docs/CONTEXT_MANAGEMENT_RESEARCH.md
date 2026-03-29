# Modern Context Engineering & Governance Report

**Date:** January 21, 2026
**Status:** Research & Architecture Recommendation
**Target:** Engineering Team & System Architects

---

## 1. Executive Summary

This report analyzes the current "Dual Orchestration" architecture with a specific focus on **Context Management** and **Context Rot**.

"Context Rot" manifests in two distinct forms in large agentic systems:
1.  **Cognitive Rot:** The LLM's inability to retain or prioritize relevant information from a long conversation history (Context Window saturation).
2.  **Operational Rot:** The degradation of tool connections, schema validity, and system state awareness over time (MCP connection staleness).

**Key Recommendations:**
*   **Adopt "Recursive Context" (MIT CSAIL):** Shift from linear history lists to a **"Session-as-Database"** model where agents query their own history via code (SQL/Python), significantly extending effective memory.
*   **Implement "Context Gateway" (IBM Context Forge pattern):** Centralize MCP tool management through a governance gateway to prevent operational rot and ensure observability.

---

## 2. Current Architecture Analysis

### 2.1 Current State (`session_manager.py`)
The current `SessionManager` implements a **Linear History Model**:
*   **Structure:** In-memory lists (`queries`, `hypotheses`, `insights`).
*   **Context Injection:** Likely injects "recent queries" or a "summary" text block into the prompt.
*   **Limitation:**
    *   **O(N) Complexity:** As the session grows, the cost to process context grows linearly (or quadratically for attention).
    *   **Attention Dilution:** The model struggles to distinguish between a key fact from Day 1 and noise from Day 7.
    *   **Fragility:** Pure in-memory storage risks total loss on service restart (unless persisted elsewhere not seen in `session_manager.py`).

### 2.2 Operational Risks
*   **Direct MCP Connections:** Agents connect directly to MCP servers. If a server updates its tools or goes offline, the agent holds "stale context" (invalid tool definitions), leading to runtime failures.

---

## 3. Emerging Solutions Research

### 3.1 Cognitive Context: MIT Recursive Language Models (RLMs)
**The Concept:**
Instead of feeding a massive text dump to the LLM, we provide the LLM with a **programming environment** and treat the context as a **Database**.

**How it works:**
1.  **Storage:** Session history, entities, and hypotheses are stored in a structured format (SQLite or Vector DB).
2.  **Retrieval:** The LLM *writes code* to retrieve what it needs.
    *   *Old Way:* "Here is the last 50 messages... answer the user."
    *   *RLM Way:* User asks "How has our understanding of BRCA1 changed?" -> LLM writes:
        ```python
        # Agent-generated code
        past_hypotheses = db.query("SELECT * FROM hypotheses WHERE entity='BRCA1' AND date < '2025-01-01'")
        current_hypotheses = db.query("SELECT * FROM hypotheses WHERE entity='BRCA1' AND date > '2025-01-01'")
        print(compare(past_hypotheses, current_hypotheses))
        ```
3.  **Benefit:** The context window contains only the *result* of the query, not the entire noise of the history. This virtually eliminates cognitive context rot.

### 3.2 Operational Context: IBM Context Forge (MCP Gateway)
**The Concept:**
`mcp-context-forge` is an architectural pattern where a **Central Gateway** manages all MCP servers.

**How it works:**
1.  **Registry:** The Gateway maintains the "Golden Source of Truth" for all available tools and their schemas.
2.  **Proxy:** Agents talk to the Gateway, not the tools directly.
3.  **Governance:** The Gateway enforces rate limits, logs usage (Lineage), and—crucially—**updates context**. If an MCP server changes its schema, the Gateway updates immediately. The next time the Agent asks "What tools do I have?", it gets the fresh context, preventing "Operational Rot".

---

## 4. Problem-Solution Deep Dive

### 4.1 Cognitive Context Rot (The "Amnesia" Problem)
**The Issue:**
In standard LLM apps, "memory" is just a long text log of the conversation. As a scientist researches a drug over weeks, this log gets too big. The LLM starts "forgetting" early facts (like a specific chemical property mentioned on Day 1) or gets confused by too much noise. This is fatal for competitive intelligence where precision is key.

**The Solution: Recursive Memory (MIT RLM / Session-as-Database)**
*   **What it is:** Instead of forcing the AI to "remember" everything in its immediate thought bubble (context window), we give it a **Searchable Database** of its own memories.
*   **How it works:**
    *   **Storage:** Every hypothesis, chemical entity, and insight found by the scientist is stored in a structured database (SQL or Vector DB), not just a text file.
    *   **Retrieval:** The AI writes a "query" (like a mini-program) to search its database for past context, bringing *only* those specific facts into its active mind.
*   **Enterprise Scale:** A scientist can have a research session that lasts **years**. The database grows, but the AI's "thinking cost" stays low.

### 4.2 Operational Context Rot (The "Broken Tool" Problem)
**The Issue:**
In a large enterprise like EMD Serono, backend systems change. IT might update a database schema or change an API key. In a standard setup, the AI Agents hold "stale" instructions on how to connect. When they try to work, they crash or hallucinate data because the tool is broken.

**The Solution: Context Forge Pattern (MCP Gateway)**
*   **What it is:** A central **"Traffic Control Tower"** (Gateway) that sits between the AI Agents and the actual data sources.
*   **How it works:**
    1.  **Registry:** The Gateway maintains the "Golden Source of Truth" for every tool.
    2.  **Governance:** It acts as a security checkpoint, ensuring scientists only access data they are authorized for (e.g., Phase 1 vs. Phase 3 trial data).
*   **Enterprise Scale:**
    *   **Resilience:** Agents don't break when backend systems change.
    *   **Compliance:** Full audit log of exactly who accessed what data and when (critical for FDA regulations).

---

## 5. Summary of Impact for Scientists

| Feature | Old Way (Standard Chatbot) | New Way (Recursive + Context Forge) |
| :--- | :--- | :--- |
| **Long Research** | "I forgot what we discussed last Tuesday." | "Here is the exact molecule we discussed last Tuesday, compared to today's finding." |
| **System Reliability** | "Error: Tool connection failed." | "System maintenance detected on Database A, rerouting to Backup Source B." |
| **Data Safety** | Agents blindly access whatever they can. | Strict, auditable access control for sensitive trial data. |

---

## 6. Proposed Architecture Evolution

### 4.1 The "Recursive Session Manager" (Cognitive)
We should refactor `streamlit-app/orchestration/session_manager.py` to be a **Retrieval Engine**.

**New Components:**
*   **`SessionDB`:** A lightweight SQLite + Vector store (e.g., ChromaDB/FAISS) replacing in-memory dicts.
*   **`SelfQueryRetriever`:** A standard tool exposed to the Agent Orchestrator allowing it to run semantic searches on its own history.
    *   *Tool:* `search_session_memory(query: str, time_range: str)`
*   **Recursive Summarization Loop:** A background job that runs every N turns to condense "Raw Turns" into "High-Level Insights" stored in the DB.

### 4.2 The "Governance Gateway" (Operational)
We should formalize the `docs/GOVERNANCE_LAYER.md` into a concrete **Context Gateway**.

**Implementation:**
*   **Context Proxy:** A lightweight FastAPI service that wraps the MCP servers.
*   **Dynamic Tool Registry:** When an agent initializes, it fetches tool definitions from the Gateway.
*   **Heartbeat:** The Gateway pings MCP servers. If `BioMCP` is down, it removes those tools from the context offering, so agents don't try to call dead tools (avoiding hallucinations/errors).

---

## 5. Implementation Roadmap

### Phase 1: Structured Persistence (Immediate)
*   **Goal:** Move `SessionManager` from Dicts to SQLite.
*   **Action:** Update `session_manager.py` to persist `ResearchSession` objects to a local `sessions.db`.

### Phase 2: RLM Integration (Short Term)
*   **Goal:** Give Agents the ability to query history.
*   **Action:** Create a new MCP tool `query_memory` that exposes the `sessions.db` to the Agent.
*   **Prompt Update:** Instruct the Orchestrator: *"If you need to recall past details, do not rely on your context window. Use the `query_memory` tool."*

### Phase 3: Context Gateway (Medium Term)
*   **Goal:** Centralized Tool Governance.
*   **Action:** Implement the `Governance Layer` as the `Context Forge`.
*   **Benefit:** Full audit trails and protection against tool rot.

---

## 6. Conclusion

By adopting **Recursive Language Model** patterns, we transform "Memory" from a passive, rotting list of text into an active, queryable database. By adopting the **IBM Context Forge** pattern, we secure our tool context against operational drift. This Dual-Context approach ensures the system remains intelligent and stable over long-running research campaigns.

![alt text](image.png)