"""
Report Agent

Dedicated agent for generating structured pharmaceutical research reports.
Extends BaseAgent so it can be used by any application via the standard
agent interface: ReportAgent.process(task, context) -> AgentResult.

The agent owns the full report lifecycle:
1. Loads the EMD report format template
2. Breaks it into section-level research tasks
3. Uses the LLM to research and populate each section
4. Compiles all sections into the final EMD-structured report

Currently supports:
- Competitive Intelligence Report

The report type and drug/target are passed via AgentTask.parameters.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


# ---------------------------------------------------------------------------
# EMD format template (loaded once, cached at module level)
# ---------------------------------------------------------------------------

_EMD_FORMAT_CACHE: Optional[str] = None


def _load_emd_format() -> str:
    global _EMD_FORMAT_CACHE
    if _EMD_FORMAT_CACHE is not None:
        return _EMD_FORMAT_CACHE

    fmt_path = Path(__file__).resolve().parent.parent / "docs" / "EMD_report_format.md"
    if fmt_path.exists():
        _EMD_FORMAT_CACHE = fmt_path.read_text(encoding="utf-8")
    else:
        _EMD_FORMAT_CACHE = ""
    return _EMD_FORMAT_CACHE


# ---------------------------------------------------------------------------
# Section definitions for Competitive Intelligence reports
# ---------------------------------------------------------------------------

# Each section maps to a focused research prompt.  Core CI sections get
# thorough treatment; non-core sections get a brief summary.

CI_CORE_SECTIONS = [
    {
        "id": "1",
        "title": "Executive Summary and 6R Framework Alignment",
        "research_prompt": (
            "Provide an executive summary and 6R framework assessment "
            "(Right Target, Right Tissue, Right Safety, Right Feasibility, "
            "Right Patient, Right Commercial) for {drug_name}. "
            "Include strategic fit and biological rationale."
        ),
    },
    {
        "id": "2",
        "title": "General Target and Biomarker Information",
        "research_prompt": (
            "Provide comprehensive target and biomarker information for {drug_name}: "
            "target name, synonyms, biochemical class, function, molecular function / "
            "mode of action, subcellular location, gene ID, protein ID, protein family, "
            "drug targets, known ligands, and interacting proteins."
        ),
    },
    {
        "id": "9",
        "title": "Competitive Landscape",
        "research_prompt": (
            "Provide an exhaustive competitive landscape analysis for {drug_name}. "
            "Cover all four tiers: Tier 1 (direct competitors — same indication, "
            "similar mechanism), Tier 2 (adjacent — same indication different mechanism "
            "or same target different indication), Tier 3 (platform competitors), "
            "Tier 4 (emerging players and disruptors). "
            "Include a drug/asset landscape table (asset, company, development stage, "
            "target/MOA, biomarker strategy, indication, region, differentiation notes). "
            "Include a clinical trial landscape table (trial/NCT, sponsor, phase, "
            "indication, biomarker use, platform/assay, enrollment, status). "
            "Include a patent landscape snapshot. "
            "Cite specific companies, NCT numbers, and mechanisms."
        ),
    },
    {
        "id": "8",
        "title": "Regulatory and Commercial Overview",
        "research_prompt": (
            "Provide the regulatory and commercial overview for {drug_name}: "
            "approval status by country/region, regulatory class, validation stage, "
            "performance metrics (sensitivity, specificity, turnaround, cost), "
            "commercial overview (market share, reimbursement), and guideline "
            "landscape (NCCN, ASCO/CAP, region-specific)."
        ),
    },
    {
        "id": "11",
        "title": "Target Landscape and Development Trends",
        "research_prompt": (
            "Provide the target landscape and development trends for {drug_name}: "
            "overview of diseases amenable to the mechanism, competitor situation "
            "on-target and on-pathway, drug development data table (drug name, "
            "originator, current developer, highest status, target, MOA, indication, "
            "modality, pathway), clinical trials data table, and development trends "
            "(modality trends, biomarker strategy evolution, combination opportunities)."
        ),
    },
    {
        "id": "17",
        "title": "Risks, Gaps, and Recommended Next Steps",
        "research_prompt": (
            "Identify evidence gaps, key risks (scientific, translational, regulatory, "
            "commercial), and recommended next steps for {drug_name}. "
            "Include specific actionable recommendations for assays, competitive "
            "intelligence follow-up, vendor outreach, experiments, and patent review."
        ),
    },
]

CI_BRIEF_SECTIONS = [
    {"id": "3", "title": "Molecular Pathways and Mechanism"},
    {"id": "4", "title": "Tumor Microenvironment and Mutation Profile"},
    {"id": "5", "title": "Biomarker Landscape"},
    {"id": "6", "title": "Target Prevalence"},
    {"id": "7", "title": "Assay Landscape"},
    {"id": "10", "title": "Vendors and External Partners"},
    {"id": "12", "title": "Target Characteristics Based on Molecular Data"},
    {"id": "13", "title": "Scientific Textual Insights"},
    {"id": "14", "title": "Experimental Materials Availability"},
    {"id": "15", "title": "Key Opinion Leaders"},
    {"id": "16", "title": "Patent Landscape"},
    {"id": "18", "title": "References and Appendices"},
]


# ---------------------------------------------------------------------------
# ReportAgent
# ---------------------------------------------------------------------------


class ReportAgent(BaseAgent):
    """
    Dedicated pharmaceutical report generation agent.

    Produces structured reports following the EMD Biopharma R&D format.
    Can be invoked by any application through the standard BaseAgent
    interface:

        task = AgentTask(
            task_id="...",
            query="Generate CI report for Pembrolizumab",
            task_type="report_generation",
            parameters={
                "drug_name": "Pembrolizumab",
                "report_type": "competitive_intelligence",
                "conversation_context": "...",   # optional
            },
        )
        result = await report_agent.process(task, context)
        report_markdown = result.result_data["report"]
    """

    def __init__(self, mcp_orchestrator=None, llm=None, config_data=None):
        # Store config_data before super().__init__ so we can create a
        # properly configured LLM if none was provided.
        self._config_data = config_data

        if llm is None and config_data is not None:
            from utils.llm_factory import get_llm_from_config
            llm = get_llm_from_config(config_data, temperature=0.3, max_tokens=16384)

        super().__init__("ReportAgent", mcp_orchestrator, llm)

        # Pre-load the EMD format template
        self._emd_format = _load_emd_format()

    # ---- BaseAgent abstract method implementations ----

    def _define_capabilities(self) -> List[str]:
        return [
            "competitive_intelligence_report",
            "target_cv_report",
            "clinical_summary_report",
            "report_section_research",
            "emd_format_compilation",
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return [
            "biomcp",
            "opentargets",
            "pubchem",
            "stringdb",
            "medrxiv",
            "biorxiv",
        ]

    def _define_keywords(self) -> List[str]:
        return [
            "report", "generate report", "competitive intelligence",
            "CI report", "target CV", "clinical summary",
            "EMD format", "biopharma report",
        ]

    # ---- Core processing ----

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Generate a full report.

        Expected task.parameters:
            drug_name (str): The drug or target to report on.
            report_type (str): One of "competitive_intelligence" (default).
            conversation_context (str, optional): Chat transcript for extra context.
        """
        start_time = time.time()
        result = AgentResult(
            task_id=task.task_id,
            agent_name=self.agent_name,
            success=True,
        )

        try:
            params = task.parameters or {}
            drug_name = params.get("drug_name", task.query)
            report_type = params.get("report_type", "competitive_intelligence")
            conversation_context = params.get("conversation_context", "")

            if report_type == "competitive_intelligence":
                report_md = await self._generate_ci_report(
                    drug_name, conversation_context
                )
            else:
                report_md = f"# Report\n\nReport type '{report_type}' is not yet implemented."

            result.result_data = {
                "report": report_md,
                "drug_name": drug_name,
                "report_type": report_type,
                "agent": self.agent_name,
            }
            result.mcps_used = self.preferred_mcps
            result.tools_used = ["llm_section_research", "emd_compilation"]

        except Exception as e:
            result.success = False
            result.error_message = f"ReportAgent error: {str(e)}"

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result

    # ---- Competitive Intelligence report ----

    async def _generate_ci_report(
        self, drug_name: str, conversation_context: str
    ) -> str:
        """Research each section individually, then compile the full report."""

        report_date = datetime.now().strftime("%Y-%m-%d")
        section_results: Dict[str, str] = {}

        # 1) Research core sections (detailed)
        for section in CI_CORE_SECTIONS:
            section_md = self._research_section(
                drug_name=drug_name,
                section_id=section["id"],
                section_title=section["title"],
                research_prompt=section["research_prompt"].format(drug_name=drug_name),
                conversation_context=conversation_context,
                detailed=True,
            )
            section_results[section["id"]] = section_md

        # 2) Research non-core sections (brief)
        for section in CI_BRIEF_SECTIONS:
            section_md = self._research_section(
                drug_name=drug_name,
                section_id=section["id"],
                section_title=section["title"],
                research_prompt=(
                    f"Provide a brief 2-3 sentence summary of the "
                    f"{section['title'].lower()} for {drug_name}."
                ),
                conversation_context=conversation_context,
                detailed=False,
            )
            section_results[section["id"]] = section_md

        # 3) Compile into final document
        report = self._compile_report(drug_name, report_date, section_results)
        return report

    def _research_section(
        self,
        drug_name: str,
        section_id: str,
        section_title: str,
        research_prompt: str,
        conversation_context: str,
        detailed: bool,
    ) -> str:
        """Use the LLM to research and write a single report section."""

        # Build a section-specific prompt that references the EMD template
        # structure so the LLM produces correctly formatted output.
        emd_section_ref = self._extract_section_template(section_id)

        detail_instruction = (
            "Be thorough and detailed. Populate ALL tables from the template "
            "with real data. Use specific drug names, NCT numbers, companies, "
            "and mechanisms. Do NOT leave table rows empty."
            if detailed
            else "Keep it concise — 2-4 sentences. Include a brief table only "
            "if you have concrete data; otherwise omit the table."
        )

        context_block = ""
        if conversation_context:
            context_block = (
                f"\n\nThe user has been researching {drug_name}. "
                f"Relevant conversation:\n{conversation_context[:3000]}"
            )

        prompt = f"""You are a senior pharmaceutical intelligence analyst writing Section {section_id} of a Competitive Intelligence Report for **{drug_name}**.

## EMD Template for This Section
{emd_section_ref}

## Research Task
{research_prompt}
{context_block}

## Formatting Requirements
- Use the EXACT markdown headings and table formats from the EMD template above.
- {detail_instruction}
- Be factual. Cite specific data where possible.
- Output ONLY the section markdown — no preamble, no commentary.
- Start with the section heading: ## {section_id}. {section_title}

Write this section now:"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            return content.strip()
        except Exception as e:
            return (
                f"## {section_id}. {section_title}\n\n"
                f"*Section generation failed: {e}*"
            )

    def _extract_section_template(self, section_id: str) -> str:
        """Extract a specific section from the EMD format template."""
        if not self._emd_format:
            return "(EMD template not available)"

        lines = self._emd_format.split("\n")
        section_lines = []
        capturing = False

        for line in lines:
            # Match "## N." or "## NN." at the start of a line
            if line.startswith(f"## {section_id}."):
                capturing = True
            elif capturing and line.startswith("## ") and not line.startswith(f"## {section_id}."):
                # Hit the next top-level section — stop
                break

            if capturing:
                section_lines.append(line)

        return "\n".join(section_lines) if section_lines else "(Section template not found)"

    def _compile_report(
        self,
        drug_name: str,
        report_date: str,
        section_results: Dict[str, str],
    ) -> str:
        """Assemble all sections into the final report document."""

        header = (
            f"# Biopharma Research & Development Report\n"
            f"# Competitive Intelligence: {drug_name}\n\n"
            f"**Report Date:** {report_date}\n"
            f"**Prepared By:** AI Research Intelligence System (ReportAgent)\n"
            f"**Subject:** {drug_name}\n\n"
            f"---\n"
        )

        # Order sections by their numeric ID
        all_section_ids = sorted(
            section_results.keys(),
            key=lambda x: int(x),
        )

        body_parts = []
        for sid in all_section_ids:
            body_parts.append(section_results[sid])
            body_parts.append("\n---\n")

        footer = (
            "\n*Generated by ReportAgent — Pharmaceutical Research Intelligence System*\n"
        )

        return header + "\n".join(body_parts) + footer
