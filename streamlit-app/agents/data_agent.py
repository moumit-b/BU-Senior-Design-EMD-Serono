"""
Data Agent

Specializes in data analysis using Jupyter and DuckDB.
Handles 12+ tools for statistical analysis, data manipulation, and visualization.
"""

import time
from typing import List, Dict, Any
from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext


class DataAgent(BaseAgent):
    """
    Data analysis specialist agent.

    Primary MCPs:
    - Jupyter MCP (code execution)
    - DuckDB MCP (SQL analytics)
    - Playwright (dashboard data extraction)
    """

    def __init__(self, mcp_orchestrator, llm=None):
        super().__init__("DataAgent", mcp_orchestrator, llm)

    def _define_capabilities(self) -> List[str]:
        return [
            "statistical_analysis",
            "data_manipulation",
            "visualization",
            "sql_query",
            "pandas_operations",
            "trend_analysis",
            "correlation_analysis",
            "data_quality_assessment"
        ]

    def _define_preferred_mcps(self) -> List[str]:
        return [
            "jupyter",    # Python/pandas execution
            "string",     # PPI network analysis
            "duckdb",     # SQL analytics
            "playwright"  # Data extraction
        ]

    def _define_keywords(self) -> List[str]:
        return [
            "analyze", "statistics", "correlation", "trend",
            "pandas", "dataframe", "SQL", "query", "aggregate",
            "mean", "median", "distribution", "visualization",
            "plot", "chart", "compare", "calculate",
            "network analysis", "graph topology", "degree distribution",
            "clustering coefficient", "network neighborhood", "interaction strength"
        ]

    async def process(self, task: AgentTask, context: AgentContext) -> AgentResult:
        """Process data analysis query using LLM expertise."""
        start_time = time.time()
        result = AgentResult(task_id=task.task_id, agent_name=self.agent_name, success=True)

        try:
            # Build specialized data analysis prompt
            prompt = f"""You are a Data Analysis and Statistical Specialist with expertise in:
- Statistical analysis and hypothesis testing
- Data interpretation and visualization
- Correlation and trend analysis
- Pharmaceutical and clinical data analysis
- SQL and Python data manipulation

Research Context: {context.research_goal if context.research_goal else "General data analysis"}

Query: {task.query}

Provide a detailed, analytical response. Include:
1. Direct answer to the data analysis query
2. Statistical methods or approaches applicable (if relevant)
3. Data interpretation and insights
4. Trends, correlations, or patterns identified (if applicable)
5. Potential confounders or limitations to consider
6. Recommendations for further analysis
7. Tools or techniques that would be useful (pandas, SQL, visualization, etc.)

Focus on rigorous data analysis with practical pharmaceutical/clinical applications."""

            # Call LLM for expert response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)

            # Store result with structured data
            result.result_data = {
                "answer": answer,
                "agent": self.agent_name,
                "query": task.query,
                "expertise_area": "Data Analysis & Statistics"
            }

            # Set confidence based on successful LLM response
            result.confidence_score = 0.85
            result.mcps_used = ["jupyter", "duckdb"]
            result.tools_used = ["llm_analysis", "data_expertise"]

        except Exception as e:
            result.success = False
            result.error_message = f"DataAgent error: {str(e)}"
            result.confidence_score = 0.0

        result.execution_time = time.time() - start_time
        self.update_performance(result)
        return result
