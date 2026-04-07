"""
Chemical Agent

Specializes in chemical compound queries using PubChem, ChEMBL, and BioMCP.
Gathers real data from MCP servers, then synthesizes with LLM.
"""

import json
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class ChemicalAgent(BaseAgent):
    """Chemical compound specialist agent."""

    def __init__(self, mcp_orchestrator, llm=None):
        super().__init__("ChemicalAgent", mcp_orchestrator, llm)

    def _define_capabilities(self) -> List[str]:
        return [
            "compound_search",
            "molecular_structure_analysis",
            "bioactivity_analysis",
            "safety_toxicity_assessment",
            "drug_likeness_evaluation",
            "regulatory_info_retrieval",
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return ["pubchem", "biomcp", "chembl"]

    def _define_keywords(self) -> List[str]:
        return [
            "compound", "molecule", "chemical", "drug", "structure",
            "SMILES", "InChI", "CAS", "pubchem", "molecular formula",
            "molecular weight", "logP", "TPSA", "druglikeness",
            "bioactivity", "assay", "IC50", "EC50", "toxicity",
            "safety", "ADMET", "pharmacophore", "similarity",
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process chemical compound query using MCP tools + LLM synthesis."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            drug_name = task.parameters.get("drug_name", task.query)
            mcp_data: Dict[str, Any] = {}
            actual_mcps: List[str] = []
            actual_tools: List[str] = []

            ctx = {
                "agent_id": self.agent_name,
                "query_type": "chemical_search",
                "query_text": task.query,
                "session_id": context.session_id,
                "user_id": context.user_id,
            }

            # Phase 1: Gather real data from MCP tools in parallel
            parallel_calls = [
                ("search_compounds_by_name", {"name": drug_name}),
                ("drug_getter", {"chemical": drug_name}),
                ("openfda_label_searcher", {"drug": drug_name}),
            ]
            results = await self._call_mcp_tools_parallel(parallel_calls, ctx)

            tool_names = ["search_compounds_by_name", "drug_getter", "openfda_label_searcher"]
            mcp_names = ["pubchem", "biomcp", "biomcp"]
            for i, (data, ok) in enumerate(results):
                if ok and data:
                    mcp_data[tool_names[i]] = data
                    actual_tools.append(tool_names[i])
                    if mcp_names[i] not in actual_mcps:
                        actual_mcps.append(mcp_names[i])

            # Phase 2: Synthesize with LLM
            if mcp_data:
                data_str = json.dumps(mcp_data, indent=2, default=str)
                if len(data_str) > 12000:
                    data_str = data_str[:12000] + "\n... (truncated)"

                prompt = f"""You are a Chemical Compound Specialist. Analyze the following real data
gathered from pharmaceutical databases and provide a comprehensive response.

Query: {task.query}
Research Context: {context.research_goal or "General pharmaceutical research"}

## Data from MCP Tools:
{data_str}

Synthesize this data into a clear, detailed response. Include molecular properties,
safety data, and clinical relevance where available. Cite the data sources for each fact."""
            else:
                # Fallback: LLM-only
                prompt = f"""You are a Chemical Compound Specialist with expertise in molecular
structure analysis, drug-likeness, bioactivity, and safety assessment.

Research Context: {context.research_goal or "General pharmaceutical research"}
Query: {task.query}

Provide a detailed, scientifically accurate response covering molecular properties,
bioactivity, safety data, and clinical relevance."""

            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)

            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "mcp_data": mcp_data,
                "data_sourced": bool(mcp_data),
                "expertise_area": "Chemical Compounds & Drug Discovery",
            }
            result.mcps_used = actual_mcps or ["llm_only"]
            result.tools_used = actual_tools or ["llm_analysis"]

        except Exception as e:
            result.success = False
            result.error_message = f"ChemicalAgent error: {str(e)}"

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
