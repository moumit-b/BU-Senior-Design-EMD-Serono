"""
Governance Dashboard Page

Displays audit logs, compliance status, service health, and gateway statistics.
Reads the gateway instance from Streamlit session state (shared with the
Dual Orchestration Lab).
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from governance import ContextForgeGateway

st.set_page_config(page_title="Governance Dashboard", page_icon="🛡️", layout="wide")

st.title("🛡️ Governance Dashboard — Context Forge")

st.markdown(
    "Live view of the **IBM Context Forge Gateway** governing all MCP tool calls."
)

# ---------------------------------------------------------------------------
# Obtain gateway — prefer the one already in session (from Dual Orchestration
# Lab), otherwise create a standalone instance for dashboard viewing.
# ---------------------------------------------------------------------------
gateway: ContextForgeGateway = st.session_state.get("gateway")
if gateway is None:
    gateway = ContextForgeGateway()
    st.session_state.gateway = gateway
    st.info("No active gateway session — showing empty dashboard. Connect via the Dual Orchestration Lab to see live data.")

# ---------------------------------------------------------------------------
# Top-level metrics
# ---------------------------------------------------------------------------
stats = gateway.get_gateway_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Calls", stats.get("total_calls", 0))
with col2:
    st.metric("Successful", stats.get("successful_calls", 0))
with col3:
    rate = 0
    total = stats.get("total_calls", 0)
    if total > 0:
        rate = round(stats.get("successful_calls", 0) / total * 100, 1)
    st.metric("Success Rate", f"{rate}%")
with col4:
    st.metric("Compliance Blocks", stats.get("compliance_blocks", 0))

st.divider()

# ---------------------------------------------------------------------------
# Service Health
# ---------------------------------------------------------------------------
st.header("Service Health")

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
                st.success("Healthy")
            else:
                st.error("Unhealthy")
else:
    st.info("No MCP servers registered. Connect to MCPs in the Dual Orchestration Lab.")

st.divider()

# ---------------------------------------------------------------------------
# Compliance Violations
# ---------------------------------------------------------------------------
st.header("Compliance Violations")

violations = gateway.compliance_engine.get_violations(limit=20)
if violations:
    for v in reversed(violations):
        st.warning(
            f"**[{v['stage'].upper()}]** {v['timestamp']} — "
            f"`{v['server']}/{v['tool']}`: {v['reason']}"
        )
else:
    st.success("No compliance violations recorded.")

st.divider()

# ---------------------------------------------------------------------------
# Recent Audit Logs
# ---------------------------------------------------------------------------
st.header("Recent Audit Logs")

recent_logs = gateway.audit_logger.get_recent_logs(limit=30)
if recent_logs:
    for log in recent_logs:
        status_icon = "✅" if log.get("result_status") == "success" else "❌"
        exec_time = log.get("execution_time")
        time_str = f" ({exec_time:.2f}s)" if exec_time else ""
        st.markdown(
            f"{status_icon} `{log.get('timestamp', '')}` — "
            f"**{log.get('actor', '')}** called `{log.get('mcp_server', '')}.{log.get('tool_name', '')}` "
            f"→ {log.get('result_status', 'unknown')}{time_str}"
        )
else:
    st.info("No audit logs yet. Run queries in the Dual Orchestration Lab to generate audit data.")

st.divider()

# ---------------------------------------------------------------------------
# Rate Limiting Stats
# ---------------------------------------------------------------------------
st.header("Rate Limiting")
usage = gateway.rate_limiter.get_usage_stats("demo_user")
r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Requests (last hour)", usage.get("total_requests", 0))
with r2:
    st.metric("Limit", usage.get("limit", 100))
with r3:
    st.metric("Remaining", usage.get("remaining", 100))