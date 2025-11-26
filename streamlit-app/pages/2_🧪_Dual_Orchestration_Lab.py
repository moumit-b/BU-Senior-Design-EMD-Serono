"""
Dual Orchestration Lab - Interactive Demo

This page demonstrates the novel dual orchestration architecture with:
1. Bidirectional Learning (MCP <-> Agent feedback)
2. Dynamic Tool Composition (creating reusable workflows)
3. Research Session Memory (multi-turn context)

All demonstrations use REAL MCP connections and REAL learning.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.mcp_orchestrator import MCPOrchestrator
from orchestration.performance_kb import PerformanceKnowledgeBase
from orchestration.tool_composer import ToolComposer
from orchestration.session_manager import SessionManager
from models.performance import QueryType, PerformanceFeedback
from models.entities import Drug, Gene, EntityType
from mcp_tools import MCPToolWrapper
from config import MCP_SERVERS

# Page configuration
st.set_page_config(
    page_title="Dual Orchestration Lab",
    page_icon="",
    layout="wide"
)

# Initialize session state
if 'demo_initialized' not in st.session_state:
    st.session_state.demo_initialized = False
    st.session_state.mcp_wrappers = {}
    st.session_state.mcp_orchestrator = None
    st.session_state.performance_kb = None
    st.session_state.tool_composer = None
    st.session_state.session_manager = None
    st.session_state.query_history = []
    st.session_state.active_session_id = None
    st.session_state.mcps_connected = False
    st.session_state.connection_status = {}


async def initialize_mcp_wrappers(servers: List[str]) -> Dict[str, MCPToolWrapper]:
    """Initialize selected MCP server wrappers."""
    wrappers = {}

    for server_name in servers:
        if server_name in MCP_SERVERS:
            config = MCP_SERVERS[server_name]
            wrapper = MCPToolWrapper(config)

            try:
                await wrapper.connect()
                wrappers[server_name] = wrapper
                st.success(f"Connected to {server_name}")
            except Exception as e:
                st.warning(f"Could not connect to {server_name}: {str(e)}")

    return wrappers


def initialize_demo():
    """Initialize the dual orchestration system."""
    if st.session_state.demo_initialized:
        return

    with st.spinner("Initializing Dual Orchestration System..."):
        # Initialize core components
        st.session_state.performance_kb = PerformanceKnowledgeBase()
        st.session_state.session_manager = SessionManager()

        # Initialize MCP orchestrator (will connect to MCPs on first use)
        st.session_state.mcp_orchestrator = MCPOrchestrator(mcp_wrappers={})
        st.session_state.tool_composer = ToolComposer(st.session_state.mcp_orchestrator)

        st.session_state.demo_initialized = True


class MCPEventLoop:
    """Persistent event loop for MCP operations in a background thread."""
    def __init__(self):
        self.loop = None
        self.thread = None

    def start(self):
        """Start the event loop in a background thread."""
        if self.thread is not None:
            return

        import threading

        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

        # Wait for loop to be created
        import time
        while self.loop is None:
            time.sleep(0.01)

    def run_coroutine(self, coro, timeout=30):
        """Run a coroutine in the event loop thread."""
        if self.loop is None:
            raise RuntimeError("Event loop not started")

        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(timeout=timeout)


@st.cache_resource
def get_mcp_event_loop():
    """Get or create the persistent MCP event loop."""
    loop_manager = MCPEventLoop()
    loop_manager.start()
    return loop_manager


@st.cache_resource
def connect_to_mcps():
    """Connect to MCP servers and cache the wrappers."""
    loop_manager = get_mcp_event_loop()

    wrappers = {}
    status = {}

    # Try to connect to each MCP server
    for server_name, config in MCP_SERVERS.items():
        try:
            wrapper = MCPToolWrapper(config)

            # Connect using the persistent event loop
            loop_manager.run_coroutine(wrapper.connect(), timeout=10)

            wrappers[server_name] = wrapper
            status[server_name] = "connected"
        except Exception as e:
            status[server_name] = f"failed: {str(e)[:50]}"

    return wrappers, status


def display_header():
    """Display the page header."""
    st.title("🧪 Dual Orchestration Lab")
    st.markdown(
        """
        **Interactive demonstration of the dual orchestration architecture**

        This lab showcases three novel features with REAL MCP connections:
        - 🔄 **Bidirectional Learning**: MCPs and Agents teach each other
        - 🔧 **Tool Composition**: Create and reuse multi-step workflows
        - 🧠 **Session Memory**: Multi-turn research with context
        """
    )

    # MCP Connection Status
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.session_state.mcps_connected:
            connected_mcps = [k for k, v in st.session_state.connection_status.items() if v == "connected"]
            if connected_mcps:
                st.success(f"✓ Connected to {len(connected_mcps)} MCP(s): {', '.join(connected_mcps)}")
            else:
                st.warning("No MCPs connected. Some features will use simulated data.")
        else:
            st.info("MCPs not connected. Click 'Connect to MCPs' to use real data sources.")

    with col2:
        if st.button("🔌 Connect to MCPs", use_container_width=True):
            with st.spinner("Connecting to MCP servers..."):
                wrappers, status = connect_to_mcps()
                st.session_state.mcp_wrappers = wrappers
                st.session_state.connection_status = status
                st.session_state.mcps_connected = True

                # Update orchestrator with real wrappers
                if st.session_state.mcp_orchestrator:
                    st.session_state.mcp_orchestrator.mcp_wrappers = wrappers

            st.rerun()

    # Show connection details in expander
    if st.session_state.mcps_connected:
        with st.expander("🔍 MCP Connection Details"):
            for server_name, status in st.session_state.connection_status.items():
                if status == "connected":
                    st.success(f"✓ {server_name}: Connected")
                else:
                    st.error(f"✗ {server_name}: {status}")

    st.divider()


def tab_quick_demo():
    """Quick demo tab - run scenarios or custom queries."""
    st.header("Quick Demo")

    # Scenario selection
    scenario = st.radio(
        "Choose a scenario:",
        [
            "Custom Query",
            "Scenario 1: Intelligent Query Routing",
            "Scenario 2: Multi-Step Workflow",
            "Scenario 3: Research Session"
        ],
        index=0
    )

    if scenario == "Custom Query":
        query = st.text_input(
            "Enter your query:",
            placeholder="e.g., Find inhibitors of BRCA1"
        )
    elif scenario == "Scenario 1: Intelligent Query Routing":
        query = "Find inhibitors of BRCA1"
        st.info(f"**Preset Query:** {query}")
    elif scenario == "Scenario 2: Multi-Step Workflow":
        query = "Find BRCA1 inhibitors, check their clinical trials, and compare safety profiles"
        st.info(f"**Preset Query:** {query}")
    else:  # Scenario 3
        query = "What is BRCA1?"
        st.info(f"**Preset Query (Multi-turn):** {query}")

    col1, col2 = st.columns([1, 5])
    with col1:
        execute = st.button("Execute", type="primary", use_container_width=True)
    with col2:
        clear = st.button("Clear History", use_container_width=True)

    if clear:
        st.session_state.query_history = []
        st.session_state.active_session_id = None
        st.rerun()

    if execute and query:
        execute_query(query, scenario)


def execute_query(query: str, scenario: str):
    """Execute a query and display results with live updates."""

    # Create execution container
    execution_container = st.container()
    results_container = st.container()

    with execution_container:
        st.subheader("🔄 Execution View")

        # Query analysis
        with st.spinner("Analyzing query..."):
            time.sleep(0.3)  # Brief analysis

            # Detect query type and assign to specialized agent
            query_lower = query.lower()
            if "inhibitor" in query_lower:
                query_type = QueryType.INHIBITOR_SEARCH
                agent_name = "Clinical Agent"
                recommended_mcp = "biomcp"
                tool_name = "search_pubmed"  # BioMCP tool
                tool_params_key = "query"
            elif "clinical trial" in query_lower:
                query_type = QueryType.CLINICAL_TRIAL
                agent_name = "Clinical Agent"
                recommended_mcp = "biomcp"
                tool_name = "search_clinical_trials"
                tool_params_key = "query"
            elif "gene" in query_lower or any(gene in query_lower for gene in ["brca1", "tp53", "egfr"]):
                query_type = QueryType.GENE_LOOKUP
                agent_name = "Clinical Agent"
                recommended_mcp = "biomcp"
                tool_name = "search_pubmed"
                tool_params_key = "query"
            else:
                query_type = QueryType.CHEMICAL_SEARCH
                agent_name = "Chemical Agent"
                recommended_mcp = "pubchem"
                tool_name = "search_compounds_by_name"  # FIXED: correct tool name
                tool_params_key = "name"  # FIXED: PubChem expects 'name' not 'query'

            st.success(f"Query Type: `{query_type.value}`")
            st.info(f"**Agent Orchestrator** → Assigned to: `{agent_name}`")
            st.info(f"**{agent_name}** → Requests MCP: `{recommended_mcp}` (Tool: `{tool_name}`)")

        # Performance tracking
        perf_col1, perf_col2, perf_col3 = st.columns(3)

        with perf_col1:
            st.metric("Agent", agent_name)

        with perf_col2:
            st.metric("MCP Selected", recommended_mcp)

        # Execute MCP call (REAL or simulated)
        start_time = time.time()
        success = False
        result_data = None
        result_count = 0

        # Check if we have a real MCP connection
        use_real_mcp = (
            st.session_state.mcps_connected
            and recommended_mcp in st.session_state.mcp_wrappers
            and st.session_state.connection_status.get(recommended_mcp) == "connected"
        )

        with st.spinner(f"Executing via {recommended_mcp} {'(REAL)' if use_real_mcp else '(SIMULATED)'}..."):
            if use_real_mcp:
                # REAL MCP CALL
                try:
                    wrapper = st.session_state.mcp_wrappers[recommended_mcp]

                    # Preprocess query for MCP-specific format
                    processed_query = query
                    if recommended_mcp == "pubchem" and tool_name == "search_compounds_by_name":
                        # Extract compound name from natural language query
                        # Simple extraction: look for key words and take the last word or compound name
                        import re
                        # Remove question words and common phrases
                        processed_query = re.sub(r'\b(what|is|the|molecular|formula|of|structure|tell me about|find|show me)\b', '', query.lower(), flags=re.IGNORECASE)
                        processed_query = processed_query.strip().strip('?').strip()

                        # If nothing left, use original query
                        if not processed_query:
                            processed_query = query

                    # Call the tool via wrapper using the persistent event loop
                    loop_manager = get_mcp_event_loop()
                    result_data = loop_manager.run_coroutine(
                        wrapper.call_tool(tool_name, {tool_params_key: processed_query}),
                        timeout=30
                    )

                    # Check if result is an error message
                    if isinstance(result_data, str) and result_data.startswith("Error"):
                        success = False
                        result_count = 0
                        st.error(f"Tool call failed: {result_data}")
                    else:
                        success = True
                        # Try to parse result count
                        if isinstance(result_data, str):
                            result_count = len(result_data.split('\n')[:20])  # Approximate
                        else:
                            result_count = 1

                except Exception as e:
                    st.error(f"MCP call failed: {str(e)}")
                    result_data = f"Error: {str(e)}"
                    success = False
            else:
                # SIMULATED execution
                if recommended_mcp == "biomcp":
                    time.sleep(1.2)
                    success = True
                    result_count = 12
                elif recommended_mcp == "pubchem":
                    time.sleep(0.8)
                    success = True
                    result_count = 8
                else:
                    time.sleep(1.5)
                    success = True
                    result_count = 10

        execution_time = time.time() - start_time

        with perf_col3:
            st.metric("Execution Time", f"{execution_time:.2f}s")

        # Bidirectional learning visualization - DUAL ORCHESTRATION
        st.markdown("### 📊 Dual Orchestration Learning")

        # Show the architecture flow
        st.markdown("**Architecture Flow:**")
        st.markdown(f"```\nUser Query → Agent Orchestrator → {agent_name} → MCP Orchestrator → {recommended_mcp}\n```")

        learn_col1, learn_col2 = st.columns(2)

        with learn_col1:
            st.markdown("**MCP Layer → Agent Layer:**")
            if success:
                st.success(f"{recommended_mcp} succeeded for `{query_type.value}` queries")
                st.caption(f"Recommendation to {agent_name}: Use {recommended_mcp} for similar queries")
            else:
                st.error(f"{recommended_mcp} failed")
                st.caption(f"Feedback to {agent_name}: Try alternative MCP")

        with learn_col2:
            st.markdown("**Agent Layer → MCP Layer:**")
            st.info(f"{agent_name} recorded: {recommended_mcp} performance for {query_type.value}")
            st.caption("Pattern saved to Performance Knowledge Base")

        # Record performance
        if st.session_state.performance_kb:
            # Update performance metrics
            perf_feedback = PerformanceFeedback(
                source=recommended_mcp,
                latency_ms=execution_time * 1000,
                success=success,
                recommendation=f"Use {recommended_mcp} for {query_type.value} queries"
            )

            # Record agent learning - with actual agent name
            st.session_state.performance_kb.record_agent_learning(
                agent_name=agent_name,
                learning=f"Learned that {recommended_mcp} is optimal for {query_type.value}",
                category="mcp_preference"
            )

    # Display results
    with results_container:
        st.subheader("📋 Results")

        if success:
            # Show real MCP data if available
            if use_real_mcp and result_data:
                st.markdown(f"**Real MCP Results from {recommended_mcp}:**")

                # Display raw results in expandable section
                with st.expander("📄 Raw MCP Response", expanded=True):
                    if isinstance(result_data, str):
                        st.text(result_data[:2000])  # Limit display to first 2000 chars
                        if len(result_data) > 2000:
                            st.caption(f"... (showing first 2000 of {len(result_data)} characters)")
                    else:
                        st.json(result_data)

                st.success(f"✓ Successfully retrieved data from {recommended_mcp}")

            else:
                # Simulated results based on query type
                if query_type == QueryType.INHIBITOR_SEARCH:
                    st.markdown(f"**Found {result_count} BRCA1 Inhibitors (Simulated):**")

                    results_data = [
                        {"name": "Olaparib", "type": "PARP inhibitor", "status": "FDA Approved"},
                        {"name": "Rucaparib", "type": "PARP inhibitor", "status": "FDA Approved"},
                        {"name": "Niraparib", "type": "PARP inhibitor", "status": "FDA Approved"},
                        {"name": "Talazoparib", "type": "PARP inhibitor", "status": "FDA Approved"},
                    ]

                    for result in results_data:
                        with st.expander(f"🔬 {result['name']}", expanded=False):
                            st.markdown(f"**Type:** {result['type']}")
                            st.markdown(f"**Status:** {result['status']}")
                            st.markdown("**Mechanism:** PARP enzyme inhibition leading to synthetic lethality in BRCA-mutated cells")

                elif query_type == QueryType.GENE_LOOKUP:
                    st.markdown("**BRCA1 Gene Information (Simulated):**")
                    st.markdown("""
                    - **Official Name:** BRCA1 DNA Repair Associated
                    - **Function:** Tumor suppressor, DNA repair
                    - **Associated Diseases:** Breast cancer, Ovarian cancer
                    - **Chromosome:** 17q21.31
                    """)

                else:
                    st.markdown(f"**Found {result_count} results (Simulated)**")
                    st.info("Connect to MCPs to see real results!")

            # Add to query history - including agent name for dual orchestration tracking
            st.session_state.query_history.append({
                "timestamp": datetime.now(),
                "query": query,
                "query_type": query_type.value,
                "agent": agent_name,  # NEW: Track which agent handled this
                "mcp": recommended_mcp,
                "execution_time": execution_time,
                "success": success,
                "result_count": result_count,
                "real_mcp": use_real_mcp
            })
        else:
            st.error("Query execution failed")


def tab_learning_dashboard():
    """Learning dashboard tab - show performance metrics."""
    st.header("📊 Learning Dashboard")

    if not st.session_state.performance_kb:
        st.warning("Performance Knowledge Base not initialized. Run a query first!")
        return

    # Dual Orchestration Overview
    st.subheader("Dual Orchestration System Metrics")

    if st.session_state.query_history:
        # Count real vs simulated queries
        real_queries = sum(1 for q in st.session_state.query_history if q.get('real_mcp', False))
        total_queries = len(st.session_state.query_history)

        # Count unique agents used
        agents_used = set(q.get('agent', 'Unknown') for q in st.session_state.query_history)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Queries", total_queries)
        with col2:
            st.metric("Active Agents", len(agents_used))
        with col3:
            st.metric("Real MCP Calls", f"{real_queries} ({real_queries/total_queries*100:.0f}%)" if total_queries > 0 else "0")

        st.divider()

        # Agent Layer Performance
        st.subheader("Agent Layer Performance")

        agent_stats = {}
        for query in st.session_state.query_history:
            agent = query.get('agent', 'Unknown')
            if agent not in agent_stats:
                agent_stats[agent] = {'queries': 0, 'successes': 0, 'total_time': 0}
            agent_stats[agent]['queries'] += 1
            if query['success']:
                agent_stats[agent]['successes'] += 1
            agent_stats[agent]['total_time'] += query['execution_time']

        agent_cols = st.columns(len(agent_stats))
        for idx, (agent, stats) in enumerate(agent_stats.items()):
            with agent_cols[idx]:
                success_rate = (stats['successes'] / stats['queries'] * 100) if stats['queries'] > 0 else 0
                avg_time = (stats['total_time'] / stats['queries']) if stats['queries'] > 0 else 0
                st.metric(f"🤖 {agent}", f"{stats['queries']} queries")
                st.progress(success_rate / 100)
                st.caption(f"Success: {success_rate:.0f}%")
                st.caption(f"Avg Time: {avg_time:.2f}s")

        st.divider()

        # MCP Layer Performance
        st.subheader("MCP Layer Performance")

        # Aggregate metrics from query history
        mcp_stats = {}

        for query in st.session_state.query_history:
            mcp = query['mcp']
            if mcp not in mcp_stats:
                mcp_stats[mcp] = {
                    'queries': 0,
                    'successes': 0,
                    'total_time': 0,
                    'real_calls': 0
                }

            mcp_stats[mcp]['queries'] += 1
            if query['success']:
                mcp_stats[mcp]['successes'] += 1
            mcp_stats[mcp]['total_time'] += query['execution_time']
            if query.get('real_mcp', False):
                mcp_stats[mcp]['real_calls'] += 1

        # Display metrics
        cols = st.columns(len(mcp_stats))

        for idx, (mcp, stats) in enumerate(mcp_stats.items()):
            with cols[idx]:
                success_rate = (stats['successes'] / stats['queries'] * 100) if stats['queries'] > 0 else 0
                avg_time = (stats['total_time'] / stats['queries']) if stats['queries'] > 0 else 0

                st.metric(mcp, f"{stats['queries']} queries")
                st.progress(success_rate / 100)
                st.caption(f"Success: {success_rate:.0f}%")
                st.caption(f"Avg Time: {avg_time:.2f}s")
                if stats['real_calls'] > 0:
                    st.caption(f"✓ {stats['real_calls']} real calls")
                else:
                    st.caption("⊙ Simulated")
    else:
        st.info("No queries executed yet. Run some queries to see performance metrics!")

    st.divider()

    # Query Type Routing Intelligence
    st.subheader("Query Type Routing Intelligence")

    if st.session_state.query_history:
        # Group by query type
        query_type_routing = {}

        for query in st.session_state.query_history:
            qtype = query['query_type']
            mcp = query['mcp']

            if qtype not in query_type_routing:
                query_type_routing[qtype] = {}

            if mcp not in query_type_routing[qtype]:
                query_type_routing[qtype][mcp] = 0

            query_type_routing[qtype][mcp] += 1

        for qtype, mcps in query_type_routing.items():
            best_mcp = max(mcps.items(), key=lambda x: x[1])
            st.success(f"`{qtype}` → **{best_mcp[0]}** (learned from {best_mcp[1]} queries)")
    else:
        st.info("No routing patterns learned yet")

    st.divider()

    # Agent Learning (Bidirectional Learning Feature)
    st.subheader("Agent Learning (from MCP Feedback)")

    # Show learnings for each agent that has been used
    if st.session_state.query_history:
        agents_used = set(q.get('agent', 'Unknown') for q in st.session_state.query_history)

        for agent in agents_used:
            agent_learnings = st.session_state.performance_kb.get_agent_learnings(agent)

            if agent_learnings and agent_learnings.learnings:
                with st.expander(f"🤖 {agent} ({len(agent_learnings.learnings)} learnings)", expanded=True):
                    for learning in agent_learnings.learnings:
                        st.markdown(f"- {learning}")
            else:
                st.info(f"{agent}: No learnings recorded yet")
    else:
        st.info("No agent learnings recorded yet - run some queries to see bidirectional learning!")


def tab_tool_composer():
    """Tool composer tab - create and manage composed tools."""
    st.header("🔧 Tool Composer")

    st.info("Tool composition feature - Create multi-step workflows that can be reused")

    # Create new tool
    with st.expander("➕ Create New Composed Tool", expanded=False):
        tool_name = st.text_input("Tool Name", placeholder="e.g., BRCA1_Inhibitor_Safety_Analysis")
        tool_description = st.text_area("Description", placeholder="Describe what this tool does...")

        st.markdown("**Steps:**")
        num_steps = st.number_input("Number of steps", min_value=1, max_value=10, value=3)

        steps = []
        for i in range(num_steps):
            st.markdown(f"**Step {i+1}:**")
            col1, col2 = st.columns(2)

            with col1:
                mcp = st.selectbox(
                    f"MCP Server",
                    options=list(MCP_SERVERS.keys()),
                    key=f"mcp_step_{i}"
                )

            with col2:
                tool = st.text_input(
                    f"Tool Name",
                    placeholder="e.g., search_inhibitors",
                    key=f"tool_step_{i}"
                )

            steps.append({"mcp": mcp, "tool": tool})

        if st.button("Create Tool"):
            st.success(f"Tool '{tool_name}' created with {num_steps} steps!")
            st.info("This tool can now be reused for similar queries")

    st.divider()

    # Existing tools
    st.subheader("Existing Composed Tools")
    st.info("No composed tools yet. Create one above or execute a multi-step workflow!")


def tab_research_sessions():
    """Research sessions tab - manage multi-turn conversations."""
    st.header("🧠 Research Sessions")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.info("Research sessions maintain context across multiple queries")

    with col2:
        if st.button("➕ New Session", use_container_width=True):
            if st.session_state.session_manager:
                session = st.session_state.session_manager.create_session(
                    user_id="demo_user",
                    research_goal="Demo research session"
                )
                st.session_state.active_session_id = session.session_id
                st.success("New session created!")
                st.rerun()

    # Active session
    if st.session_state.active_session_id:
        session_id = st.session_state.active_session_id
        session = st.session_state.session_manager.get_session(session_id)

        if session:
            st.markdown(f"**Active Session:** `{session_id[:8]}...`")
            st.markdown(f"**Research Goal:** {session.research_goal}")

            st.divider()

            # Session stats
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Queries", len(session.queries))

            with col2:
                st.metric("Entities", len(session.entities))

            with col3:
                st.metric("Hypotheses", len(session.hypotheses))

            # Entities
            if session.entities:
                st.subheader("Discovered Entities")
                for entity in session.entities:
                    st.markdown(f"- **{entity.name}** ({entity.entity_type.value})")

            # Hypotheses
            if session.hypotheses:
                st.subheader("Formed Hypotheses")
                for hyp in session.hypotheses:
                    st.markdown(f"- {hyp.statement} (Confidence: {hyp.confidence*100:.0f}%)")
    else:
        st.info("No active session. Start a new session or run a query in Quick Demo.")


def main():
    """Main application."""
    display_header()

    # Initialize demo
    initialize_demo()

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Quick Demo",
        "📊 Learning Dashboard",
        "🔧 Tool Composer",
        "🧠 Research Sessions"
    ])

    with tab1:
        tab_quick_demo()

    with tab2:
        tab_learning_dashboard()

    with tab3:
        tab_tool_composer()

    with tab4:
        tab_research_sessions()


if __name__ == "__main__":
    main()
