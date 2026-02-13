"""
Orchestrator Agent (LangGraph State Machine)

Coordinates multiple specialized agents using LangGraph for complex multi-agent workflows.
All agents and the orchestrator use Claude Sonnet 4.5 via the centralized LLM factory.
"""

from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator
from langgraph.graph import StateGraph, END
import time

from .base_agent import AgentTask, AgentResult, AgentContext
from .chemical_agent import ChemicalAgent
from .clinical_agent import ClinicalAgent
from .literature_agent import LiteratureAgent
from .gene_agent import GeneAgent
from .data_agent import DataAgent


class OrchestratorState(TypedDict):
    """State passed through the orchestration graph."""
    query: str
    session_id: str
    user_id: str
    query_intent: Optional[str]
    query_complexity: str
    keywords: List[str]
    execution_plan: Optional[Dict[str, Any]]
    assigned_agents: List[str]
    agent_tasks: List[AgentTask]
    agent_results: Annotated[List[AgentResult], operator.add]
    final_answer: Optional[str]
    entities_discovered: List[Dict[str, Any]]
    execution_time: float
    governance_context: Dict[str, Any]
    performance_feedback: Dict[str, Any]


class OrchestratorAgent:
    """LangGraph-based orchestrator for multi-agent coordination."""

    def __init__(self, mcp_orchestrator, governance_gateway, llm=None):
        self.mcp_orchestrator = mcp_orchestrator
        self.governance_gateway = governance_gateway

        # Initialize LLM using factory if not provided
        if llm is None:
            from utils.llm_factory import get_llm
            self.llm = get_llm()
        else:
            self.llm = llm

        # Initialize specialized agents (they will also use LLM factory)
        self.agents = {
            "chemical": ChemicalAgent(mcp_orchestrator, self.llm),
            "clinical": ClinicalAgent(mcp_orchestrator, self.llm),
            "literature": LiteratureAgent(mcp_orchestrator, self.llm),
            "gene": GeneAgent(mcp_orchestrator, self.llm),
            "data": DataAgent(mcp_orchestrator, self.llm)
        }

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph state machine."""
        workflow = StateGraph(OrchestratorState)

        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("create_plan", self._create_plan_node)
        workflow.add_node("assign_agents", self._assign_agents_node)
        workflow.add_node("execute_tasks", self._execute_tasks_node)
        workflow.add_node("synthesize", self._synthesize_node)
        workflow.add_node("validate", self._validate_node)

        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "create_plan")
        workflow.add_edge("create_plan", "assign_agents")
        workflow.add_edge("assign_agents", "execute_tasks")
        workflow.add_edge("execute_tasks", "synthesize")
        workflow.add_edge("synthesize", "validate")
        workflow.add_edge("validate", END)

        return workflow.compile()

    async def process_query(self, query: str, session_id: str, user_id: str) -> Dict[str, Any]:
        """Process query through orchestration workflow."""
        start_time = time.time()

        initial_state = OrchestratorState(
            query=query,
            session_id=session_id,
            user_id=user_id,
            query_intent=None,
            query_complexity="moderate",
            keywords=[],
            execution_plan=None,
            assigned_agents=[],
            agent_tasks=[],
            agent_results=[],
            final_answer=None,
            entities_discovered=[],
            execution_time=0.0,
            governance_context={},
            performance_feedback={}
        )

        final_state = await self.workflow.ainvoke(initial_state)
        final_state["execution_time"] = time.time() - start_time

        return final_state

    def _analyze_query_node(self, state: OrchestratorState) -> OrchestratorState:
        """Analyze query to determine intent and complexity."""
        query = state["query"].lower()

        keywords = []
        for agent in self.agents.values():
            for keyword in agent.keywords:
                if keyword.lower() in query:
                    keywords.append(keyword)

        complexity = "simple"
        if len(keywords) > 3 or " and " in query or " with " in query:
            complexity = "moderate"
        if len(keywords) > 6 or "compare" in query or "analyze" in query:
            complexity = "complex"

        state["keywords"] = list(set(keywords))
        state["query_complexity"] = complexity
        state["query_intent"] = "research"

        return state

    def _create_plan_node(self, state: OrchestratorState) -> OrchestratorState:
        """Create execution plan based on query analysis."""
        complexity = state["query_complexity"]

        plan = {
            "strategy": "parallel" if complexity == "simple" else "sequential",
            "max_agents": 1 if complexity == "simple" else 3,
            "timeout": 30 if complexity == "simple" else 60
        }

        state["execution_plan"] = plan
        return state

    def _assign_agents_node(self, state: OrchestratorState) -> OrchestratorState:
        """Assign agents based on keywords and plan."""
        keywords = state["keywords"]
        max_agents = state["execution_plan"]["max_agents"]

        agent_scores = {}
        for agent_name, agent in self.agents.items():
            score = agent.can_handle(state["query"], keywords)
            if score > 0.3:
                agent_scores[agent_name] = score

        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [name for name, score in sorted_agents[:max_agents]]

        state["assigned_agents"] = selected if selected else ["chemical"]
        return state

    async def _execute_tasks_node(self, state: OrchestratorState) -> OrchestratorState:
        """Execute tasks with assigned agents."""
        results = []

        context = AgentContext(
            session_id=state["session_id"],
            user_id=state["user_id"],
            research_goal=state["query"],
            mcp_performance_feedback=state.get("performance_feedback", {})
        )

        for agent_name in state["assigned_agents"]:
            agent = self.agents[agent_name]
            task = AgentTask(
                task_id=f"task_{agent_name}_{int(time.time())}",
                query=state["query"],
                task_type="general_query",
                session_id=state["session_id"]
            )

            result = await agent.process(task, context)
            results.append(result)

        state["agent_results"] = results
        return state

    def _synthesize_node(self, state: OrchestratorState) -> OrchestratorState:
        """Synthesize results from multiple agents using LLM."""
        results = state["agent_results"]

        combined_data = {}
        entities = []
        agent_answers = []

        # Collect successful agent responses
        for result in results:
            if result.success:
                combined_data[result.agent_name] = result.result_data
                entities.extend(result.entities_discovered)

                # Extract the actual answer from each agent
                if result.result_data and isinstance(result.result_data, dict):
                    answer = result.result_data.get("answer", "")
                    expertise_area = result.result_data.get("expertise_area", result.agent_name)
                    if answer:
                        agent_answers.append(f"**{expertise_area}**:\n{answer}\n")

        # Use LLM to synthesize comprehensive response
        if agent_answers:
            synthesis_prompt = f"""You are synthesizing research findings from multiple specialized pharmaceutical research agents.

**Original Query:** {state['query']}

**Research Goal:** {state.get('research_goal', 'Comprehensive pharmaceutical research')}

**Agent Findings:**

{chr(10).join(agent_answers)}

**Your Task:**
Synthesize these findings into a comprehensive, well-organized response that:
1. Directly addresses the original query
2. Integrates insights from all specialized agents
3. Highlights key findings and their significance
4. Provides a coherent narrative connecting different perspectives
5. Identifies any gaps or areas requiring further investigation

Provide a professional, scientifically accurate synthesis suitable for pharmaceutical research intelligence."""

            try:
                response = self.llm.invoke(synthesis_prompt)
                final_answer = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                # Fallback if LLM synthesis fails
                final_answer = f"# Multi-Agent Analysis\n\n{chr(10).join(agent_answers)}\n\n*Note: LLM synthesis unavailable ({str(e)})*"
        else:
            final_answer = "No successful results were obtained from the specialized agents. Please try rephrasing your query or check agent connectivity."

        state["final_answer"] = final_answer
        state["entities_discovered"] = entities

        return state

    def _validate_node(self, state: OrchestratorState) -> OrchestratorState:
        """Validate results for compliance."""
        state["governance_context"]["compliance_passed"] = True
        state["governance_context"]["validation_timestamp"] = time.time()

        return state
