"""
Pharma Research Intelligence Platform
EMD Serono · Multi-Agent Research System

Supports multiple LLM providers:
- Standard: Anthropic Claude Sonnet 4.5
- Enterprise: Azure OpenAI / AWS Bedrock (Merck config)
- Local: Ollama

All MCP tool calls flow through the Context Forge Gateway for
governance, audit logging, compliance, and rate limiting.
"""

import os
import time
import asyncio
import streamlit as st
from typing import Optional

import theme as _theme
from agent import MCPAgent
from mcp_tools import initialize_mcp_tools, _active_wrappers
from config_manager import config_manager
from utils.llm_factory import validate_llm_setup
from governance import ContextForgeGateway
from auth import init_default_users, render_login_page, get_current_user, logout
from ui.chat_history import render_sidebar_history, ensure_active_session, save_message
from context.chat_vector_store import ChatVectorStore


# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Pharma Research Intelligence",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# CSS injection — delegates to theme module
# ---------------------------------------------------------------------------

def _inject_css() -> None:
    active_theme = st.session_state.get("theme", "dark")
    st.markdown(_theme.get_css(active_theme), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------

@st.cache_resource
def get_db():
    """Initialize and return a shared DatabaseManager instance."""
    from context.database import DatabaseManager
    db = DatabaseManager()
    db.initialize()
    return db


@st.cache_resource
def get_chat_vector_store(_db):
    """Initialize ChatVectorStore (pgvector or numpy fallback)."""
    return ChatVectorStore(_db)


@st.cache_resource
def get_tool_tracker(_db):
    """Initialize persistent ToolMetricsTracker."""
    from metrics.tool_tracker import ToolMetricsTracker
    return ToolMetricsTracker(_db)


def load_configuration_data(config_name: str):
    """Load configuration data into session state."""
    cache_key = f"config_data_{config_name}"
    try:
        config_data = config_manager.load_configuration(config_name)
        st.session_state[cache_key] = config_data
        return config_data
    except Exception as e:
        st.error(f"Failed to load {config_name} configuration: {e}")
        return None


def get_selected_configuration() -> str:
    if "selected_config" not in st.session_state:
        st.session_state.selected_config = "standard"
    return st.session_state.selected_config


@st.cache_resource
def initialize_agent_with_config(config_name: str, _cache_buster: str = None):
    """
    Initialize the MCP agent with tools, governance gateway, and orchestrator.
    Passes tool_tracker so all direct tool calls are recorded persistently.
    """
    with st.spinner("Initializing agent…"):
        try:
            config_data = load_configuration_data(config_name)
            if not config_data:
                return None

            if config_name in ("standard", "ollama"):
                mcp_servers = config_data.get("mcp_servers", {})
            else:
                import config as _cfg
                mcp_servers = getattr(_cfg, "MCP_SERVERS", {})

            tools = []
            if mcp_servers:
                try:
                    from mcp_tools import get_mcp_loop
                    loop = get_mcp_loop()
                    future = asyncio.run_coroutine_threadsafe(
                        initialize_mcp_tools(mcp_servers), loop
                    )
                    tools = future.result(timeout=300)
                except Exception as mcp_err:
                    import traceback as _tb
                    print(f"[ERROR] MCP init: {mcp_err}\n{_tb.format_exc()}")
                    st.warning(f"MCP servers unavailable: {type(mcp_err).__name__}")

                if _active_wrappers:
                    feature_flags = config_data.get("feature_flags", {})
                    governance_enabled = feature_flags.get("use_governance_gateway", True)
                    try:
                        if governance_enabled:
                            gateway = ContextForgeGateway()
                            gateway.register_mcp_wrappers(_active_wrappers)
                            st.session_state["gateway"] = gateway

                            from orchestration.mcp_orchestrator import MCPOrchestrator
                            mcp_orch = MCPOrchestrator(mcp_wrappers=_active_wrappers)
                            mcp_orch.set_gateway(gateway)
                            st.session_state["mcp_orchestrator"] = mcp_orch
                        else:
                            from orchestration.mcp_orchestrator import MCPOrchestrator
                            mcp_orch = MCPOrchestrator(mcp_wrappers=_active_wrappers)
                            st.session_state["mcp_orchestrator"] = mcp_orch
                    except Exception as gw_err:
                        import traceback as _tb
                        print(f"[ERROR] Gateway: {gw_err}\n{_tb.format_exc()}")
                        try:
                            from orchestration.mcp_orchestrator import MCPOrchestrator
                            st.session_state["mcp_orchestrator"] = MCPOrchestrator(
                                mcp_wrappers=_active_wrappers
                            )
                        except Exception:
                            pass

            tavily_key = os.getenv("TAVILY_API_KEY")
            if tavily_key:
                try:
                    from utils.tavily_tool import get_tavily_tool
                    tools.append(get_tavily_tool())
                except Exception:
                    pass

            # Get tracker for persistent metrics
            db = get_db()
            tracker = get_tool_tracker(db)

            agent = MCPAgent(tools if tools else [], config_data, tool_tracker=tracker)
            return agent

        except Exception as e:
            st.error(f"Agent initialization failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def display_intermediate_steps(steps) -> None:
    """Render agent reasoning steps in a collapsible expander."""
    if not steps:
        return
    with st.expander(f"Agent Reasoning — {len(steps)} step{'s' if len(steps) != 1 else ''}", expanded=False):
        for i, (action, observation) in enumerate(steps, 1):
            p = _theme._PALETTES.get(st.session_state.get("theme", "dark"), _theme.DARK)
            st.markdown(
                f"<div style='font-size:0.75rem;font-weight:600;letter-spacing:0.08em;"
                f"text-transform:uppercase;color:{p.text_muted};margin-bottom:0.4rem'>"
                f"Step {i}</div>",
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f"<div style='font-size:0.72rem;font-weight:600;letter-spacing:0.06em;"
                    f"text-transform:uppercase;color:{p.accent};margin-bottom:0.3rem'>Action</div>",
                    unsafe_allow_html=True,
                )
                st.code(
                    f"Tool: {action.tool}\nInput: {action.tool_input}",
                    language="text",
                )
            with col2:
                st.markdown(
                    f"<div style='font-size:0.72rem;font-weight:600;letter-spacing:0.06em;"
                    f"text-transform:uppercase;color:{p.success};margin-bottom:0.3rem'>Observation</div>",
                    unsafe_allow_html=True,
                )
                st.code(str(observation)[:800], language="text")
            if i < len(steps):
                st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)


def _render_sidebar_config(profiles) -> str:
    """
    Render configuration section in sidebar. Returns selected config name.
    """
    # Theme toggle — top right of brand section
    col_brand, col_toggle = st.columns([5, 1])
    with col_brand:
        st.markdown(
            "<div class='sidebar-icon'>⬡</div>"
            "<div class='sidebar-brand'>EMD Serono</div>"
            "<div class='sidebar-title'>Research Intelligence</div>"
            "<div class='sidebar-subtitle'>Multi-Agent Research Platform</div>",
            unsafe_allow_html=True,
        )
    with col_toggle:
        current_theme = st.session_state.get("theme", "dark")
        toggle_icon = "☀️" if current_theme == "dark" else "🌙"
        if st.button(toggle_icon, key="theme_toggle", help="Toggle light/dark mode"):
            st.session_state["theme"] = "light" if current_theme == "dark" else "dark"
            st.rerun()

    profile_options = {name: p.display_name for name, p in profiles.items()}
    current = get_selected_configuration()

    selected = st.selectbox(
        "Configuration",
        options=list(profile_options.keys()),
        format_func=lambda x: profile_options[x],
        index=list(profile_options.keys()).index(current)
        if current in profile_options else 0,
        label_visibility="collapsed",
        key="config_selector",
    )

    if selected != current:
        st.session_state.selected_config = selected
        st.cache_resource.clear()
        st.rerun()

    # Compact LLM status
    config_data = load_configuration_data(selected)
    if config_data:
        llm_val = validate_llm_setup(config_data)
        if llm_val["ready"]:
            model = llm_val.get("model", "")
            short_model = model.split("/")[-1] if "/" in model else model
            st.markdown(
                f"<div class='llm-status'>"
                f"<span class='dot ok'></span>"
                f"{short_model or llm_val.get('provider','LLM')} · Ready"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='llm-status'>"
                "<span class='dot err'></span>LLM not configured"
                "</div>",
                unsafe_allow_html=True,
            )

        # Model selector for Merck config
        if selected == "merck" and "available_models" in config_data:
            available_models = config_data.get("available_models", [])
            current_model = config_data.get("primary_model", "gpt-4o")
            azure_models = config_data.get("azure_models", [])
            bedrock_models = config_data.get("bedrock_models", [])

            if available_models:
                model_labels = []
                for m in available_models:
                    if m in azure_models:
                        model_labels.append(f"Azure · {m}")
                    elif m in bedrock_models:
                        model_labels.append(f"Bedrock · {m}")
                    else:
                        model_labels.append(m)

                cur_idx = next(
                    (i for i, m in enumerate(available_models) if m == current_model), 0
                )
                sel_idx = st.selectbox(
                    "Model",
                    options=range(len(model_labels)),
                    format_func=lambda x: model_labels[x],
                    index=cur_idx,
                    key="merck_model_selector",
                )
                if available_models[sel_idx] != current_model:
                    config_data["primary_model"] = available_models[sel_idx]
                    st.session_state[f"config_data_{selected}"] = config_data
                    st.cache_resource.clear()

    return selected


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _inject_css()

    db = get_db()
    init_default_users(db)

    # Auth gate — show login page and stop if not authenticated
    if not st.session_state.get("authenticated"):
        render_login_page(db)
        return

    user = get_current_user()
    user_id = user["user_id"]
    display_name = user.get("display_name", user.get("username", "User"))

    vs = get_chat_vector_store(db)
    tracker = get_tool_tracker(db)
    st.session_state["tool_tracker"] = tracker

    # ── Sidebar ──────────────────────────────────────────────────────────
    profiles = config_manager.get_available_profiles()

    p = _theme._PALETTES.get(st.session_state.get("theme", "dark"), _theme.DARK)

    with st.sidebar:
        selected_config = _render_sidebar_config(profiles)

        st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

        # Chat history (new conversation button + session list)
        render_sidebar_history(db, user_id)

        st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

        st.markdown(
            f"<div style='font-size:0.72rem;color:{p.text_muted};margin-bottom:0.5rem'>"
            f"Signed in as <strong style='color:{p.text_secondary}'>{display_name}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", use_container_width=True):
            logout()
            st.rerun()

    # ── Page header ───────────────────────────────────────────────────────
    st.markdown(
        "<div class='page-header'>"
        "<h1>Pharma Research Intelligence</h1>"
        "<span class='sub'>EMD Serono · Multi-Agent Research System</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Agent initialization ──────────────────────────────────────────────
    cache_buster = str(int(time.time() // 300))
    agent = initialize_agent_with_config(selected_config, cache_buster)

    if agent is None:
        st.error("Agent initialization failed. Please check your LLM configuration.")
        return

    # ── Active session ────────────────────────────────────────────────────
    chat_session_id = ensure_active_session(db, user_id)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_research, tab_reports, tab_metrics, tab_governance, tab_catalog = st.tabs([
        "Research", "Reports", "Tool Metrics", "Governance", "Tool Catalog"
    ])

    # ── Tab 1: Research ───────────────────────────────────────────────────
    with tab_research:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Render message history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("steps"):
                    display_intermediate_steps(message["steps"])

        # Chat input
        prompt = st.chat_input("Ask about pharmaceutical research…")

        if prompt:
            # Render user message immediately
            st.session_state.messages.append({"role": "user", "content": prompt})
            save_message(db, chat_session_id, "user", prompt)

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Researching…"):
                    result = agent.query(prompt, conversation_history=st.session_state.messages)
                    response = result.get("output", "No response generated.")
                    steps = result.get("intermediate_steps", [])

                st.markdown(response)
                if steps:
                    display_intermediate_steps(steps)

            # Persist assistant response
            save_message(db, chat_session_id, "assistant", response, steps)

            # Embed exchange in vector store for future semantic retrieval
            try:
                vs.add_chat_context(chat_session_id, user_id, prompt, response)
            except Exception:
                pass

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "steps": steps,
            })

    # ── Tab 2: Reports ────────────────────────────────────────────────────
    with tab_reports:
        from ui.report_panel import render_report_panel
        render_report_panel(agent, db_manager=db, vector_store=vs)

    # ── Tab 3: Tool Metrics ───────────────────────────────────────────────
    with tab_metrics:
        from ui.tool_metrics_tab import render_tool_metrics
        render_tool_metrics(db)

    # ── Tab 4: Governance ─────────────────────────────────────────────────
    with tab_governance:
        from ui.governance_tab import render_governance_tab
        render_governance_tab(st.session_state.get("gateway"))

    # ── Tab 5: Tool Catalog ───────────────────────────────────────────────
    with tab_catalog:
        from ui.tool_catalog_tab import render_tool_catalog
        render_tool_catalog(_active_wrappers)


if __name__ == "__main__":
    main()
