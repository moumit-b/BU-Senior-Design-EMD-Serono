"""
Streamlit MCP Agent Application

A configurable application that supports multiple LLM providers:
- Standard: Anthropic Claude Sonnet 4.5 (open-source)  
- Merck Enterprise: Azure OpenAI and AWS Bedrock (enterprise)
"""

import streamlit as st
import asyncio
from typing import Optional
from agent import MCPAgent
from mcp_tools import initialize_mcp_tools
from config_manager import config_manager
from utils.llm_factory import validate_llm_setup


# Page configuration
st.set_page_config(
    page_title="MCP Agent - Pharmaceutical Research",
    page_icon="🧪",
    layout="wide"
)


def get_selected_configuration():
    """Get the selected configuration from session state or default."""
    if "selected_config" not in st.session_state:
        st.session_state.selected_config = "standard"
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
def initialize_agent_with_config(config_name: str):
    """Initialize the MCP agent with tools from configured servers and selected config."""
    with st.spinner("Initializing agent..."):
        try:
            # Load configuration data
            config_data = load_configuration_data(config_name)
            if not config_data:
                return None
            
            # Get MCP servers from appropriate config
            if config_name == "standard":
                mcp_servers = config_data.get("mcp_servers", {})
            else:
                # For Merck config, use empty MCP servers for now (focus on LLM)
                mcp_servers = {}
            
            tools = []
            if mcp_servers:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    tools = loop.run_until_complete(initialize_mcp_tools(mcp_servers))
                    loop.close()

                    if tools:
                        st.info(f"Connected to MCP servers, loaded {len(tools)} tools")
                except Exception as mcp_error:
                    st.warning(f"MCP servers not available: {str(mcp_error)}")
                    st.info("Running in direct LLM mode without MCP tools")
            else:
                st.info("Running in direct LLM mode without MCP tools")

            agent = MCPAgent(tools if tools else [], config_data)
            return agent

        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None


def display_intermediate_steps(steps):
    """Display the agent's reasoning process."""
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
            index=0 if get_selected_configuration() == "standard" else 1,
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
            else:
                st.error("❌ LLM Not Ready")
                for error in llm_validation.get("errors", []):
                    st.error(f"• {error}")
            
            # Show MCP servers for standard config
            if selected_config == "standard":
                mcp_servers = config_data.get("mcp_servers", {})
                if mcp_servers:
                    st.markdown("**MCP Servers:**")
                    for server_name, server_config in mcp_servers.items():
                        st.markdown(f"• {server_name}: {server_config.get('description', 'N/A')}")
            else:
                st.markdown("**Mode:** Direct LLM (No MCP servers)")
        
        st.divider()
        
        # Configuration-specific instructions
        if selected_config == "standard":
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
                **Required:**
                1. Set `AZURE_OPENAI_API_KEY` or `AZURE_API_KEY`
                2. Access to Merck's Azure OpenAI endpoint
                
                **Environment Variables:**
                ```
                AZURE_OPENAI_API_KEY=your-key-here
                ```
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
        else:
            st.title("🧪 MCP Agent - Pharmaceutical Research")
            st.markdown("Open-source pharmaceutical research intelligence system")
    else:
        st.title("🧪 MCP Agent - Pharmaceutical Research")

    # Initialize agent with selected configuration
    agent = initialize_agent_with_config(selected_config)

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

    st.divider()

    # Query interface
    st.header("💬 Ask a Question")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "steps" in message and message["steps"]:
                display_intermediate_steps(message["steps"])

    if prompt := st.chat_input("Ask about pharmaceutical research..."):
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
        st.rerun()


if __name__ == "__main__":
    main()
