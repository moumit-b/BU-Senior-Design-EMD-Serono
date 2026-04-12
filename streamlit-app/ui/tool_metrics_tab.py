"""
Tool Metrics Tab UI

Displays persistent tool call metrics: call counts, success rates,
and average latencies per agent-tool pair.
"""

import streamlit as st
import pandas as pd
from typing import Optional


def render_tool_metrics(db_manager) -> None:
    """Render the Tool Metrics tab content."""
    tracker = st.session_state.get("tool_tracker")

    if tracker is None:
        st.info("Tool metrics tracker is not yet initialized. Run a query to populate data.")
        return

    summary = tracker.get_summary()
    metrics = tracker.get_all_metrics()

    # --- Summary cards ---
    st.markdown("### Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Calls", summary["total_calls"])
    with c2:
        st.metric("Successful", summary["total_successes"])
    with c3:
        st.metric("Failed", summary["total_failures"])
    with c4:
        st.metric("Unique Tools", summary["unique_tools"])
    with c5:
        st.metric("Success Rate", f"{summary['overall_success_rate']}%")

    st.divider()

    if not metrics:
        st.info("No tool calls recorded yet. Run a research query to populate metrics.")
        return

    # --- Filters ---
    col_f1, col_f2 = st.columns(2)
    agents = sorted({m["agent_name"] for m in metrics})
    servers = sorted({m["mcp_server"] for m in metrics if m["mcp_server"] != "—"})

    with col_f1:
        selected_agent = st.selectbox(
            "Filter by Agent",
            options=["All Agents"] + agents,
            key="metrics_agent_filter",
        )
    with col_f2:
        selected_server = st.selectbox(
            "Filter by MCP Server",
            options=["All Servers"] + servers,
            key="metrics_server_filter",
        )

    filtered = metrics
    if selected_agent != "All Agents":
        filtered = [m for m in filtered if m["agent_name"] == selected_agent]
    if selected_server != "All Servers":
        filtered = [m for m in filtered if m["mcp_server"] == selected_server]

    if not filtered:
        st.info("No results match the selected filters.")
        return

    # --- Table ---
    st.markdown("### Tool Call Detail")
    df = pd.DataFrame(filtered, columns=[
        "tool_name", "agent_name", "mcp_server",
        "call_count", "success_count", "failure_count",
        "success_rate", "avg_latency_ms", "last_called_at",
    ])
    df.columns = [
        "Tool", "Agent", "MCP Server",
        "Calls", "Successes", "Failures",
        "Success Rate (%)", "Avg Latency (ms)", "Last Called",
    ]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Success Rate (%)": st.column_config.ProgressColumn(
                "Success Rate (%)",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
            "Calls": st.column_config.NumberColumn("Calls", format="%d"),
            "Avg Latency (ms)": st.column_config.NumberColumn("Avg Latency (ms)", format="%.0f ms"),
        },
    )

    # --- Per-agent breakdown ---
    if selected_agent == "All Agents" and len(agents) > 1:
        st.divider()
        st.markdown("### Calls per Agent")
        agent_totals = {}
        for m in metrics:
            a = m["agent_name"]
            agent_totals[a] = agent_totals.get(a, 0) + m["call_count"]
        agent_df = pd.DataFrame(
            sorted(agent_totals.items(), key=lambda x: x[1], reverse=True),
            columns=["Agent", "Total Calls"],
        )
        st.bar_chart(agent_df.set_index("Agent"))
