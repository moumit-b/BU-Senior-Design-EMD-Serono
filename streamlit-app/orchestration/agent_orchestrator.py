"""
Agent Orchestrator - Multi-Agent Coordination

This is the TOP LAYER of dual orchestration that handles:
- Query analysis and task decomposition
- Agent selection and routing
- Multi-agent workflow execution
- Result synthesis
- Learning from MCP performance feedback (Novel Feature 1)
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re

from models.performance import PerformanceFeedback
from .mcp_orchestrator import MCPOrchestrator
from .performance_kb import PerformanceKnowledgeBase
from .tool_composer import ToolComposer
from .session_manager import SessionManager


@dataclass
class QueryPlan:
    """Plan for executing a query."""
    original_query: str
    query_type: str  # 'simple', 'complex_sequential', 'complex_parallel'
    tasks: List[Dict[str, Any]]  # List of tasks to execute
    required_agents: List[str]  # Agent IDs needed
    keywords: List[str]  # Extracted keywords
    confidence: float  # Confidence in the plan


class AgentOrchestrator:
    """
    Multi-Agent Orchestrator

    Novel Features:
    1. Learns from MCP feedback to improve agent-MCP matching
    2. Uses performance KB to route queries optimally
    3. Creates and reuses composed tools
    """

    def __init__(
        self,
        mcp_orchestrator: MCPOrchestrator,
        performance_kb: PerformanceKnowledgeBase,
        tool_composer: ToolComposer,
        session_manager: SessionManager
    ):
        self.mcp_orchestrator = mcp_orchestrator
        self.performance_kb = performance_kb
        self.tool_composer = tool_composer
        self.session_manager = session_manager

        # Agent preferences (learned over time)
        self.agent_mcp_preferences: Dict[str, Dict[str, float]] = {
            'chemical': {},
            'literature': {},
            'clinical': {},
            'data': {},
            'gene': {}
        }

    async def execute_query(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a query using the dual orchestration system.

        Args:
            query: User query
            session_id: Optional session ID for context

        Returns:
            Dictionary with results and metadata
        """
        # Step 1: Analyze query and create plan
        plan = self.analyze_query(query, session_id)

        # Step 2: Check if we have a composed tool for this
        composed_tool = self.tool_composer.find_matching_tool(query)
        if composed_tool:
            print(f"✓ Found composed tool: {composed_tool.name}")
            result = await self._execute_composed_tool(composed_tool, plan)
            return {
                'output': result,
                'method': 'composed_tool',
                'tool_used': composed_tool.name,
                'plan': plan
            }

        # Step 3: Execute plan with agents
        if plan.query_type == 'simple':
            result = await self._execute_simple_query(plan)
        elif plan.query_type == 'complex_sequential':
            result = await self._execute_sequential_workflow(plan)
        else:  # complex_parallel
            result = await self._execute_parallel_workflow(plan)

        # Step 4: Learn from execution
        self._update_learning(plan, result)

        # Step 5: Consider creating composed tool for future
        if plan.query_type != 'simple' and result.get('success', False):
            await self._maybe_create_composed_tool(plan, result)

        return result

    def analyze_query(self, query: str, session_id: Optional[str] = None) -> QueryPlan:
        """
        Analyze query and create execution plan.

        Novel Feature: Uses session context if available.
        """
        query_lower = query.lower()

        # Extract keywords
        keywords = self._extract_keywords(query)

        # Determine query type and required agents
        required_agents = []
        tasks = []

        # Chemical queries
        if any(kw in query_lower for kw in ['molecular', 'compound', 'chemical', 'drug', 'molecule', 'smiles', 'formula']):
            required_agents.append('chemical')
            tasks.append({
                'agent': 'chemical',
                'action': 'extract_compound_info',
                'input': query,
                'keywords': keywords
            })

        # Literature queries
        if any(kw in query_lower for kw in ['paper', 'publication', 'research', 'study', 'pubmed']):
            required_agents.append('literature')
            tasks.append({
                'agent': 'literature',
                'action': 'search_literature',
                'input': query,
                'keywords': keywords
            })

        # Clinical trial queries
        if any(kw in query_lower for kw in ['trial', 'clinical', 'phase', 'enrollment', 'nct']):
            required_agents.append('clinical')
            tasks.append({
                'agent': 'clinical',
                'action': 'find_trials',
                'input': query,
                'keywords': keywords
            })

        # Gene/protein queries
        if any(kw in query_lower for kw in ['gene', 'protein', 'brca', 'dna', 'pathway', 'expression']):
            required_agents.append('gene')
            tasks.append({
                'agent': 'gene',
                'action': 'analyze_gene',
                'input': query,
                'keywords': keywords
            })

        # Determine complexity
        if len(required_agents) == 0:
            # Default to chemical agent for unknown queries
            required_agents = ['chemical']
            tasks = [{'agent': 'chemical', 'action': 'general_query', 'input': query, 'keywords': keywords}]
            query_type = 'simple'
        elif len(required_agents) == 1:
            query_type = 'simple'
        elif self._requires_sequential_execution(query, required_agents):
            query_type = 'complex_sequential'
        else:
            query_type = 'complex_parallel'

        return QueryPlan(
            original_query=query,
            query_type=query_type,
            tasks=tasks,
            required_agents=required_agents,
            keywords=keywords,
            confidence=0.8  # TODO: Implement confidence scoring
        )

    async def _execute_simple_query(self, plan: QueryPlan) -> Dict[str, Any]:
        """Execute a simple single-agent query."""
        task = plan.tasks[0]
        agent_id = task['agent']

        # Get agent's preferred MCPs
        preferred_mcps = self.agent_mcp_preferences.get(agent_id, {})

        # Prepare context for MCP orchestrator
        context = {
            'agent_id': agent_id,
            'query_type': task['action'],
            'keywords': task['keywords']
        }

        # For this demo, we'll simulate calling an MCP tool
        # In a real implementation, we'd determine which tool based on the agent's logic
        tool_name = self._select_tool_for_task(task)
        params = self._extract_params_from_query(task['input'])

        # Call MCP orchestrator
        result, feedback = await self.mcp_orchestrator.route_tool_call(
            tool_name=tool_name,
            params=params,
            context=context
        )

        # Learn from feedback
        self._learn_from_feedback(agent_id, feedback)

        return {
            'output': result,
            'method': 'simple_query',
            'agent': agent_id,
            'feedback': feedback,
            'success': feedback.success
        }

    async def _execute_sequential_workflow(self, plan: QueryPlan) -> Dict[str, Any]:
        """Execute tasks sequentially (each depends on previous)."""
        results = []
        accumulated_context = {}

        for i, task in enumerate(plan.tasks):
            # Pass results from previous tasks as context
            task['previous_results'] = accumulated_context

            result = await self._execute_task(task)
            results.append(result)

            # Accumulate context for next task
            accumulated_context[task['agent']] = result

        # Synthesize results
        final_output = self._synthesize_results(results, plan)

        return {
            'output': final_output,
            'method': 'sequential_workflow',
            'intermediate_results': results,
            'success': all(r.get('success', False) for r in results)
        }

    async def _execute_parallel_workflow(self, plan: QueryPlan) -> Dict[str, Any]:
        """Execute tasks in parallel (independent)."""
        import asyncio

        # Execute all tasks concurrently
        tasks = [self._execute_task(task) for task in plan.tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]

        # Synthesize results
        final_output = self._synthesize_results(valid_results, plan)

        return {
            'output': final_output,
            'method': 'parallel_workflow',
            'intermediate_results': valid_results,
            'success': len(valid_results) > 0
        }

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task."""
        agent_id = task['agent']
        context = {
            'agent_id': agent_id,
            'query_type': task['action'],
            'keywords': task.get('keywords', [])
        }

        tool_name = self._select_tool_for_task(task)
        params = self._extract_params_from_query(task['input'])

        result, feedback = await self.mcp_orchestrator.route_tool_call(
            tool_name=tool_name,
            params=params,
            context=context
        )

        self._learn_from_feedback(agent_id, feedback)

        return {
            'agent': agent_id,
            'result': result,
            'feedback': feedback,
            'success': feedback.success
        }

    async def _execute_composed_tool(
        self,
        composed_tool: Any,
        plan: QueryPlan
    ) -> str:
        """Execute a composed tool workflow."""
        # This would execute the multi-step workflow defined in the composed tool
        # For now, return a placeholder
        return f"Executed composed tool: {composed_tool.name}"

    def _synthesize_results(self, results: List[Dict], plan: QueryPlan) -> str:
        """Synthesize results from multiple agents into final answer."""
        if not results:
            return "No results obtained."

        if len(results) == 1:
            return str(results[0].get('result', 'No result'))

        # Multi-agent synthesis
        synthesis = f"Based on analysis from {len(results)} specialized agents:\n\n"
        for r in results:
            agent = r.get('agent', 'unknown')
            result = r.get('result', 'No result')
            synthesis += f"**{agent.capitalize()} Agent**: {result}\n\n"

        return synthesis

    def _learn_from_feedback(self, agent_id: str, feedback: PerformanceFeedback):
        """
        Learn from MCP feedback to improve agent-MCP matching.

        Novel Feature 1: Bidirectional Learning
        """
        if not feedback.success:
            return

        # Update agent's MCP preferences
        mcp_source = feedback.source
        if mcp_source and mcp_source != 'cache':
            if agent_id not in self.agent_mcp_preferences:
                self.agent_mcp_preferences[agent_id] = {}

            # Increase preference for successful MCP
            current_pref = self.agent_mcp_preferences[agent_id].get(mcp_source, 0.5)
            self.agent_mcp_preferences[agent_id][mcp_source] = min(1.0, current_pref + 0.1)

    def _update_learning(self, plan: QueryPlan, result: Dict[str, Any]):
        """Update performance knowledge base with execution results."""
        # Record successful patterns
        if result.get('success', False):
            self.performance_kb.record_successful_pattern(
                query_type=plan.query_type,
                agents=plan.required_agents,
                keywords=plan.keywords
            )

    async def _maybe_create_composed_tool(
        self,
        plan: QueryPlan,
        result: Dict[str, Any]
    ):
        """
        Consider creating a composed tool for future reuse.

        Novel Feature 2: Dynamic Tool Composition
        """
        # Simple heuristic: if query was complex and successful, consider composing
        if len(plan.tasks) >= 2 and result.get('success', False):
            # This would analyze the workflow and create a composed tool
            # For now, just log the opportunity
            print(f"Opportunity to create composed tool for: {plan.original_query}")

    # Helper methods

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query."""
        # Simple keyword extraction (could be enhanced with NLP)
        stopwords = {'what', 'is', 'the', 'a', 'an', 'how', 'find', 'show', 'tell', 'me', 'about'}
        words = re.findall(r'\w+', query.lower())
        return [w for w in words if w not in stopwords and len(w) > 3]

    def _requires_sequential_execution(self, query: str, agents: List[str]) -> bool:
        """Determine if agents must run sequentially or can run in parallel."""
        # Heuristic: certain combinations require sequential execution
        if 'gene' in agents and 'chemical' in agents:
            # Gene info often needed before finding drugs
            return True
        if 'chemical' in agents and 'clinical' in agents:
            # Drug info needed before finding trials
            return True
        return False

    def _select_tool_for_task(self, task: Dict[str, Any]) -> str:
        """Select MCP tool based on task."""
        agent = task['agent']
        action = task['action']

        # Map agent actions to tools (simplified mapping)
        tool_map = {
            'chemical': 'get_compound_properties',
            'literature': 'search_publications',
            'clinical': 'search_trials',
            'gene': 'get_gene_info',
            'data': 'analyze_data'
        }

        return tool_map.get(agent, 'unknown_tool')

    def _extract_params_from_query(self, query: str) -> Dict[str, Any]:
        """Extract parameters from natural language query."""
        # Very simple extraction - in practice, would use NLP
        # Look for quoted terms or capitalized terms as potential parameters
        import re

        # Try to find compound names (capitalized words or quoted text)
        quoted = re.findall(r'"([^"]+)"', query)
        if quoted:
            return {'name': quoted[0]}

        # Try to find capitalized words (potential compound/gene names)
        words = query.split()
        capitalized = [w for w in words if w[0].isupper() and len(w) > 1]
        if capitalized:
            return {'name': capitalized[0]}

        # Default: use whole query
        return {'query': query}

    def get_agent_insights(self) -> Dict[str, Any]:
        """Get insights about agent performance and preferences."""
        return {
            'agent_mcp_preferences': self.agent_mcp_preferences,
            'performance_patterns': self.performance_kb.get_patterns()
        }
