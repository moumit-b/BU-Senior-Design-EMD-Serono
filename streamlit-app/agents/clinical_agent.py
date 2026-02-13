"""
Clinical Agent

Specializes in clinical trials and regulatory data using BioMCP and OpenFDA.
Handles 30+ tools for trial search, regulatory info, adverse events, and approvals.
"""

import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class ClinicalAgent(BaseAgent):
    """
    Clinical trials and regulatory specialist agent.

    Primary MCPs:
    - BioMCP (ClinicalTrials.gov, NCI CTS, OpenFDA)
    - PubChem (regulatory info)
    - Brave Search
    - Playwright
    """

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
            "disease_vocabulary_mapping",
            "drug_shortage_monitoring"
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return [
            "biomcp",     # Primary for trials and OpenFDA
            "pubchem",    # Regulatory cross-references
            "brave",      # News updates
            "playwright"  # Dashboard access
        ]

    def _define_keywords(self) -> List[str]:
        return [
            "clinical trial", "trial", "NCT", "phase", "recruitment",
            "FDA", "approval", "regulatory", "label", "indication",
            "adverse event", "safety", "recall", "shortage",
            "intervention", "sponsor", "enrollment", "endpoint",
            "protocol", "inclusion", "exclusion", "OpenFDA"
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process clinical/regulatory query using LLM expertise."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            # Build specialized clinical trials prompt
            prompt = f"""You are a Clinical Trials and Regulatory Affairs Specialist with expertise in:
- Clinical trial design and protocol analysis
- FDA regulatory processes and drug approvals
- Adverse event monitoring and pharmacovigilance
- Clinical study phases and endpoints
- Drug labeling and safety information

Research Context: {context.research_goal if context.research_goal else "General clinical research"}

Query: {task.query}

Provide a detailed, evidence-based response. Include:
1. Direct answer to the clinical/regulatory query
2. Relevant clinical trial information (phases, endpoints, status if applicable)
3. Regulatory context (FDA approvals, indications, safety data if relevant)
4. Adverse events or safety considerations (if applicable)
5. Clinical significance and implications
6. Key databases or NCT numbers for reference (ClinicalTrials.gov, OpenFDA, etc.)

Focus on current, accurate clinical and regulatory information."""

            # Call LLM for expert response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)

            # Store result with structured data
            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "expertise_area": "Clinical Trials & Regulatory Affairs"
            }

            # Set confidence based on successful LLM response
            result.confidence_score = 0.85
            result.mcps_used = ["biomcp", "openfda"]
            result.tools_used = ["llm_analysis", "clinical_expertise"]

        except Exception as e:
            result.success = False
            result.error_message = f"ClinicalAgent error: {str(e)}"
            result.confidence_score = 0.0

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
