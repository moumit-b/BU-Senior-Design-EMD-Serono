"""
Streamlit MCP Agent Application

A prototype application that uses LangChain agents with Claude Sonnet 4.5 to query
MCP servers for pharmaceutical research, chemistry, and drug development.
"""

import streamlit as st
import asyncio
from typing import Optional
from agent import MCPAgent
from mcp_tools import initialize_mcp_tools
from config import MCP_SERVERS, LLM_PROVIDER, CLAUDE_MODEL
from utils.llm_factory import validate_llm_setup


# Page configuration
st.set_page_config(
    page_title="MCP Agent - Pharmaceutical Research",
    page_icon="🧪",
    layout="wide"
)


@st.cache_resource
def initialize_agent():
    """Initialize the MCP agent with tools from configured servers."""
    with st.spinner("Initializing agent..."):
        try:
            tools = []
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tools = loop.run_until_complete(initialize_mcp_tools(MCP_SERVERS))
                loop.close()

                if tools:
                    st.info(f"Connected to MCP servers, loaded {len(tools)} tools")
            except Exception as mcp_error:
                st.warning(f"MCP servers not available: {str(mcp_error)}")
                st.info("Running in direct LLM mode without MCP tools")

            agent = MCPAgent(tools if tools else [])
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

    st.title("MCP Agent - Pharmaceutical Research Assistant")
    st.markdown(
        f"""
        This application uses a LangChain agent powered by **Claude Sonnet 4.5** for pharmaceutical
        research, chemistry, and drug development queries. Optionally connects to MCP servers for enhanced data access.
        """
    )

    # Sidebar with configuration info
    with st.sidebar:
        st.header("Configuration")

        llm_validation = validate_llm_setup()
        if llm_validation["ready"]:
            st.success(f"LLM Ready: {llm_validation.get('model', 'N/A')}")
        else:
            st.error("LLM Not Ready")
            for error in llm_validation.get("errors", []):
                st.error(error)

        st.markdown(f"**Provider:** {LLM_PROVIDER}")
        st.markdown(f"**Model:** {CLAUDE_MODEL}")
        st.markdown(f"**MCP Servers:**")
        for server_name, server_config in MCP_SERVERS.items():
            st.markdown(f"- {server_name}: {server_config.get('description', 'N/A')}")

        st.divider()

        st.header("Example Queries")
        st.markdown(
            """
            **Chemistry:**
            - What is the molecular formula of aspirin?
            - Explain the mechanism of action of ibuprofen

            **Drug Development:**
            - What are the phases of clinical trials?
            - Explain the concept of bioavailability

            **Biology:**
            - How does CRISPR gene editing work?
            - What is the role of p53 in cancer?
            """
        )

        st.divider()

        st.header("About")
        st.markdown(
            f"""
            This prototype demonstrates:
            - **LangChain agents** - Intelligent query routing
            - **Claude Sonnet 4.5** - Advanced LLM
            - **MCP server integration** - Optional data sources
            - **Pharmaceutical research** - Chemistry, biology, drug development
            """
        )

    # Initialize agent
    agent = initialize_agent()

    if agent is None:
        st.error("Failed to initialize agent. Please check your configuration.")
        st.markdown(
            """
            Make sure:
            1. `ANTHROPIC_API_KEY` is set in `.env` file or as environment variable
            2. Required packages are installed (`pip install -r requirements.txt`)
            """
        )
        return

    # Display available tools
    with st.expander("Available Tools", expanded=False):
        tools = agent.get_available_tools()
        if tools:
            for tool in tools:
                st.markdown(f"- `{tool}`")
        else:
            st.warning("No tools available - running in direct LLM mode")

    st.divider()

    # Query interface
    st.header("Ask a Question")

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
