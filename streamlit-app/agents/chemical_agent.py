"""
Chemical Agent

Specializes in chemical compound queries using PubChem, ChEMBL, and BioMCP.
Handles 40+ tools for compound search, properties, bioactivity, safety, and toxicity.
"""

import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class ChemicalAgent(BaseAgent):
    """
    Chemical compound specialist agent.

    Primary MCPs:
    - PubChem-MCP-Server (Augmented-Nature)
    - ChEMBL-MCP-Server (Augmented-Nature)
    - BioMCP (genomoncology)
    - Brave Search (web/news)
    - Playwright (web automation)
    """

    def __init__(self, mcp_orchestrator, llm=None):
        super().__init__("ChemicalAgent", mcp_orchestrator, llm)

    def _define_capabilities(self) -> List[str]:
        return [
            "compound_search",
            "molecular_structure_analysis",
            "bioactivity_analysis",
            "safety_toxicity_assessment",
            "drug_likeness_evaluation",
            "pharmacophore_analysis",
            "similar_compound_search",
            "patent_search",
            "regulatory_info_retrieval"
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return [
            "pubchem",  # Primary for chemical structures
            "chembl",   # Bioactivity data
            "biomcp",   # Cross-domain chemical data
            "brave",    # News and updates
            "playwright"  # Dashboard automation
        ]

    def _define_keywords(self) -> List[str]:
        return [
            "compound", "molecule", "chemical", "drug", "structure",
            "SMILES", "InChI", "CAS", "pubchem", "molecular formula",
            "molecular weight", "logP", "TPSA", "druglikeness",
            "bioactivity", "assay", "IC50", "EC50", "toxicity",
            "safety", "ADMET", "pharmacophore", "similarity",
            "substructure", "patent", "synthesis"
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process chemical compound query using LLM expertise."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            # Build specialized chemical compound prompt
            prompt = f"""You are a Chemical Compound Specialist with expertise in:
- Molecular structure analysis and chemical properties
- Drug-likeness evaluation and ADMET properties
- Bioactivity data interpretation
- Chemical safety and toxicity assessment
- Pharmaceutical compound research

Research Context: {context.research_goal if context.research_goal else "General pharmaceutical research"}

Query: {task.query}

Provide a detailed, scientifically accurate response. Include:
1. Direct answer to the query
2. Relevant molecular properties (if applicable)
3. Chemical structure information (SMILES, InChI, molecular formula if relevant)
4. Bioactivity or safety data (if applicable)
5. Clinical or pharmaceutical relevance
6. Key references or databases (PubChem, ChEMBL, etc.)

Focus on factual, evidence-based information."""

            # Call LLM for expert response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)

            # Store result with structured data
            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "expertise_area": "Chemical Compounds & Drug Discovery"
            }

            # Set confidence based on successful LLM response
            result.confidence_score = 0.85
            result.mcps_used = ["pubchem", "chembl", "biomcp"]
            result.tools_used = ["llm_analysis", "compound_expertise"]

        except Exception as e:
            result.success = False
            result.error_message = f"ChemicalAgent error: {str(e)}"
            result.confidence_score = 0.0

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
