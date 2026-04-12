"""
Governance Tab UI

Displays Context Forge Gateway stats, service health, compliance violations,
audit logs, and rate limiting information.
"""

import streamlit as st


def render_governance_tab(gateway=None) -> None:
    """Render the Governance tab content."""
    from governance import ContextForgeGateway

    if gateway is None:
        gateway = ContextForgeGateway()
        st.session_state["gateway"] = gateway

    st.markdown("### Context Forge Governance")
    st.markdown(
        "Live telemetry from the **Context Forge Gateway** governing all MCP tool calls."
    )

    # --- Top-level metrics ---
    stats = gateway.get_gateway_stats()
    total = stats.get("total_calls", 0)
    successful = stats.get("successful_calls", 0)
    success_rate = round(successful / total * 100, 1) if total > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Calls", total)
    with c2:
        st.metric("Successful", successful)
    with c3:
        st.metric("Success Rate", f"{success_rate}%")
    with c4:
        st.metric("Compliance Blocks", stats.get("compliance_blocks", 0))

    st.divider()

    # --- Service Health ---
    st.markdown("#### Service Health")
    health_status = gateway.get_health_status()
    if health_status:
        for server, info in health_status.items():
            hcol1, hcol2, hcol3 = st.columns([3, 1, 1])
            with hcol1:
                st.text(server)
            with hcol2:
                st.text(f"{info.get('tool_count', 0)} tools")
            with hcol3:
                if info.get("healthy", False):
                    st.success("Healthy", icon="✅")
                else:
                    st.error("Unhealthy", icon="❌")
    else:
        st.info("No MCP servers registered. Initialize the agent to connect servers.")

    st.divider()

    # --- Compliance Violations ---
    st.markdown("#### Compliance Violations")
    violations = gateway.compliance_engine.get_violations(limit=20)
    if violations:
        for v in reversed(violations):
            st.warning(
                f"**[{v['stage'].upper()}]** {v['timestamp']} — "
                f"`{v['server']}/{v['tool']}`: {v['reason']}"
            )
    else:
        st.success("No compliance violations recorded.", icon="✅")

    st.divider()

    # --- Recent Audit Logs ---
    st.markdown("#### Recent Audit Logs")
    recent_logs = gateway.audit_logger.get_recent_logs(limit=30)
    if recent_logs:
        for log in recent_logs:
            status_icon = "✅" if log.get("result_status") == "success" else "❌"
            exec_time = log.get("execution_time")
            time_str = f" ({exec_time:.2f}s)" if exec_time else ""
            st.markdown(
                f"{status_icon} `{log.get('timestamp', '')}` — "
                f"**{log.get('actor', '')}** called "
                f"`{log.get('mcp_server', '')}.{log.get('tool_name', '')}` "
                f"→ {log.get('result_status', 'unknown')}{time_str}"
            )
    else:
        st.info("No audit logs yet. Run queries to generate governance data.")

    st.divider()

    # --- Rate Limiting ---
    st.markdown("#### Rate Limiting")
    usage = gateway.rate_limiter.get_usage_stats("admin")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Requests (last hour)", usage.get("total_requests", 0))
    with r2:
        st.metric("Limit", usage.get("limit", 100))
    with r3:
        st.metric("Remaining", usage.get("remaining", 100))
