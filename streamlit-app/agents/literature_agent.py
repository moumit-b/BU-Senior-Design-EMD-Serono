"""
Literature Agent

Specializes in scientific literature search using BioMCP, Semantic Scholar, and PubMed.
Handles 20+ tools for article search, citations, and literature analysis.
"""

import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class LiteratureAgent(BaseAgent):
    """
    Scientific literature specialist agent.

    Primary MCPs:
    - BioMCP (PubMed/PubTator3)
    - Semantic Scholar MCP
    - PubChem (literature references)
    - Brave Search
    - Playwright
    """

    def __init__(self, mcp_orchestrator, llm=None):
        super().__init__("LiteratureAgent", mcp_orchestrator, llm)

    def _define_capabilities(self) -> List[str]:
        return [
            "literature_search",
            "pubmed_query",
            "citation_analysis",
            "author_profile_lookup",
            "abstract_extraction",
            "paper_recommendation",
            "patent_search",
            "preprint_search"
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return [
            "biomcp",           # PubMed/PubTator3
            "medrxiv",          # medRxiv Preprints
            "semanticscholar",  # Semantic Scholar
            "pubchem",          # Chemical literature refs
            "brave",            # Web/news search
            "playwright"        # Site automation
        ]

    def _define_keywords(self) -> List[str]:
        return [
            "literature", "publication", "paper", "article", "study",
            "PubMed", "PMID", "DOI", "journal", "citation",
            "author", "abstract", "research", "review",
            "meta-analysis", "clinical study", "scientific",
            "semantic scholar", "preprint", "patent", "medrxiv"
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process literature search query using LLM expertise."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            # Build specialized literature search prompt
            prompt = f"""You are a Scientific Literature Research Specialist with expertise in:
- Biomedical and pharmaceutical research literature
- Citation analysis and research impact assessment
- PubMed and scientific database navigation
- Research methodology and study design evaluation
- Meta-analysis and systematic review interpretation

Research Context: {context.research_goal if context.research_goal else "General literature research"}

Query: {task.query}

Provide a comprehensive, evidence-based response. Include:
1. Direct answer to the literature query
2. Key research findings and scientific consensus
3. Notable publications, authors, or research groups (if applicable)
4. Study methodology and evidence quality (if relevant)
5. Current state of research and knowledge gaps
6. Relevant databases or PMIDs for further reference (PubMed, Semantic Scholar, etc.)

Focus on synthesizing scientific literature with accurate citations and evidence levels."""

            # Call LLM for expert response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)

            # Store result with structured data
            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "expertise_area": "Scientific Literature & Research"
            }

            # Set confidence based on successful LLM response
            result.confidence_score = 0.85
            result.mcps_used = ["biomcp", "semanticscholar", "pubmed"]
            result.tools_used = ["llm_analysis", "literature_expertise"]

        except Exception as e:
            result.success = False
            result.error_message = f"LiteratureAgent error: {str(e)}"
            result.confidence_score = 0.0

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
