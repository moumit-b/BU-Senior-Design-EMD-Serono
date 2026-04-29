"""
Governance Tab UI

Displays Context Forge Gateway stats, service health, compliance violations,
audit logs, and rate limiting information.
"""

import streamlit as st
import theme as _theme


def render_governance_tab(gateway=None) -> None:
    """Render the Governance tab content."""
    from governance import ContextForgeGateway

    if gateway is None:
        gateway = ContextForgeGateway()
        st.session_state["gateway"] = gateway

    p = _theme._PALETTES.get(st.session_state.get("theme", "dark"), _theme.DARK)

    st.markdown(
        f"<h3 style='font-size:1rem;font-weight:600;color:{p.text_secondary};"
        f"letter-spacing:0.04em;margin-bottom:0.2rem'>Context Forge Governance</h3>"
        f"<p style='font-size:0.82rem;color:{p.text_muted};margin-bottom:1rem'>"
        f"Live telemetry from the Context Forge Gateway governing all MCP tool calls.</p>",
        unsafe_allow_html=True,
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

    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # --- Service Health ---
    st.markdown(
        f"<h4 style='font-size:0.88rem;font-weight:600;color:{p.text_secondary};"
        f"letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.7rem'>"
        f"Service Health</h4>",
        unsafe_allow_html=True,
    )
    health_status = gateway.get_health_status()
    if health_status:
        for server, info in health_status.items():
            healthy = info.get("healthy", False)
            dot_cls = "ok" if healthy else "err"
            status_text = "Healthy" if healthy else "Unhealthy"
            card_cls = "healthy" if healthy else "unhealthy"
            st.markdown(
                f"<div class='health-card {card_cls}'>"
                f"<span class='health-dot {dot_cls}'></span>"
                f"<div style='flex:1'>"
                f"<span style='font-weight:600;font-size:0.88rem;color:{p.text_primary}'>{server}</span>"
                f"<span style='font-size:0.75rem;color:{p.text_muted};margin-left:0.5rem'>"
                f"· {info.get('tool_count', 0)} tools</span>"
                f"</div>"
                f"<span style='font-size:0.78rem;font-weight:600;"
                f"color:{p.success if healthy else p.error}'>{status_text}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No MCP servers registered. Initialize the agent to connect servers.")

    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # --- Compliance Violations ---
    st.markdown(
        f"<h4 style='font-size:0.88rem;font-weight:600;color:{p.text_secondary};"
        f"letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.7rem'>"
        f"Compliance Violations</h4>",
        unsafe_allow_html=True,
    )
    violations = gateway.compliance_engine.get_violations(limit=20)
    if violations:
        for v in reversed(violations):
            st.markdown(
                f"<div style='background:{p.error}18;border:1px solid {p.error}44;"
                f"border-left:3px solid {p.error};border-radius:6px;"
                f"padding:0.6rem 0.9rem;margin:0.3rem 0;font-size:0.82rem'>"
                f"<strong style='color:{p.error}'>[{v['stage'].upper()}]</strong> "
                f"<span style='color:{p.text_muted}'>{v['timestamp']}</span> — "
                f"<code style='font-size:0.78rem'>{v['server']}/{v['tool']}</code>: "
                f"{v['reason']}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f"<div class='health-card healthy'>"
            f"<span class='health-dot ok'></span>"
            f"<span style='font-size:0.85rem;color:{p.success}'>No compliance violations recorded</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # --- Recent Audit Logs ---
    st.markdown(
        f"<h4 style='font-size:0.88rem;font-weight:600;color:{p.text_secondary};"
        f"letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.7rem'>"
        f"Recent Audit Logs</h4>",
        unsafe_allow_html=True,
    )
    recent_logs = gateway.audit_logger.get_recent_logs(limit=30)
    if recent_logs:
        st.markdown("<div class='timeline'>", unsafe_allow_html=True)
        for log in recent_logs:
            is_ok = log.get("result_status") == "success"
            dot_cls = "ok" if is_ok else "err"
            exec_time = log.get("execution_time")
            time_str = f" · {exec_time:.2f}s" if exec_time else ""
            actor = log.get("actor", "")
            server = log.get("mcp_server", "")
            tool = log.get("tool_name", "")
            ts = log.get("timestamp", "")
            status = log.get("result_status", "unknown")
            status_color = p.success if is_ok else p.error
            st.markdown(
                f"<div class='timeline-item'>"
                f"<span class='timeline-dot {dot_cls}'></span>"
                f"<span style='color:{p.text_muted};font-size:0.75rem'>{ts}</span> — "
                f"<strong style='color:{p.text_primary}'>{actor}</strong> called "
                f"<code style='font-size:0.78rem'>{server}.{tool}</code> "
                f"→ <span style='color:{status_color};font-weight:600'>{status}</span>"
                f"<span style='color:{p.text_muted}'>{time_str}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No audit logs yet. Run queries to generate governance data.")

    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # --- Rate Limiting ---
    st.markdown(
        f"<h4 style='font-size:0.88rem;font-weight:600;color:{p.text_secondary};"
        f"letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.7rem'>"
        f"Rate Limiting</h4>",
        unsafe_allow_html=True,
    )
    usage = gateway.rate_limiter.get_usage_stats("admin")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Requests (last hour)", usage.get("total_requests", 0))
    with r2:
        st.metric("Limit", usage.get("limit", 100))
    with r3:
        st.metric("Remaining", usage.get("remaining", 100))
