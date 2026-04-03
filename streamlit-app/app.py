"""
Streamlit MCP Agent Application

A configurable application that supports multiple LLM providers:
- Standard: Anthropic Claude Sonnet 4.5 (open-source)
- Merck Enterprise: Azure OpenAI and AWS Bedrock (enterprise)
- Ollama: Local LLM via Ollama (qwen3:235b-thinking, llama3, etc.)

All MCP tool calls are mediated through the IBM Context Forge Gateway
for governance, audit logging, compliance, and rate limiting.
"""

import os
import streamlit as st
import asyncio
from typing import Optional
from agent import MCPAgent
from mcp_tools import initialize_mcp_tools, _active_wrappers
from config_manager import config_manager
from utils.llm_factory import validate_llm_setup
from governance import ContextForgeGateway

# Page configuration
st.set_page_config(
    page_title="MCP Agent - Pharmaceutical Research",
    page_icon="🧪",
    layout="wide"
)


def get_selected_configuration():
    """Get the selected configuration from session state or default."""
    if "selected_config" not in st.session_state:
        st.session_state.selected_config = "standard"  # Default to Standard (Claude)
    return st.session_state.selected_config


def load_configuration_data(config_name: str):
    """Load configuration data and cache it in session state."""
    cache_key = f"config_data_{config_name}"
    
    # Always reload configuration to pick up fresh environment variables
    try:
        config_data = config_manager.load_configuration(config_name)
        st.session_state[cache_key] = config_data
        return config_data
    except Exception as e:
        st.error(f"Failed to load {config_name} configuration: {str(e)}")
        return None


@st.cache_resource
def initialize_agent_with_config(config_name: str, _cache_buster: str = None):
    """Initialize the MCP agent with tools from configured servers and selected config.

    Context Forge Gateway is automatically initialized and registered with MCP
    wrappers so that all tool calls flow through governance (audit, compliance,
    rate limiting, health monitoring).
    """
    with st.spinner("Initializing agent..."):
        try:
            # Load configuration data
            config_data = load_configuration_data(config_name)
            if not config_data:
                return None

            # Get MCP servers from appropriate config
            if config_name in ("standard", "ollama"):
                mcp_servers = config_data.get("mcp_servers", {})
            else:
                # For Merck config, use the same MCP servers as standard config
                import config
                mcp_servers = getattr(config, 'MCP_SERVERS', {})

            tools = []
            if mcp_servers:
                try:
                    from mcp_tools import get_mcp_loop
                    loop = get_mcp_loop()

                    # Run initialize_mcp_tools in the background loop
                    future = asyncio.run_coroutine_threadsafe(
                        initialize_mcp_tools(mcp_servers),
                        loop
                    )
                    tools = future.result(timeout=60)

                    if tools:
                        st.info(f"Connected to MCP servers, loaded {len(tools)} tools")

                    # --- Context Forge Gateway ---
                    # Register live MCP wrappers with the governance gateway
                    feature_flags = config_data.get("feature_flags", {})
                    governance_enabled = feature_flags.get("use_governance_gateway", True)

                    if _active_wrappers and governance_enabled:
                        gateway = ContextForgeGateway()
                        gateway.register_mcp_wrappers(_active_wrappers)
                        # Store gateway in a way accessible to the rest of the app
                        st.session_state["gateway"] = gateway
                        st.info(
                            f"Context Forge Gateway active: "
                            f"{len(_active_wrappers)} MCP server(s) governed"
                        )

                except Exception as mcp_error:
                    st.warning(f"MCP servers not available: {str(mcp_error)}")
                    st.info("Running in direct LLM mode without MCP tools")
            else:
                st.info("Running in direct LLM mode without MCP tools")
            
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                try:
                    from utils.tavily_tool import get_tavily_tool
                    tavily_tool = get_tavily_tool()
                    tools.append(tavily_tool)
                    st.info("Tavily web search enabled")
                except Exception as tavily_error:
                    st.warning(f"Tavily not available: {str(tavily_error)}")
                    
            agent = MCPAgent(tools if tools else [], config_data)
            return agent

        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None


def display_intermediate_steps(steps):
    """Display the agents reasoning process."""
    if not steps:
        return

    with st.expander("View Agent Reasoning Process", expanded=False):
        for i, (action, observation) in enumerate(steps, 1):
            st.markdown(f"**Step {i}:**")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Action:**")
                st.code(f"Tool: {action.tool}\nInput: {action.tool_input}", language="text")

            with col2:
                st.markdown("**Observation:**")
                st.code(observation, language="text")

            st.divider()


def main():
    """Main Streamlit application."""

    # Get available configuration profiles
    profiles = config_manager.get_available_profiles()
    
    # Configuration selection in sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Configuration selection dropdown
        profile_options = {name: profile.display_name for name, profile in profiles.items()}
        selected_config = st.selectbox(
            "Select Configuration:",
            options=list(profile_options.keys()),
            format_func=lambda x: profile_options[x],
            index=1 if get_selected_configuration() == "merck" else 0,
            help="Choose between standard open-source or Merck enterprise configuration"
        )
        
        # Update session state if selection changed
        if selected_config != get_selected_configuration():
            st.session_state.selected_config = selected_config
            # Clear cached agent to force reinitialization
            st.cache_resource.clear()
            st.rerun()
        
        # Load and display current configuration info
        config_data = load_configuration_data(selected_config)
        if config_data:
            profile = config_data["profile"]
            
            # Display organization and description
            st.info(f"**{profile.organization}**\n\n{profile.description}")
            
            # Validate and display LLM setup
            llm_validation = validate_llm_setup(config_data)
            if llm_validation["ready"]:
                st.success(f"✅ LLM Ready")
                st.markdown(f"**Provider:** {llm_validation.get('provider', 'N/A')}")
                st.markdown(f"**Model:** {llm_validation.get('model', 'N/A')}")
                if "organization" in llm_validation:
                    st.markdown(f"**Organization:** {llm_validation['organization']}")
                    
                # Model selection for Merck configuration
                if selected_config == "merck" and "available_models" in config_data:
                    available_models = config_data.get("available_models", [])
                    current_model = config_data.get("primary_model", "gpt-4o")
                    
                    if available_models:
                        st.markdown("**Model Selection:**")
                        # Get model categorization
                        azure_models = config_data.get("azure_models", [])
                        bedrock_models = config_data.get("bedrock_models", [])
                        
                        # Create formatted model options showing provider
                        model_options = []
                        for model in available_models:
                            if model in azure_models:
                                model_options.append(f"🔵 Azure: {model}")
                            elif model in bedrock_models:
                                model_options.append(f"🟠 Bedrock: {model}")
                            else:
                                model_options.append(model)
                        
                        # Find current selection
                        current_index = 0
                        for i, model in enumerate(available_models):
                            if model == current_model:
                                current_index = i
                                break
                        
                        selected_index = st.selectbox(
                            "Choose Model (Azure OpenAI or AWS Bedrock):",
                            options=range(len(model_options)),
                            format_func=lambda x: model_options[x],
                            index=current_index,
                            help="Select the model to use for queries. Azure OpenAI (GPT models) or AWS Bedrock (Claude models)"
                        )
                        
                        selected_model = available_models[selected_index]
                        
                        # Update config_data if model changed
                        if selected_model != current_model:
                            config_data["primary_model"] = selected_model
                            st.session_state[f"config_data_{selected_config}"] = config_data
                            # Clear cached agent to force reinitialization with new model
                            st.cache_resource.clear()
                            
                            # Show which provider is being used
                            if selected_model in azure_models:
                                st.info(f"🔵 Switched to Azure OpenAI: {selected_model}")
                            elif selected_model in bedrock_models:
                                st.info(f"🟠 Switched to AWS Bedrock: {selected_model}")
                            else:
                                st.info(f"Model changed to: {selected_model}")
                            
            else:
                st.error("❌ LLM Not Ready")
                for error in llm_validation.get("errors", []):
                    st.error(f"• {error}")
            
            # Show MCP servers for all configurations
            if selected_config in ("standard", "ollama"):
                mcp_servers = config_data.get("mcp_servers", {})
                if mcp_servers:
                    st.markdown("**MCP Servers:**")
                    for server_name, server_config in mcp_servers.items():
                        st.markdown(f"• {server_name}: {server_config.get('description', 'N/A')}")
            else:
                # For Merck config, show available MCP servers
                import config
                mcp_servers = getattr(config, 'MCP_SERVERS', {})
                if mcp_servers:
                    st.markdown("**MCP Servers:**")
                    for server_name, server_config in mcp_servers.items():
                        st.markdown(f"• {server_name}: {server_config.get('description', 'N/A')}")
                else:
                    st.markdown("**Mode:** Direct LLM (No MCP servers)")
        
        st.divider()

        # Configuration-specific instructions
        if selected_config == "ollama":
            st.header("📋 Ollama Setup")
            st.markdown(
                """
                **Local Mode (Ollama):**
                1. Install Ollama: https://ollama.com
                2. Pull model: `ollama pull qwen3:235b-thinking`
                3. Start server: `ollama serve`
                4. No API key required.

                **Custom model:** Set `OLLAMA_MODEL` in `.env`
                """
            )
        elif selected_config == "standard":
            st.header("📋 Setup Instructions")
            st.markdown(
                """
                **Required:**
                1. Set `ANTHROPIC_API_KEY` in `.env` file
                2. Install: `pip install -r requirements.txt`

                **API Key Format:**
                ```
                ANTHROPIC_API_KEY=sk-ant-api03-...
                ```
                """
            )
        else:
            st.header("📋 Merck Setup")
            st.markdown(
                """
                **Unified Mode:**
                1. System now uses **Anthropic Claude 3.5**
                2. Set `ANTHROPIC_API_KEY` in your `.env`

                **Branding:**
                - Profile: `Merck Enterprise`
                - Org: `Merck R&D`
                """
            )

        st.divider()

        st.header("💡 Example Queries")
        if selected_config == "standard":
            st.markdown(
                """
                **Chemistry:**
                - What is the molecular formula of aspirin?
                - Find the structure of caffeine

                **Drug Development:**
                - What are the phases of clinical trials?
                - Explain bioavailability

                **Biology:**
                - How does CRISPR gene editing work?
                - What is the role of p53 in cancer?
                """
            )
        else:
            st.markdown(
                """
                **Pharmaceutical Analysis:**
                - Compare drug efficacy across trials
                - Analyze competitive landscape for diabetes drugs
                
                **Research Intelligence:**
                - Summarize recent publications on immunotherapy
                - Generate competitive intelligence report
                
                **Data Analysis:**
                - Statistical analysis of clinical trial outcomes
                - Trend analysis in drug development
                """
            )

    # Dynamic title based on configuration
    if config_data and config_data.get("profile"):
        profile = config_data["profile"]
        if profile.name == "merck":
            st.title("🧬 Merck Agentic Platform")
            st.markdown(f"**{config_data.get('system_name', 'Agentic Platform')}** - {profile.organization}")
        elif profile.name == "ollama":
            st.title("🧪 MCP Agent - Local Mode")
            model_name = config_data.get("ollama_model", "qwen3:235b-thinking")
            st.markdown(f"Running locally via **Ollama** ({model_name}) with Context Forge governance")
        else:
            st.title("🧪 MCP Agent - Pharmaceutical Research")
            st.markdown("Open-source pharmaceutical research intelligence system")
    else:
        st.title("🧪 MCP Agent - Pharmaceutical Research")

    # Initialize agent with selected configuration
    import time
    cache_buster = str(int(time.time() // 300))  # Change every 5 minutes to force fresh agent
    agent = initialize_agent_with_config(selected_config, cache_buster)

    if agent is None:
        st.error("Failed to initialize agent. Please check your configuration.")
        return

    # Display available tools
    with st.expander("Available Tools", expanded=False):
        tools = agent.get_available_tools()
        if tools:
            st.markdown("**Available MCP Tools:**")
            for tool in tools:
                st.markdown(f"• `{tool}`")
        else:
            st.info("Running in direct LLM mode without MCP tools")

    # Context Forge Gateway Status
    gateway = st.session_state.get("gateway")
    if gateway is not None:
        with st.expander("Context Forge Governance", expanded=False):
            stats = gateway.get_gateway_stats()
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                st.metric("Total Calls", stats.get("total_calls", 0))
            with g2:
                st.metric("Successful", stats.get("successful_calls", 0))
            with g3:
                st.metric("Compliance Blocks", stats.get("compliance_blocks", 0))
            with g4:
                st.metric("Governed Servers", stats.get("registered_servers", 0))

    st.divider()

    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Capture chat input at page level (outside columns) so it renders
    # at the natural page bottom without Streamlit container issues.
    prompt = st.chat_input("Ask about pharmaceutical research...")

    # --- Two-column layout: Chat (left) | Report Panel (right) ---
    chat_col, report_col = st.columns([3, 2])

    # ---- Left column: Chat interface ----
    with chat_col:
        st.header("Ask a Question")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "steps" in message and message["steps"]:
                    display_intermediate_steps(message["steps"])

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = agent.query(prompt)

                    response = result.get("output", "No response generated")
                    st.markdown(response)

                    steps = result.get("intermediate_steps", [])
                    if steps:
                        display_intermediate_steps(steps)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "steps": steps
                    })

        if st.button("Clear Chat History"):
            st.session_state.messages = []
            # Also clear report state tied to this conversation
            st.session_state.pop("generated_report", None)
            st.session_state.pop("identified_drug", None)
            st.session_state.pop("drug_msg_count", None)
            st.rerun()

    # ---- Right column: Report generation panel ----
    with report_col:
        from ui.report_panel import render_report_panel
        render_report_panel(agent)


if __name__ == "__main__":
    main()
