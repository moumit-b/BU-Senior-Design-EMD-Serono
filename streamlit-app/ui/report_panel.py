"""
Report Panel UI Component

Renders the report generation panel on the right side of the app.
Analyzes conversation history to identify drugs/targets and generates
structured reports using the EMD report format.
"""

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
        agent: The initialized MCPAgent instance (used for its LLM).
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
        # Clear cached drug when chat is empty
        st.session_state.pop("identified_drug", None)
        st.session_state.pop("drug_msg_count", None)
        return None

    # Only re-extract if conversation length changed
    msg_count = len(messages)
    if (
        "identified_drug" in st.session_state
        and st.session_state.get("drug_msg_count") == msg_count
    ):
        return st.session_state.identified_drug

    # Run extraction
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


def _generate_and_display_report(
    agent, messages: List[Dict[str, Any]], drug_name: str, report_type: str
) -> None:
    """Generate the report and store it in session state."""
    with st.spinner("Generating report... This may take a minute."):
        from reporting.chat_report_generator import generate_report_from_chat

        config_data = getattr(agent, "config_data", None)
        report_md = generate_report_from_chat(
            messages=messages,
            drug_name=drug_name,
            report_type=report_type,
            config_data=config_data,
        )
        st.session_state.generated_report = report_md

    st.rerun()


def _display_report(report_md: str, drug_name: str) -> None:
    """Display the generated report with download options."""
    st.divider()

    # Build a descriptive download filename
    safe_name = drug_name.replace(" ", "_").replace("/", "-")
    today = datetime.date.today().isoformat()
    filename = f"CI_Report_{safe_name}_{today}.md"

    # Download and clear buttons
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

    # Render the report
    with st.container(height=600):
        st.markdown(report_md)
