"""
Report Panel UI Component

Renders the report generation panel.
Saves generated reports to the database and injects prior context
(past reports + semantically related chat history) into the ReportAgent.
"""

import asyncio
import datetime
import logging
import time
import streamlit as st
from typing import List, Dict, Any, Optional


logger = logging.getLogger(__name__)

REPORT_TYPES = {
    "competitive_intelligence": "Competitive Intelligence Report",
    # Future types:
    # "target_cv": "Target CV Report",
    # "clinical_summary": "Clinical Summary Report",
    # "biomarker_landscape": "Biomarker Landscape Report",
}


def render_report_panel(agent, db_manager=None, vector_store=None) -> None:
    """Render the report generation panel."""
    messages = st.session_state.get("messages", [])
    drug_name = _get_identified_drug(messages, agent)

    chat_session_id = st.session_state.get("current_chat_session_id")

    if drug_name is None:
        st.info(
            "**No subject identified.**\n\n"
            "Begin a conversation about a drug, compound, or biological target "
            "and the system will detect it automatically."
        )
        st.markdown("### Past Reports")
        _render_past_reports(db_manager, chat_session_id=chat_session_id)
        return

    st.success(f"**Research subject:** {drug_name}")

    selected_type = st.selectbox(
        "Report Type",
        options=list(REPORT_TYPES.keys()),
        format_func=lambda k: REPORT_TYPES[k],
        key="report_type_selector",
    )

    if st.button("Generate Report", type="primary", use_container_width=True):
        _generate_and_display_report(
            agent, messages, drug_name, selected_type,
            db_manager=db_manager, vector_store=vector_store,
        )

    if "generated_report" in st.session_state and st.session_state.generated_report:
        _display_report(st.session_state.generated_report, drug_name)

    st.divider()
    _render_past_reports(db_manager, chat_session_id=chat_session_id, drug_name=drug_name)
    _render_dev_log()


# ---------------------------------------------------------------------------
# Drug detection
# ---------------------------------------------------------------------------

def _get_identified_drug(messages: List[Dict[str, Any]], agent) -> Optional[str]:
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

    previous_drug = st.session_state.get("identified_drug")
    if previous_drug is not None and drug != previous_drug:
        st.session_state.pop("generated_report", None)

    st.session_state.identified_drug = drug
    st.session_state.drug_msg_count = msg_count
    return drug


# ---------------------------------------------------------------------------
# Context assembly (current + prior)
# ---------------------------------------------------------------------------

def _build_conversation_context(messages: List[Dict[str, Any]], max_chars: int = 8000) -> str:
    """Condense messages into a transcript."""
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


def _retrieve_prior_reports_context(db_manager, drug_name: str) -> str:
    """
    Fetch previous reports on the same drug from the database.
    Returns a condensed summary for injection into the ReportAgent.
    """
    if db_manager is None:
        return ""
    try:
        from context.db_models import ReportRecord
        with db_manager.get_session() as session:
            records = (
                session.query(ReportRecord)
                .filter(ReportRecord.drug_name.ilike(f"%{drug_name}%"))
                .order_by(ReportRecord.created_at.desc())
                .limit(3)
                .all()
            )
            if not records:
                return ""
            parts = []
            for r in records:
                date_str = r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown date"
                # Include first 3000 chars of prior report as context
                parts.append(
                    f"--- Prior report ({date_str}) ---\n{r.content_md[:3000]}\n"
                )
            return "\n".join(parts)
    except Exception as e:
        logger.warning(f"_retrieve_prior_reports_context error: {e}")
        return ""


def _retrieve_related_chat_context(vector_store, drug_name: str) -> str:
    """
    Semantic search over all chat history for exchanges about this drug.
    Returns a condensed string of the most relevant past conversations.
    """
    if vector_store is None:
        return ""
    try:
        results = vector_store.search_chat_contexts(drug_name, n_results=8)
        if not results:
            return ""
        parts = [r["content_text"] for r in results]
        combined = "\n---\n".join(parts)
        # Cap to avoid exceeding prompt limits
        return combined[:4000]
    except Exception as e:
        logger.warning(f"_retrieve_related_chat_context error: {e}")
        return ""


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _generate_and_display_report(
    agent,
    messages: List[Dict[str, Any]],
    drug_name: str,
    report_type: str,
    db_manager=None,
    vector_store=None,
) -> None:
    """Instantiate the ReportAgent and generate the report."""
    st.session_state["report_dev_log"] = []
    st.session_state.pop("hallucination_check", None)

    def log(msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        st.session_state.setdefault("report_dev_log", []).append(entry)
        logger.info(msg)

    with st.spinner("Generating report — this may take several minutes…"):
        from agents.report_agent import ReportAgent
        from agents.base_agent import AgentTask, AgentContext

        config_data = getattr(agent, "config_data", None)
        mcp_orchestrator = st.session_state.get("mcp_orchestrator")
        tool_tracker = st.session_state.get("tool_tracker")

        log(f"MCPOrchestrator: {'active' if mcp_orchestrator else 'None (LLM-only mode)'}")

        report_agent = ReportAgent(
            mcp_orchestrator=mcp_orchestrator,
            llm=None,
            config_data=config_data,
            tool_tracker=tool_tracker,
        )
        log(f"ReportAgent created with {len(report_agent._agents)} specialized agents")

        # Assemble context: current chat + prior reports + related past chats
        conversation_context = _build_conversation_context(messages)

        log("Retrieving prior reports for this drug…")
        prior_reports_context = _retrieve_prior_reports_context(db_manager, drug_name)
        if prior_reports_context:
            log(f"Found prior report context ({len(prior_reports_context)} chars)")

        log("Searching related chat history via vector store…")
        related_chat_history = _retrieve_related_chat_context(vector_store, drug_name)
        if related_chat_history:
            log(f"Found related chat history ({len(related_chat_history)} chars)")

        user_id = st.session_state.get("user_id", "streamlit_user")
        chat_session_id = st.session_state.get("current_chat_session_id", "streamlit_session")

        task = AgentTask(
            task_id=f"report_{int(time.time())}",
            query=f"Generate {report_type} report for {drug_name}",
            task_type="report_generation",
            parameters={
                "drug_name": drug_name,
                "report_type": report_type,
                "conversation_context": conversation_context,
                "prior_reports_context": prior_reports_context,
                "related_chat_history": related_chat_history,
            },
        )

        context = AgentContext(
            session_id=chat_session_id,
            user_id=user_id,
            research_goal=f"Competitive intelligence research on {drug_name}",
        )

        log(f"Starting report generation for '{drug_name}' ({report_type})")
        gen_start = time.time()

        try:
            try:
                asyncio.get_running_loop()
                running = True
            except RuntimeError:
                running = False

            if running:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, report_agent.process(task, context))
                    result = future.result(timeout=600)
            else:
                result = asyncio.run(report_agent.process(task, context))

        except Exception as exc:
            log(f"EXCEPTION: {type(exc).__name__}: {exc}")
            result = None

        elapsed = time.time() - gen_start

        if result and result.success:
            report_md = result.result_data.get("report", "")
            st.session_state.generated_report = report_md
            log(f"Report generated in {elapsed:.1f}s")
            log(f"MCPs used: {result.mcps_used}")

            # Save report to database
            if db_manager and report_md:
                _save_report_to_db(db_manager, chat_session_id, user_id, drug_name, report_type, report_md)
                log("Report saved to database")
        elif result:
            st.session_state.generated_report = (
                f"# Report Generation Failed\n\n**Error:** {result.error_message}\n\n"
                f"Please check your LLM configuration and try again."
            )
            log(f"Report failed after {elapsed:.1f}s: {result.error_message}")
        else:
            st.session_state.generated_report = (
                "# Report Generation Failed\n\n"
                "**Error:** Report generation timed out or crashed.\n\n"
                "Check the Dev Log for details."
            )
            log(f"No result after {elapsed:.1f}s")

    st.rerun()


def _save_report_to_db(db_manager, chat_session_id, user_id, drug_name, report_type, content_md):
    """Save the generated report to the reports table."""
    try:
        from context.db_models import ReportRecord
        with db_manager.get_session() as session:
            record = ReportRecord(
                chat_session_id=chat_session_id,
                user_id=user_id,
                drug_name=drug_name,
                report_type=report_type,
                content_md=content_md,
                created_at=datetime.datetime.now(),
            )
            session.add(record)
    except Exception as e:
        logger.warning(f"_save_report_to_db error: {e}")


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def _display_report(report_md: str, drug_name: str) -> None:
    """Display the generated report with download options."""
    from reporting.exporters.pdf_exporter import PDFExporter
    safe_name = drug_name.replace(" ", "_").replace("/", "-")
    today = datetime.date.today().isoformat()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            label="Download (.md)",
            data=report_md,
            file_name=f"CI_Report_{safe_name}_{today}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        try:
            pdf_bytes = PDFExporter().export({"markdown": report_md})
            st.download_button(
                label="Download (.pdf)",
                data=pdf_bytes,
                file_name=f"CI_Report_{safe_name}_{today}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"PDF unavailable: {e}")
    with col3:
        if st.button("Verify Identifiers", use_container_width=True):
            with st.spinner("Verifying NCT numbers, PMIDs, and DOIs…"):
                from ml.hallucination_checker import verify_report as _verify
                st.session_state["hallucination_check"] = _verify(report_md)
            st.rerun()
    with col4:
        if st.button("Clear Report", use_container_width=True):
            st.session_state.generated_report = None
            st.session_state.pop("report_dev_log", None)
            st.session_state.pop("hallucination_check", None)
            st.rerun()

    _render_verification_results()

    with st.container(height=600):
        st.markdown(report_md)


def _render_verification_results() -> None:
    """Display identifier verification results below the report action buttons."""
    results = st.session_state.get("hallucination_check")
    if results is None:
        return

    if not results:
        st.info("No verifiable identifiers (NCT numbers, PMIDs, DOIs) found in this report.")
        return

    valid   = {k: v for k, v in results.items() if v["valid"]}
    invalid = {k: v for k, v in results.items() if not v["valid"]}

    label = (
        f"Identifier Verification — "
        f"{len(valid)} verified ✓  |  {len(invalid)} failed ✗"
    )
    with st.expander(label, expanded=len(invalid) > 0):
        if invalid:
            st.error(f"{len(invalid)} identifier(s) could not be verified — possible hallucination:")
            for id_val, r in invalid.items():
                st.markdown(f"- `{id_val}` ({r['type'].upper()}) — {r['details']}")
        if valid:
            st.success(f"{len(valid)} identifier(s) confirmed real:")
            for id_val, r in valid.items():
                st.markdown(f"- `{id_val}` ({r['type'].upper()}) — {r['details']}")


def _render_past_reports(db_manager, chat_session_id: Optional[str] = None, drug_name: Optional[str] = None) -> None:
    """Show a list of previously generated reports from the database."""
    if db_manager is None:
        return
    try:
        from context.db_models import ReportRecord
        from reporting.exporters.pdf_exporter import PDFExporter
        with db_manager.get_session() as session:
            base = session.query(ReportRecord)
            if chat_session_id:
                base = base.filter(ReportRecord.chat_session_id == chat_session_id)
            if drug_name:
                q = base.filter(
                    ReportRecord.drug_name.ilike(f"%{drug_name}%")
                ).order_by(ReportRecord.created_at.desc()).limit(10)
            else:
                q = base.order_by(ReportRecord.created_at.desc()).limit(20)
            # Materialize into plain dicts before session closes to avoid DetachedInstanceError
            records = [
                {
                    "report_id": r.report_id,
                    "drug_name": r.drug_name,
                    "report_type": r.report_type,
                    "content_md": r.content_md,
                    "created_at": r.created_at,
                }
                for r in q.all()
            ]

        if not records:
            return

        label = f"Past Reports — {drug_name}" if drug_name else "Past Reports"
        with st.expander(label, expanded=True):
            for r in records:
                date_str = r["created_at"].strftime("%Y-%m-%d %H:%M") if r["created_at"] else "unknown"
                col_info, col_view, col_md, col_pdf = st.columns([3, 1, 1, 1])
                with col_info:
                    st.markdown(f"**{r['drug_name']}** · {REPORT_TYPES.get(r['report_type'], r['report_type'])} · {date_str}")
                with col_view:
                    if st.button("View", key=f"view_{r['report_id']}"):
                        st.session_state.generated_report = r["content_md"]
                        st.session_state.identified_drug = r["drug_name"]
                        st.rerun()
                with col_md:
                    safe = r["drug_name"].replace(" ", "_")
                    date_sfx = r["created_at"].strftime("%Y%m%d") if r["created_at"] else "report"
                    st.download_button(
                        ".md",
                        data=r["content_md"],
                        file_name=f"CI_{safe}_{date_sfx}.md",
                        mime="text/markdown",
                        key=f"dl_md_{r['report_id']}",
                    )
                with col_pdf:
                    try:
                        pdf_bytes = PDFExporter().export({"markdown": r["content_md"]})
                        st.download_button(
                            ".pdf",
                            data=pdf_bytes,
                            file_name=f"CI_{safe}_{date_sfx}.pdf",
                            mime="application/pdf",
                            key=f"dl_pdf_{r['report_id']}",
                        )
                    except Exception:
                        st.caption("—")
    except Exception as e:
        logger.warning(f"_render_past_reports error: {e}")


def _render_dev_log() -> None:
    log_entries = st.session_state.get("report_dev_log", [])
    if not log_entries:
        return
    with st.expander("Generation Log", expanded=False):
        for entry in log_entries:
            st.text(entry)
        mcp_orchestrator = st.session_state.get("mcp_orchestrator")
        if mcp_orchestrator:
            st.markdown("---")
            st.markdown("**MCP Health:**")
            for server, healthy in mcp_orchestrator.health_status.items():
                st.text(f"  {server}: {'OK' if healthy else 'DOWN'}")
