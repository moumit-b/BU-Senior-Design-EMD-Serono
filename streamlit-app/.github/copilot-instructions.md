<!-- Copilot instructions for coding agents working on this repo -->
# Copilot Instructions — Streamlit multi-agent app

Purpose: Give an AI coding agent the minimal, high-value context to be productive quickly in this repository.

- Big picture:
  - This is a Streamlit app that orchestrates multiple domain-specific "agents" (chemical, clinical, gene, literature, data) via an orchestration layer.
  - Core flow: UI pages (Streamlit entrypoints) invoke the orchestrator(s) -> orchestrator composes tools/agents -> agents use `context` (database, vector store, memory retriever) -> governance intercepts via `governance/*`.
  - Entrypoints: `app.py` (main app) and Streamlit page files under `pages/` (e.g., `2_🧪_Dual_Orchestration_Lab.py`).

- Important directories and what to read first:
  - `agents/` — implementations of domain agents. Look at `orchestrator_agent.py` for orchestration patterns and at other `*_agent.py` files for agent interface expectations.
  - `orchestration/` — the glue: `agent_orchestrator.py`, `mcp_orchestrator.py`, `tool_composer.py`, and `session_manager.py` show how agents are composed and how sessions are tracked.
  - `context/` — persistence and retrieval: `database.py`, `vector_store.py`, `memory_retriever.py`, and `session_db.py` are key to how state and embeddings are stored/queried.
  - `governance/` — cross-cutting concerns: `audit_logger.py`, `compliance_engine.py`, `gateway.py` (request gating), and `rate_limiter.py` (throttling). Agents call these for policy enforcement and logging.
  - `utils/llm_factory.py` — centralized LLM construction and configuration. Prefer using this factory to create model clients so runtime settings and providers stay consistent.
  - `models/` — domain entities and composed tools; `composed_tool.py` demonstrates how multiple tools are packaged for the orchestrator.

- Project-specific conventions and patterns:
  - Agent classes live in `agents/` and follow a consistent method set (see `base_agent.py` for the interface). New agents should subclass `BaseAgent`.
  - Orchestration composes agents and tools via `tool_composer.py` — prefer adding capabilities here rather than calling agents directly from UI code.
  - Session lifecycle is managed by `session_manager.py` and `context/session_db.py` — use these helpers to create/restore session state.
  - Streamlit pages are placed in `pages/` and named using a numeric prefix and emoji. Follow existing filenames for ordering/UI layout.
  - Use `utils/llm_factory.py` to configure model parameters (temperature, provider) instead of instantiating LLMs inline.

- Developer workflows & run commands (discoverable in repo):
  - Create and activate a Python venv, then install deps:

    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

  - Run Streamlit locally (preferred):

    streamlit run app.py

  - There are convenience scripts: `run.sh` (macOS/Linux) and `run.bat` (Windows) — inspect them before changing.

- Integration points and external dependencies:
  - External LLM providers are configured in `utils/llm_factory.py` and via env vars used across the repo.
  - Vector store and DB backends are abstracted in `context/vector_store.py` and `context/database.py` — implementations may require API keys or local DB setup.
  - Governance components (gateway/compliance) sit between orchestrators and agents. Changes to request/response shapes should be coordinated across `governance/*` and `orchestration/*`.

- Coding guidelines specific to this codebase:
  - Keep LLM instantiation in `llm_factory.py`; modify provider or default params there.
  - Extend agents by subclassing `BaseAgent` in `agents/base_agent.py`; follow its method signatures and return data shapes used by `orchestration/agent_orchestrator.py`.
  - Persist session state via `session_manager.py` + `context/session_db.py` — do not write ad-hoc session files in pages.
  - When adding a new Streamlit page, put it in `pages/` and name with a numeric prefix to control ordering.

- Useful quick examples (grep these files to inspect patterns):
  - Agent interface: `agents/base_agent.py`
  - LLM creation: `utils/llm_factory.py`
  - Orchestration composition: `orchestration/tool_composer.py` and `orchestration/agent_orchestrator.py`
  - Persistence: `context/vector_store.py` and `context/database.py`

- If you need to make a change but are unsure where to place it:
  - For model/client config: change `utils/llm_factory.py`.
  - For agent behavior: add/modify classes in `agents/` and update `tool_composer.py` if exposing new capabilities to orchestrator.
  - For session or retrieval behavior: modify `orchestration/session_manager.py` or files in `context/`.

- Next steps / feedback:
  - If you want this file targeted to a specific agent automation (PR authoring, test generation, or migration assistant), say which focus and I'll tailor the instructions.
