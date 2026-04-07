"""
Clinical Agent

Specializes in clinical trials and regulatory data using BioMCP and OpenFDA.
Gathers real data from MCP servers, then synthesizes with LLM.
"""

import json
import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class ClinicalAgent(BaseAgent):
    """Clinical trials and regulatory specialist agent."""

    def __init__(self, mcp_orchestrator, llm=None):
        super().__init__("ClinicalAgent", mcp_orchestrator, llm)

    def _define_capabilities(self) -> List[str]:
        return [
            "clinical_trial_search",
            "trial_protocol_analysis",
            "regulatory_info_retrieval",
            "adverse_event_analysis",
            "drug_approval_lookup",
            "intervention_search",
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return ["biomcp", "opentargets"]

    def _define_keywords(self) -> List[str]:
        return [
            "clinical trial", "trial", "NCT", "phase", "recruitment",
            "FDA", "approval", "regulatory", "label", "indication",
            "adverse event", "safety", "recall", "shortage",
            "intervention", "sponsor", "enrollment", "endpoint",
            "protocol", "OpenFDA", "opentargets",
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process clinical/regulatory query using MCP tools + LLM synthesis."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            drug_name = task.parameters.get("drug_name", task.query)
            mcp_data: Dict[str, Any] = {}
            actual_mcps: List[str] = []
            actual_tools: List[str] = []

            ctx = {
                "agent_id": self.agent_name,
                "query_type": "clinical_trial",
                "query_text": task.query,
                "session_id": context.session_id,
                "user_id": context.user_id,
            }

            # Phase 1: Gather real data in parallel
            parallel_calls = [
                ("trial_searcher", {"interventions": drug_name}),
                ("openfda_adverse_searcher", {"drug": drug_name}),
                ("openfda_approval_searcher", {"drug": drug_name}),
                ("openfda_label_searcher", {"drug": drug_name}),
                ("nci_intervention_searcher", {"query": drug_name}),
                ("disease_getter", {"disease": task.parameters.get("indication", drug_name)}),
            ]
            results = await self._call_mcp_tools_parallel(parallel_calls, ctx)

            tool_names = [c[0] for c in parallel_calls]
            for i, (data, ok) in enumerate(results):
                if ok and data:
                    mcp_data[tool_names[i]] = data
                    actual_tools.append(tool_names[i])
                    actual_mcps.append("biomcp")

            # Deduplicate
            actual_mcps = list(set(actual_mcps))

            # Phase 2: Synthesize with LLM
            if mcp_data:
                data_str = json.dumps(mcp_data, indent=2, default=str)
                if len(data_str) > 12000:
                    data_str = data_str[:12000] + "\n... (truncated)"

                prompt = f"""You are a Clinical Trials and Regulatory Affairs Specialist. Analyze the
following real data from clinical and regulatory databases.

Query: {task.query}
Research Context: {context.research_goal or "General clinical research"}

## Data from MCP Tools:
{data_str}

Synthesize this data into a comprehensive clinical/regulatory response.
Include trial phases, NCT numbers, regulatory status, adverse events,
and approval history. Cite database sources for each fact."""
            else:
                prompt = f"""You are a Clinical Trials and Regulatory Affairs Specialist with expertise
in trial design, FDA processes, adverse events, and drug approvals.

Research Context: {context.research_goal or "General clinical research"}
Query: {task.query}

Provide a detailed, evidence-based response covering clinical trial data,
regulatory context, and safety considerations."""

            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)

            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "mcp_data": mcp_data,
                "data_sourced": bool(mcp_data),
                "expertise_area": "Clinical Trials & Regulatory Affairs",
            }
            result.mcps_used = actual_mcps or ["llm_only"]
            result.tools_used = actual_tools or ["llm_analysis"]

        except Exception as e:
            result.success = False
            result.error_message = f"ClinicalAgent error: {str(e)}"

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
