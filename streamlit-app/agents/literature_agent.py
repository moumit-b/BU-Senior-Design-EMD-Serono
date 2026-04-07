"""
Literature Agent

Specializes in scientific literature search using BioMCP, PubMed, medRxiv, and bioRxiv.
Gathers real data from MCP servers, then synthesizes with LLM.
"""

import json
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class LiteratureAgent(BaseAgent):
    """Scientific literature specialist agent."""

    def __init__(self, mcp_orchestrator, llm=None):
        super().__init__("LiteratureAgent", mcp_orchestrator, llm)

    def _define_capabilities(self) -> List[str]:
        return [
            "literature_search",
            "pubmed_query",
            "citation_analysis",
            "abstract_extraction",
            "preprint_search",
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return ["biomcp", "literature", "medrxiv", "biorxiv"]

    def _define_keywords(self) -> List[str]:
        return [
            "literature", "publication", "paper", "article", "study",
            "PubMed", "PMID", "DOI", "journal", "citation",
            "author", "abstract", "research", "review",
            "meta-analysis", "clinical study", "scientific",
            "preprint", "biorxiv", "medrxiv",
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process literature query using MCP tools + LLM synthesis."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            drug_name = task.parameters.get("drug_name", task.query)
            mcp_data: Dict[str, Any] = {}
            actual_mcps: List[str] = []
            actual_tools: List[str] = []

            ctx = {
                "agent_id": self.agent_name,
                "query_type": "literature_search",
                "query_text": task.query,
                "session_id": context.session_id,
                "user_id": context.user_id,
            }

            # Phase 1: Search across multiple literature sources in parallel
            parallel_calls = [
                ("article_searcher", {"keywords": [drug_name]}),
                ("search_pubmed", {"query": drug_name}),
                ("search_medrxiv_preprints", {"query": drug_name}),
                ("search_biorxiv_preprints", {"query": drug_name}),
            ]
            results = await self._call_mcp_tools_parallel(parallel_calls, ctx)

            tool_names = [c[0] for c in parallel_calls]
            mcp_map = {
                "article_searcher": "biomcp",
                "search_pubmed": "literature",
                "search_medrxiv_preprints": "medrxiv",
                "search_biorxiv_preprints": "biorxiv",
            }
            for i, (data, ok) in enumerate(results):
                if ok and data:
                    mcp_data[tool_names[i]] = data
                    actual_tools.append(tool_names[i])
                    mcp = mcp_map.get(tool_names[i], "biomcp")
                    if mcp not in actual_mcps:
                        actual_mcps.append(mcp)

            # Phase 2: Synthesize with LLM
            if mcp_data:
                data_str = json.dumps(mcp_data, indent=2, default=str)
                if len(data_str) > 12000:
                    data_str = data_str[:12000] + "\n... (truncated)"

                prompt = f"""You are a Scientific Literature Research Specialist. Analyze the following
real search results from biomedical literature databases.

Query: {task.query}
Research Context: {context.research_goal or "General literature research"}

## Literature Search Results:
{data_str}

Synthesize these results into a comprehensive literature review. Include
key findings, notable publications (with PMIDs/DOIs), research trends,
and knowledge gaps. Distinguish between peer-reviewed and preprint sources."""
            else:
                prompt = f"""You are a Scientific Literature Research Specialist with expertise in
biomedical research, preprints, and citation analysis.

Research Context: {context.research_goal or "General literature research"}
Query: {task.query}

Provide a comprehensive literature review covering key publications,
research trends, and knowledge gaps."""

            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)

            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "mcp_data": mcp_data,
                "data_sourced": bool(mcp_data),
                "expertise_area": "Scientific Literature & Research",
            }
            result.mcps_used = actual_mcps or ["llm_only"]
            result.tools_used = actual_tools or ["llm_analysis"]

        except Exception as e:
            result.success = False
            result.error_message = f"LiteratureAgent error: {str(e)}"

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
