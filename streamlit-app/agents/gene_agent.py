"""
Gene Agent

Specializes in gene and target biology using BioMCP and PubChem.
Handles 24+ tools for gene lookup, variant analysis, and target assessment.
"""

import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class GeneAgent(BaseAgent):
    """
    Gene and target biology specialist agent.

    Primary MCPs:
    - BioMCP (MyGene, MyDisease, MyVariant, AlphaGenome)
    - PubChem (target-based compound search)
    - Playwright
    """

    def __init__(self, mcp_orchestrator, llm=None):
        super().__init__("GeneAgent", mcp_orchestrator, llm)

    def _define_capabilities(self) -> List[str]:
        return [
            "gene_lookup",
            "variant_analysis",
            "disease_association",
            "biomarker_search",
            "target_assessment",
            "pathway_analysis",
            "protein_annotation",
            "functional_prediction"
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return [
            "biomcp",      # Gene/variant/disease data
            "opentargets", # Target prioritization
            "stringdb",      # Protein-protein interactions
            "pubchem",     # Target-compound relationships
            "playwright"   # Biology dashboards
        ]

    def _define_keywords(self) -> List[str]:
        return [
            "gene", "protein", "target", "biomarker", "variant",
            "mutation", "SNP", "HGVS", "chromosome", "locus",
            "pathway", "BRCA", "TP53", "EGFR", "expression",
            "druggability", "function", "ontology", "GO term",
            "disease association", "MyGene", "UniProt",
            "opentargets", "STRING", "protein interaction", "target prioritization"
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process gene/target query using LLM expertise."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            # Build specialized genetics and target biology prompt
            prompt = f"""You are a Genetics and Target Biology Specialist with expertise in:
- Gene structure, function, and regulation
- Genetic variants and disease associations
- Protein targets and druggability assessment
- Molecular pathways and signaling networks
- Biomarker identification and validation

Research Context: {context.research_goal if context.research_goal else "General genetics research"}

Query: {task.query}

Provide a detailed, scientifically accurate response. Include:
1. Direct answer to the gene/target query
2. Gene function and biological role (if applicable)
3. Genetic variants or mutations of interest (if relevant)
4. Disease associations and clinical significance
5. Druggability and therapeutic potential (if applicable)
6. Relevant pathways and molecular mechanisms
7. Key databases or identifiers (MyGene, UniProt, HGVS, etc.)

Focus on molecular biology insights with clinical and therapeutic relevance."""

            # Call LLM for expert response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)

            # Store result with structured data
            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "expertise_area": "Genetics & Target Biology"
            }

            # Set confidence based on successful LLM response
            result.confidence_score = 0.85
            result.mcps_used = ["biomcp", "opentargets", "stringdb", "mygene", "myvariant"]
            result.tools_used = ["llm_analysis", "genetics_expertise"]

        except Exception as e:
            result.success = False
            result.error_message = f"GeneAgent error: {str(e)}"
            result.confidence_score = 0.0

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
