"""
Streamlit MCP Agent Application

A prototype application that uses LangChain agents with Ollama to query
MCP servers (like PubChem) for chemical compound information.
"""

import streamlit as st
import asyncio
from typing import Optional
from agent import MCPAgent
from mcp_tools import initialize_mcp_tools
from config import MCP_SERVERS, OLLAMA_MODEL


# Page configuration
st.set_page_config(
    page_title="MCP Agent - Chemical Compound Query",
    page_icon="🧪",
    layout="wide"
)


@st.cache_resource
def initialize_agent():
    """Initialize the MCP agent with tools from configured servers."""
    with st.spinner("Connecting to MCP servers and initializing agent..."):
        try:
            # Initialize MCP tools asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tools = loop.run_until_complete(initialize_mcp_tools(MCP_SERVERS))
            loop.close()

            if not tools:
                st.error("No tools were loaded from MCP servers. Check server configuration.")
                return None

            # Create agent with the tools
            agent = MCPAgent(tools)
            return agent

        except Exception as e:
            st.error(f"Failed to initialize agent: {str(e)}")
            return None


def display_intermediate_steps(steps):
    """Display the agent's reasoning process."""
    if not steps:
        return

    with st.expander("🔍 View Agent Reasoning Process", expanded=False):
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

    # Header
    st.title("Team 2 MCP Agent - Chemical Compound Query Prototype")
    st.markdown(
        """
        This application uses a LangChain agent powered by **Ollama** to query
        MCP servers for chemical compound information.
        """
    )

    # Sidebar with configuration info
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.markdown(f"**Model:** {OLLAMA_MODEL}")
        st.markdown(f"**MCP Servers:**")
        for server_name, config in MCP_SERVERS.items():
            st.markdown(f"- {server_name}: {config.get('description', 'N/A')}")

        st.divider()

        st.header("📚 Example Queries")
        st.markdown(
            """
            - What is the molecular formula of aspirin?
            - Tell me about caffeine
            - What is the molecular weight of ethanol?
            - Find information about glucose
            """
        )

        st.divider()

        st.header("ℹ️ About")
        st.markdown(
            """
            This is a prototype that demonstrates:
            - LangChain agents
            - Ollama (local LLM)
            - MCP server integration
            - PubChem chemical data
            """
        )

    # Initialize agent
    agent = initialize_agent()

    if agent is None:
        st.error("Failed to initialize agent. Please check your configuration and ensure:")
        st.markdown(
            """
            1. Ollama is running locally (`ollama serve`)
            2. The model is installed (`ollama pull llama3.2`)
            3. MCP servers are properly configured
            """
        )
        return

    # Display available tools
    with st.expander("🛠️ Available Tools", expanded=False):
        tools = agent.get_available_tools()
        if tools:
            for tool in tools:
                st.markdown(f"- `{tool}`")
        else:
            st.warning("No tools available")

    st.divider()

    # Query interface
    st.header("💬 Ask a Question")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "steps" in message and message["steps"]:
                display_intermediate_steps(message["steps"])

    # Chat input
    if prompt := st.chat_input("Ask about a chemical compound..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking and querying MCP servers..."):
                result = agent.query(prompt)

                # Display response
                response = result.get("output", "No response generated")
                st.markdown(response)

                # Display intermediate steps
                steps = result.get("intermediate_steps", [])
                if steps:
                    display_intermediate_steps(steps)

                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "steps": steps
                })

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
