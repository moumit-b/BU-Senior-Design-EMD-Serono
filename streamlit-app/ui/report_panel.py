"""
Report Panel UI Component

Renders the report generation panel on the right side of the app.
Analyzes conversation history to identify drugs/targets and generates
structured reports via the dedicated ReportAgent.
"""

import asyncio
import datetime
import streamlit as st
from typing import List, Dict, Any, Optional


# Report type registry — start with Competitive Intelligence, more to come
REPORT_TYPES = {
    "competitive_intelligence": "Competitive Intelligence Report",
    # Future report types will be added here:
    # "target_cv": "Target CV Report",
    # "clinical_summary": "Clinical Summary Report",
    # "biomarker_landscape": "Biomarker Landscape Report",
}


def render_report_panel(agent) -> None:
    """Render the report generation panel.

    Args:
        agent: The initialized MCPAgent instance (used for its LLM and config).
    """
    st.header("Report Generation")

    messages = st.session_state.get("messages", [])

    # --- Drug detection ---
    drug_name = _get_identified_drug(messages, agent)

    if drug_name is None:
        st.info(
            "**No drug identified.**\n\n"
            "Start a conversation about a specific drug, compound, or "
            "biological target in the chat, and the system will "
            "automatically detect it here."
        )
        return

    st.success(f"**Identified subject:** {drug_name}")

    # --- Report type selector ---
    selected_type = st.selectbox(
        "Report Type",
        options=list(REPORT_TYPES.keys()),
        format_func=lambda k: REPORT_TYPES[k],
        key="report_type_selector",
    )

    # --- Generate button ---
    if st.button("Generate Report", type="primary", use_container_width=True):
        _generate_and_display_report(agent, messages, drug_name, selected_type)

    # --- Display previously generated report if it exists ---
    if "generated_report" in st.session_state and st.session_state.generated_report:
        _display_report(st.session_state.generated_report, drug_name)


def _get_identified_drug(
    messages: List[Dict[str, Any]], agent
) -> Optional[str]:
    """Identify the drug from conversation, caching the result.

    Re-runs extraction only when the conversation changes.
    """
    if not messages:
        st.session_state.pop("identified_drug", None)
        st.session_state.pop("drug_msg_count", None)
        return None

    msg_count = len(messages)
    if (
        "identified_drug" in st.session_state
        and st.session_state.get("drug_msg_count") == msg_count
    ):
        return st.session_state.identified_drug

    from reporting.drug_extractor import extract_drug_from_conversation

    llm = getattr(agent, "llm", None)
    drug = extract_drug_from_conversation(messages, llm=llm)

    # Clear stale report if the identified drug has changed
    previous_drug = st.session_state.get("identified_drug")
    if previous_drug is not None and drug != previous_drug:
        st.session_state.pop("generated_report", None)

    st.session_state.identified_drug = drug
    st.session_state.drug_msg_count = msg_count
    return drug


def _build_conversation_context(messages: List[Dict[str, Any]], max_chars: int = 8000) -> str:
    """Condense messages into a transcript for the ReportAgent."""
    parts = []
    total = 0
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        line = f"{role}: {content}"
        if total + len(line) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                parts.append(line[:remaining] + "...")
            break
        parts.append(line)
        total += len(line)
    return "\n".join(parts)


def _generate_and_display_report(
    agent, messages: List[Dict[str, Any]], drug_name: str, report_type: str
) -> None:
    """Instantiate the ReportAgent and generate the report."""
    with st.spinner("ReportAgent is researching and generating the report... This may take a few minutes."):
        from agents.report_agent import ReportAgent
        from agents.base_agent import AgentTask, AgentContext
        import time

        config_data = getattr(agent, "config_data", None)

        # Create the ReportAgent with the user's current LLM configuration
        report_agent = ReportAgent(
            mcp_orchestrator=None,
            llm=None,
            config_data=config_data,
        )

        # Build the task
        conversation_context = _build_conversation_context(messages)
        task = AgentTask(
            task_id=f"report_{int(time.time())}",
            query=f"Generate {report_type} report for {drug_name}",
            task_type="report_generation",
            parameters={
                "drug_name": drug_name,
                "report_type": report_type,
                "conversation_context": conversation_context,
            },
        )

        context = AgentContext(
            session_id="streamlit_session",
            user_id="streamlit_user",
            research_goal=f"Competitive intelligence research on {drug_name}",
        )

        # Run the async agent in a sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Inside an already-running loop (common in Streamlit)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, report_agent.process(task, context)).result()
            else:
                result = loop.run_until_complete(report_agent.process(task, context))
        except RuntimeError:
            result = asyncio.run(report_agent.process(task, context))

        if result.success:
            st.session_state.generated_report = result.result_data.get("report", "")
        else:
            st.session_state.generated_report = (
                f"# Report Generation Failed\n\n"
                f"**Error:** {result.error_message}\n\n"
                f"Please check your LLM configuration and try again."
            )

    st.rerun()


def _display_report(report_md: str, drug_name: str) -> None:
    """Display the generated report with download options."""
    st.divider()

    safe_name = drug_name.replace(" ", "_").replace("/", "-")
    today = datetime.date.today().isoformat()
    filename = f"CI_Report_{safe_name}_{today}.md"

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download (.md)",
            data=report_md,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        if st.button("Clear Report", use_container_width=True):
            st.session_state.generated_report = None
            st.rerun()

    with st.container(height=600):
        st.markdown(report_md)
