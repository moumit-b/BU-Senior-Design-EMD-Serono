"""
Report Generator

Main engine for generating professional research reports from session data.
"""

from enum import Enum
from typing import Dict, Any
from datetime import datetime
from pathlib import Path


class ReportType(Enum):
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    TARGET_CV = "target_cv"
    CLINICAL_SUMMARY = "clinical_summary"


class ReportFormat(Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"


class ReportGenerator:
    def __init__(self, session_manager, llm=None):
        self.session_manager = session_manager
        # Initialize LLM for report section generation
        if llm is None:
            from utils.llm_factory import get_llm
            self.llm = get_llm()
        else:
            self.llm = llm

    def generate_report(self, session_id: str, report_type: ReportType = ReportType.COMPETITIVE_INTELLIGENCE, format: ReportFormat = ReportFormat.MARKDOWN) -> str:
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if report_type == ReportType.COMPETITIVE_INTELLIGENCE:
            content = self._generate_competitive_intelligence(session)
        else:
            content = {"title": "Report", "markdown": "# Report\n\nPending implementation"}

        return content.get("markdown", "")

    def _generate_competitive_intelligence(self, session) -> Dict[str, Any]:
        """Generate comprehensive Competitive Intelligence report with LLM-powered sections."""

        # Gather session data
        queries = session.queries if hasattr(session, 'queries') else []
        entities = session.entities if hasattr(session, 'entities') else []
        insights = session.insights if hasattr(session, 'insights') else []

        # Extract query summaries
        query_summaries = [{"query": q.query_text, "agents_used": getattr(q, 'agents_used', [])} for q in queries[:10]]

        # Extract entity names (entities is a dict, not a list)
        if isinstance(entities, dict):
            entity_names = [e.name for e in list(entities.values())[:20]]
        elif isinstance(entities, list):
            entity_names = [e.name if hasattr(e, 'name') else str(e) for e in entities[:20]]
        else:
            entity_names = []

        # Extract insight content
        insight_content = [i.content for i in insights[:10]]

        # Generate Executive Summary using LLM
        exec_summary = self._generate_executive_summary(session, query_summaries, entity_names, insight_content)

        # Generate Key Findings using LLM
        key_findings = self._generate_key_findings(session, query_summaries, entity_names, insight_content)

        # Generate Competitive Landscape using LLM
        competitive_landscape = self._generate_competitive_landscape(session, entity_names, insight_content)

        # Generate Recommendations using LLM
        recommendations = self._generate_recommendations(session, insight_content)

        # Compile full report
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = []
        md.append(f"# Competitive Intelligence Report")
        md.append(f"**Generated:** {report_date}\n")
        md.append(f"**Session ID:** {session.session_id}")
        md.append(f"**Research Goal:** {session.research_goal}\n")
        md.append("---\n")

        md.append("## Executive Summary\n")
        md.append(exec_summary)
        md.append("\n---\n")

        md.append("## Research Overview\n")
        md.append(f"- **Total Queries Executed:** {len(queries)}")
        md.append(f"- **Entities Discovered:** {len(entities)}")
        md.append(f"- **Insights Generated:** {len(insights)}")
        md.append(f"- **Session Duration:** {self._calculate_duration(session)}\n")
        md.append("\n---\n")

        md.append("## Key Findings\n")
        md.append(key_findings)
        md.append("\n---\n")

        md.append("## Competitive Landscape\n")
        md.append(competitive_landscape)
        md.append("\n---\n")

        md.append("## Strategic Recommendations\n")
        md.append(recommendations)
        md.append("\n---\n")

        md.append("## Methodology\n")
        md.append("This report was generated using a multi-agent pharmaceutical research intelligence system:")
        md.append("- **Chemical Agent:** Compound analysis and drug properties")
        md.append("- **Clinical Agent:** Clinical trials and regulatory data")
        md.append("- **Literature Agent:** Scientific publications and research")
        md.append("- **Gene Agent:** Genetics and target biology")
        md.append("- **Data Agent:** Statistical analysis and trends\n")
        md.append("\n---\n")

        md.append("\n*Generated with Pharmaceutical Research Intelligence System*")
        md.append(f"\n*Powered by Claude Sonnet 4.5*")

        return {"markdown": "\n".join(md)}

    def _generate_executive_summary(self, session, queries, entities, insights) -> str:
        """Generate executive summary using LLM."""
        try:
            prompt = f"""You are writing an Executive Summary for a Competitive Intelligence report in pharmaceutical research.

Research Goal: {session.research_goal}

Session Data:
- {len(queries)} queries executed
- {len(entities)} entities discovered (e.g., {', '.join(entities[:5])})
- {len(insights)} insights generated

Sample Insights:
{chr(10).join(['- ' + str(i) for i in insights[:3]])}

Write a 2-3 paragraph executive summary that:
1. Summarizes the research objective and scope
2. Highlights the most significant findings
3. Provides strategic context for decision-making

Keep it concise, professional, and focused on actionable intelligence."""

            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"*Executive summary generation failed: {str(e)}*"

    def _generate_key_findings(self, session, queries, entities, insights) -> str:
        """Generate key findings using LLM."""
        try:
            prompt = f"""You are identifying Key Findings for a Competitive Intelligence report.

Research Goal: {session.research_goal}

Entities Discovered: {', '.join(entities[:10])}

Insights:
{chr(10).join(['- ' + str(i) for i in insights[:5]])}

Generate 4-6 key findings in bullet point format. Each finding should:
1. Be specific and evidence-based
2. Highlight competitive advantages or threats
3. Connect to the research goal
4. Be actionable

Format as bullet points with brief explanations."""

            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            # Fallback to basic findings
            findings = []
            for insight in insights[:5]:
                findings.append(f"- {insight}")
            return "\n".join(findings) if findings else "*No key findings available*"

    def _generate_competitive_landscape(self, session, entities, insights) -> str:
        """Generate competitive landscape analysis using LLM."""
        try:
            prompt = f"""You are analyzing the Competitive Landscape for a pharmaceutical intelligence report.

Research Goal: {session.research_goal}

Key Entities: {', '.join(entities[:10])}

Insights:
{chr(10).join(['- ' + str(i) for i in insights[:5]])}

Provide a competitive landscape analysis covering:
1. Major players and their positions
2. Market trends and dynamics
3. Competitive advantages and gaps
4. Emerging threats or opportunities

Format in 2-3 concise paragraphs."""

            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"*Competitive landscape analysis unavailable: {str(e)}*"

    def _generate_recommendations(self, session, insights) -> str:
        """Generate strategic recommendations using LLM."""
        try:
            prompt = f"""You are providing Strategic Recommendations for a pharmaceutical research intelligence report.

Research Goal: {session.research_goal}

Key Insights:
{chr(10).join(['- ' + str(i) for i in insights[:5]])}

Generate 3-5 actionable strategic recommendations:
1. Based on the research findings
2. Prioritized by impact and feasibility
3. Specific and measurable
4. Aligned with pharmaceutical R&D objectives

Format as numbered recommendations with brief rationale."""

            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"*Recommendations unavailable: {str(e)}*"

    def _calculate_duration(self, session) -> str:
        """Calculate session duration."""
        try:
            if hasattr(session, 'start_time') and hasattr(session, 'last_activity'):
                duration = session.last_activity - session.start_time
                minutes = int(duration / 60)
                return f"{minutes} minutes"
            return "N/A"
        except:
            return "N/A"
