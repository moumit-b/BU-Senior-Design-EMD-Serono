"""
Report Agent

Dedicated agent for generating structured pharmaceutical research reports.
Extends BaseAgent so it can be used by any application via the standard
agent interface: ReportAgent.process(task, context) -> AgentResult.

The agent owns the full report lifecycle:
1. Creates specialized agent instances (Chemical, Clinical, Gene, Literature, Data)
2. Maps each EMD section to the most relevant agents
3. Dispatches AgentTasks in parallel via asyncio.gather()
4. Collects real MCP data from agents, then uses LLM to write each section
5. Compiles all sections into the final EMD-structured report

All MCP tool calls flow through the MCPOrchestrator + Context Forge Gateway
for governance, audit logging, compliance, and rate limiting.

Currently supports:
- Competitive Intelligence Report
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext

logger = logging.getLogger(__name__)


def _log(msg: str):
    """Print + log for terminal visibility during report generation."""
    print(f"[ReportAgent] {msg}")
    logger.info(msg)

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

CI_CORE_SECTIONS = [
    {
        "id": "1",
        "title": "Executive Summary and 6R Framework Alignment",
        "agents": ["clinical", "gene"],
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
        "agents": ["gene", "chemical"],
        "research_prompt": (
            "Provide comprehensive target and biomarker information for {drug_name}: "
            "target name, synonyms, biochemical class, function, molecular function / "
            "mode of action, subcellular location, gene ID, protein ID, protein family, "
            "drug targets, known ligands, and interacting proteins."
        ),
    },
    {
        "id": "3",
        "title": "Molecular Pathways and Mechanism",
        "agents": ["gene"],
        "research_prompt": (
            "Describe the molecular pathways and mechanism of action for {drug_name}. "
            "Include signaling pathways, pathway cross-talk, and therapeutic relevance."
        ),
    },
    {
        "id": "4",
        "title": "Tumor Microenvironment and Mutation Profile",
        "agents": ["gene"],
        "research_prompt": (
            "Describe the tumor microenvironment relevance and mutation profile "
            "for {drug_name}, including immune context and genomic alterations."
        ),
    },
    {
        "id": "5",
        "title": "Biomarker Landscape",
        "agents": ["gene", "clinical"],
        "research_prompt": (
            "Describe the biomarker landscape for {drug_name}: predictive, prognostic, "
            "and pharmacodynamic biomarkers, companion diagnostics, and assay platforms."
        ),
    },
    {
        "id": "6",
        "title": "Target Prevalence",
        "agents": ["gene"],
        "research_prompt": (
            "Describe target prevalence and expression data for {drug_name} "
            "across tumor types, including IHC, FISH, NGS, and RNA expression data."
        ),
    },
    {
        "id": "7",
        "title": "Assay Landscape",
        "agents": ["chemical"],
        "research_prompt": (
            "Describe the assay landscape for {drug_name}: available assay platforms, "
            "detection methods, sensitivity, specificity, and turnaround times."
        ),
    },
    {
        "id": "8",
        "title": "Regulatory and Commercial Overview",
        "agents": ["clinical"],
        "research_prompt": (
            "Provide the regulatory and commercial overview for {drug_name}: "
            "approval status by country/region, regulatory class, validation stage, "
            "performance metrics (sensitivity, specificity, turnaround, cost), "
            "commercial overview (market share, reimbursement), and guideline "
            "landscape (NCCN, ASCO/CAP, region-specific)."
        ),
    },
    {
        "id": "9",
        "title": "Competitive Landscape",
        "agents": ["clinical", "chemical", "literature"],
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
        "id": "10",
        "title": "Vendors and External Partners",
        "agents": ["chemical"],
        "research_prompt": (
            "Identify key vendors and external partners for {drug_name}: "
            "CDx developers, assay providers, CROs, and technology licensors."
        ),
    },
    {
        "id": "11",
        "title": "Target Landscape and Development Trends",
        "agents": ["clinical", "gene"],
        "research_prompt": (
            "Provide the target landscape and development trends for {drug_name}: "
            "overview of diseases amenable to the mechanism, competitor situation "
            "on-target and on-pathway, drug development data table, clinical trials "
            "data table, and development trends (modality trends, biomarker strategy "
            "evolution, combination opportunities)."
        ),
    },
    {
        "id": "12",
        "title": "Target Characteristics Based on Molecular Data",
        "agents": ["gene"],
        "research_prompt": (
            "Describe target characteristics based on molecular data for {drug_name}: "
            "protein structure, post-translational modifications, isoforms, and "
            "structural biology insights."
        ),
    },
    {
        "id": "13",
        "title": "Scientific Textual Insights",
        "agents": ["literature"],
        "research_prompt": (
            "Provide scientific textual insights for {drug_name}: key publications, "
            "review articles, landmark studies, and emerging research themes."
        ),
    },
    {
        "id": "14",
        "title": "Experimental Materials Availability",
        "agents": ["chemical"],
        "research_prompt": (
            "Describe experimental materials availability for {drug_name}: "
            "antibodies, cell lines, animal models, reference standards, and reagents."
        ),
    },
    {
        "id": "15",
        "title": "Key Opinion Leaders",
        "agents": ["literature"],
        "research_prompt": (
            "Identify key opinion leaders (KOLs) for {drug_name}: leading researchers, "
            "clinical investigators, and their institutional affiliations."
        ),
    },
    {
        "id": "16",
        "title": "Patent Landscape",
        "agents": ["chemical", "clinical"],
        "research_prompt": (
            "Describe the patent landscape for {drug_name}: key patents, "
            "patent holders, expiration dates, and freedom to operate considerations."
        ),
    },
    {
        "id": "17",
        "title": "Risks, Gaps, and Recommended Next Steps",
        "agents": ["clinical", "gene", "literature"],
        "research_prompt": (
            "Identify evidence gaps, key risks (scientific, translational, regulatory, "
            "commercial), and recommended next steps for {drug_name}. "
            "Include specific actionable recommendations for assays, competitive "
            "intelligence follow-up, vendor outreach, experiments, and patent review."
        ),
    },
    {
        "id": "18",
        "title": "References and Appendices",
        "agents": ["literature"],
        "research_prompt": (
            "Compile references and appendices for {drug_name}: key publications "
            "with PMIDs/DOIs, data sources consulted, and methodology notes."
        ),
    },
]

# Sections that get thorough treatment (detailed tables, exhaustive analysis)
_DETAILED_SECTION_IDS = {"1", "2", "8", "9", "11", "17"}

# Max concurrent sections to prevent flooding MCP servers
_MAX_CONCURRENT_SECTIONS = 3

# Max concurrent MCP tool calls across all agents
_MCP_SEMAPHORE: Optional[asyncio.Semaphore] = None


# ---------------------------------------------------------------------------
# ReportAgent
# ---------------------------------------------------------------------------


class ReportAgent(BaseAgent):
    """
    Dedicated pharmaceutical report generation agent.

    Orchestrates specialized agents (Chemical, Clinical, Gene, Literature, Data)
    to gather real data from MCP servers, then uses LLM to synthesize each
    section of the EMD-formatted report.

    Can be invoked by any application through the standard BaseAgent interface:

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
        self._config_data = config_data

        if llm is None and config_data is not None:
            from utils.llm_factory import get_llm_from_config
            llm = get_llm_from_config(config_data, temperature=0.3, max_tokens=16384)

        super().__init__("ReportAgent", mcp_orchestrator, llm)

        # Pre-load the EMD format template
        self._emd_format = _load_emd_format()

        # Create specialized agent instances that share our orchestrator + LLM
        self._agents = self._create_agents()

    def _create_agents(self) -> Dict[str, BaseAgent]:
        """Create specialized agent instances for data gathering."""
        from .chemical_agent import ChemicalAgent
        from .clinical_agent import ClinicalAgent
        from .gene_agent import GeneAgent
        from .literature_agent import LiteratureAgent
        from .data_agent import DataAgent

        agents = {
            "chemical": ChemicalAgent(self.mcp_orchestrator, self.llm),
            "clinical": ClinicalAgent(self.mcp_orchestrator, self.llm),
            "gene": GeneAgent(self.mcp_orchestrator, self.llm),
            "literature": LiteratureAgent(self.mcp_orchestrator, self.llm),
            "data": DataAgent(self.mcp_orchestrator, self.llm),
        }
        _log(f"Created {len(agents)} specialized agents (mcp_orchestrator={'active' if self.mcp_orchestrator else 'None'})")
        return agents

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
            "biomcp", "opentargets", "pubchem",
            "stringdb", "medrxiv", "biorxiv",
        ]

    def _define_keywords(self) -> List[str]:
        return [
            "report", "generate report", "competitive intelligence",
            "CI report", "target CV", "clinical summary",
            "EMD format", "biopharma report",
        ]

    # ---- Core processing ----

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Generate a full report by orchestrating specialized agents."""
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
                report_md, mcps_used, tools_used = await self._generate_ci_report(
                    drug_name, conversation_context, context
                )
            else:
                report_md = f"# Report\n\nReport type '{report_type}' is not yet implemented."
                mcps_used = []
                tools_used = []

            result.result_data = {
                "report": report_md,
                "drug_name": drug_name,
                "report_type": report_type,
                "agent": self.agent_name,
            }
            result.mcps_used = mcps_used or ["llm_only"]
            result.tools_used = tools_used or ["llm_analysis"]

        except Exception as e:
            _log(f"PROCESS FAILED: {e}")
            result.success = False
            result.error_message = f"ReportAgent error: {str(e)}"

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result

    # ---- Competitive Intelligence report ----

    async def _generate_ci_report(
        self,
        drug_name: str,
        conversation_context: str,
        agent_context: AgentContext,
    ) -> tuple:
        """Generate CI report by dispatching all 18 sections in parallel.

        Returns:
            (report_markdown, mcps_used, tools_used)
        """
        report_date = datetime.now().strftime("%Y-%m-%d")
        all_mcps: List[str] = []
        all_tools: List[str] = []

        _log(f"Starting CI report for '{drug_name}' — {len(CI_CORE_SECTIONS)} sections")

        # Initialize a global semaphore to limit concurrent MCP calls
        global _MCP_SEMAPHORE
        _MCP_SEMAPHORE = asyncio.Semaphore(4)  # max 4 concurrent MCP calls

        # Process sections in batches to avoid flooding MCP servers
        section_results_map: Dict[str, Any] = {}
        batch_size = _MAX_CONCURRENT_SECTIONS

        for batch_start in range(0, len(CI_CORE_SECTIONS), batch_size):
            batch = CI_CORE_SECTIONS[batch_start:batch_start + batch_size]
            batch_ids = [s["id"] for s in batch]
            _log(f"Processing batch: sections {batch_ids}")

            coros = []
            for section in batch:
                coro = self._research_section_with_agents(
                    drug_name=drug_name,
                    section=section,
                    conversation_context=conversation_context,
                    agent_context=agent_context,
                    detailed=section["id"] in _DETAILED_SECTION_IDS,
                )
                coros.append((section["id"], coro))

            batch_coros = [coro for _, coro in coros]
            results = await asyncio.gather(*batch_coros, return_exceptions=True)

            for i, (section_id, _) in enumerate(coros):
                section_results_map[section_id] = results[i]

            _log(f"Batch {batch_ids} completed")

        _log(f"All {len(CI_CORE_SECTIONS)} sections completed")

        section_results: Dict[str, str] = {}
        for section_id, res in section_results_map.items():
            if isinstance(res, Exception):
                _log(f"Section {section_id} FAILED: {res}")
                title = next(
                    (s["title"] for s in CI_CORE_SECTIONS if s["id"] == section_id),
                    "Unknown",
                )
                section_results[section_id] = (
                    f"## {section_id}. {title}\n\n"
                    f"*Section generation encountered an error: {res}*"
                )
            else:
                section_md, section_mcps, section_tools = res
                section_results[section_id] = section_md
                for m in section_mcps:
                    if m not in all_mcps:
                        all_mcps.append(m)
                all_tools.extend(section_tools)

        # Compile into final document
        report = self._compile_report(drug_name, report_date, section_results)
        return report, all_mcps, list(set(all_tools))

    async def _research_section_with_agents(
        self,
        drug_name: str,
        section: Dict[str, Any],
        conversation_context: str,
        agent_context: AgentContext,
        detailed: bool,
    ) -> tuple:
        """Research a single section by dispatching to specialized agents, then synthesize.

        Returns:
            (section_markdown, mcps_used, tools_used)
        """
        section_id = section["id"]
        section_title = section["title"]
        agent_names = section.get("agents", [])
        research_prompt = section["research_prompt"].format(drug_name=drug_name)

        _log(f"Section {section_id} ({section_title}): dispatching to agents {agent_names}")

        # Phase 1: Gather data from specialized agents in parallel
        agent_data = await self._gather_agent_data(
            drug_name=drug_name,
            query=research_prompt,
            agent_names=agent_names,
            agent_context=agent_context,
        )

        # Collect MCP/tool metadata from agent results
        section_mcps: List[str] = []
        section_tools: List[str] = []
        mcp_data_blocks: Dict[str, Any] = {}

        _log(f"Section {section_id}: agent data gathered, synthesizing...")

        for agent_name, agent_result in agent_data.items():
            if agent_result and agent_result.success:
                for m in agent_result.mcps_used:
                    if m not in section_mcps and m != "llm_only":
                        section_mcps.append(m)
                for t in agent_result.tools_used:
                    if t != "llm_analysis":
                        section_tools.append(t)
                # Extract MCP data for synthesis
                rd = agent_result.result_data or {}
                if rd.get("mcp_data"):
                    mcp_data_blocks[agent_name] = rd["mcp_data"]

        # Phase 2: Synthesize with LLM using agent data + EMD template
        section_md = await self._synthesize_section(
            drug_name=drug_name,
            section_id=section_id,
            section_title=section_title,
            research_prompt=research_prompt,
            agent_data=agent_data,
            mcp_data_blocks=mcp_data_blocks,
            conversation_context=conversation_context,
            detailed=detailed,
        )

        return section_md, section_mcps, section_tools

    async def _gather_agent_data(
        self,
        drug_name: str,
        query: str,
        agent_names: List[str],
        agent_context: AgentContext,
    ) -> Dict[str, Optional[AgentResult]]:
        """Dispatch tasks to multiple specialized agents in parallel.

        Returns:
            {agent_name: AgentResult or None}
        """
        results: Dict[str, Optional[AgentResult]] = {}

        async def _run_agent(name: str) -> tuple:
            agent = self._agents.get(name)
            if agent is None:
                return name, None
            try:
                task = AgentTask(
                    task_id=f"report_sub_{name}_{int(time.time()*1000)}",
                    query=query,
                    task_type="report_data_gathering",
                    parameters={"drug_name": drug_name},
                )
                result = await agent.process(task, agent_context)
                return name, result
            except Exception as e:
                _log(f"Agent {name} failed during report gathering: {e}")
                return name, None

        # Run all agents in parallel
        tasks = [_run_agent(name) for name in agent_names]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        for item in gathered:
            if isinstance(item, Exception):
                _log(f"Agent gather exception: {item}")
            else:
                name, result = item
                results[name] = result

        return results

    async def _synthesize_section(
        self,
        drug_name: str,
        section_id: str,
        section_title: str,
        research_prompt: str,
        agent_data: Dict[str, Optional[AgentResult]],
        mcp_data_blocks: Dict[str, Any],
        conversation_context: str,
        detailed: bool,
    ) -> str:
        """Use LLM to write a section using real agent/MCP data + EMD template."""

        emd_section_ref = self._extract_section_template(section_id)

        # Build data context from agent results
        data_context_parts = []

        # Include raw MCP data (real database results)
        if mcp_data_blocks:
            mcp_str = json.dumps(mcp_data_blocks, indent=2, default=str)
            if len(mcp_str) > 8000:
                mcp_str = mcp_str[:8000] + "\n... (truncated)"
            data_context_parts.append(
                f"## Real Data from MCP Servers (via specialized agents):\n{mcp_str}"
            )

        # Include agent analysis summaries
        for agent_name, result in agent_data.items():
            if result and result.success and result.result_data.get("answer"):
                answer = result.result_data["answer"]
                if len(answer) > 3000:
                    answer = answer[:3000] + "... (truncated)"
                sources = ", ".join(result.mcps_used) if result.mcps_used else "LLM"
                data_context_parts.append(
                    f"## Analysis from {agent_name} (sources: {sources}):\n{answer}"
                )

        data_context = "\n\n".join(data_context_parts) if data_context_parts else ""

        detail_instruction = (
            "Be thorough and detailed. Populate ALL tables from the template "
            "with real data. Use specific drug names, NCT numbers, companies, "
            "and mechanisms. Do NOT leave table rows empty."
            if detailed
            else "Keep it concise — 3-5 sentences. Include a brief table only "
            "if the agent data contains concrete entries; otherwise omit the table."
        )

        context_block = ""
        if conversation_context:
            context_block = (
                f"\n\nThe user has been researching {drug_name}. "
                f"Relevant conversation:\n{conversation_context[:2000]}"
            )

        # Indicate data sourcing in prompt
        data_sourcing_note = ""
        if data_context:
            data_sourcing_note = (
                "\n\nIMPORTANT: The following data was gathered from REAL biomedical "
                "databases (PubMed, ClinicalTrials.gov, Open Targets, PubChem, "
                "STRING-db, medRxiv, bioRxiv) by specialized AI agents. Use this "
                "real data as the PRIMARY basis for your section. Cite specific "
                "identifiers (NCT numbers, PMIDs, CIDs, gene IDs) from the data.\n\n"
                f"{data_context}"
            )

        prompt = f"""You are a senior pharmaceutical intelligence analyst writing Section {section_id} of a Competitive Intelligence Report for **{drug_name}**.

## EMD Template for This Section
{emd_section_ref}

## Research Task
{research_prompt}
{data_sourcing_note}
{context_block}

## Formatting Requirements
- Use the EXACT markdown headings and table formats from the EMD template above.
- {detail_instruction}
- Be factual. Cite specific data where possible.
- Output ONLY the section markdown — no preamble, no commentary.
- Start with the section heading: ## {section_id}. {section_title}

Write this section now:"""

        try:
            content = await self._invoke_llm(prompt)
            _log(f"Section {section_id} synthesized ({len(content)} chars)")
            return content.strip()
        except Exception as e:
            _log(f"Section {section_id} LLM synthesis failed: {e}")
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
            if line.startswith(f"## {section_id}."):
                capturing = True
            elif capturing and line.startswith("## ") and not line.startswith(f"## {section_id}."):
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
            f"**Data Sources:** MCP Servers (BioMCP, PubChem, Open Targets, "
            f"STRING-db, medRxiv, bioRxiv) via Context Forge Gateway\n"
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
            "\n*Generated by ReportAgent — Multi-Agent Pharmaceutical Research "
            "Intelligence System with MCP-powered data retrieval*\n"
        )

        return header + "\n".join(body_parts) + footer
