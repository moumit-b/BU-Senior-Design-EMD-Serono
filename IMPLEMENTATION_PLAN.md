# Multi-Agent & MCP Orchestration Implementation Plan

## Overview

This document provides a detailed, phased implementation plan for building the dual-layer orchestration system:
1. **Agent Orchestration Layer** - Coordinates specialized agents
2. **MCP Orchestration Layer** - Manages MCP server communication

---

## Implementation Phases

### Phase 1: Foundation & Infrastructure (Week 1-2)

**Objectives**: Set up core infrastructure and base classes

#### Week 1: MCP Orchestration Foundation

**Tasks**:
1. Create MCP Orchestrator base structure
   - [ ] `orchestration/mcp_orchestrator.py` - Main orchestrator class
   - [ ] `orchestration/tool_registry.py` - Tool discovery and registry
   - [ ] `orchestration/server_router.py` - Server selection logic
   - [ ] `orchestration/config.py` - Configuration management

2. Implement basic health monitoring
   - [ ] `orchestration/health_monitor.py` - Server health tracking
   - [ ] Passive monitoring (track success/failure rates)
   - [ ] Simple health score calculation

3. Set up basic caching
   - [ ] `orchestration/cache_manager.py` - In-memory cache (L1)
   - [ ] LRU eviction policy
   - [ ] Simple TTL management

**Deliverables**:
- Working MCP orchestrator with basic routing
- Health monitoring dashboard (simple CLI)
- In-memory cache with 5-minute TTL
- Unit tests for core components

**Test Plan**:
```python
# Test basic routing
result = await mcp_orchestrator.execute_tool(
    "pubchem_compound_search",
    {"query": "aspirin"}
)

# Test health monitoring
health = mcp_orchestrator.get_server_health("pubchem")
assert health > 0.8

# Test caching
result1 = await mcp_orchestrator.execute_tool("tool", params)
result2 = await mcp_orchestrator.execute_tool("tool", params)
assert cache_hit_count == 1
```

---

#### Week 2: Agent Orchestration Foundation

**Tasks**:
1. Install and configure LangGraph
   - [ ] Add dependencies: `langgraph`, `langchain-core`
   - [ ] Set up LangGraph state management
   - [ ] Create base state schema

2. Create base agent architecture
   - [ ] `agents/base_agent.py` - Abstract base class for all agents
   - [ ] `agents/agent_state.py` - Shared state definitions
   - [ ] `agents/agent_tools.py` - Common tool utilities

3. Implement Orchestrator Agent (coordinator)
   - [ ] `agents/orchestrator_agent.py` - Main coordinator
   - [ ] Query classification logic
   - [ ] Basic agent routing (rule-based)
   - [ ] Result aggregation

4. Create LangGraph workflow
   - [ ] Define state graph
   - [ ] Implement conditional routing
   - [ ] Set up agent execution nodes

**Deliverables**:
- LangGraph workflow with Orchestrator
- Base agent class with MCP integration
- Simple query classification (single vs. multi-agent)
- Integration tests

**LangGraph State Schema**:
```python
class AgentState(TypedDict):
    # Input
    query: str
    session_id: str

    # Processing
    intent: Dict[str, Any]  # {type, domains, complexity}
    tasks: List[Task]  # Decomposed subtasks
    agent_assignments: Dict[str, str]  # task_id -> agent_name

    # Results
    intermediate_results: Dict[str, Any]  # agent -> result
    final_response: str

    # Metadata
    execution_trace: List[Dict]  # Debugging info
    performance_metrics: Dict[str, float]
```

**Test Plan**:
```python
# Test orchestrator routing
state = {
    "query": "What is the molecular weight of aspirin?",
    "session_id": "test_001"
}
result = await orchestrator.run(state)
assert result["agent_assignments"]["task_1"] == "chemical_agent"

# Test multi-agent coordination
state = {
    "query": "Find trials for BRCA1-targeting drugs",
    "session_id": "test_002"
}
result = await orchestrator.run(state)
assert len(result["agent_assignments"]) >= 2  # Multiple agents
```

---

### Phase 2: Specialized Agents (Week 3-4)

**Objectives**: Implement core specialized agents with MCP integration

#### Week 3: First Set of Agents

**Tasks**:

1. **Chemical Compound Agent**
   - [ ] `agents/chemical_agent.py`
   - [ ] Connect to PubChem MCP (via orchestrator)
   - [ ] Connect to Data Analysis MCP (molecular descriptors)
   - [ ] Implement compound search, property retrieval
   - [ ] Create agent-specific prompt templates

2. **Literature/PubMed Agent**
   - [ ] `agents/literature_agent.py`
   - [ ] Connect to Literature MCP
   - [ ] Connect to BioMCP (PubMed capabilities)
   - [ ] Implement paper search, abstract retrieval
   - [ ] Add summarization capabilities

3. **Clinical Trials Agent**
   - [ ] `agents/clinical_agent.py`
   - [ ] Connect to BioMCP (clinical trials)
   - [ ] Connect to Web Knowledge MCP
   - [ ] Implement trial search by condition/drug
   - [ ] Add filtering and ranking logic

**Agent Template**:
```python
class ChemicalAgent(BaseAgent):
    def __init__(self, mcp_orchestrator: MCPOrchestrator):
        super().__init__(
            name="chemical_agent",
            description="Chemical compound information specialist",
            mcp_orchestrator=mcp_orchestrator
        )
        self.llm = OllamaLLM(model="llama3.2")
        self.tools = self._setup_tools()

    def _setup_tools(self):
        """Define MCP tools this agent can use"""
        return [
            "pubchem_compound_search",
            "pubchem_compound_properties",
            "calculate_molecular_descriptors"
        ]

    async def execute(self, task: Task) -> AgentResult:
        """Execute agent task"""
        # Use ReAct-style reasoning
        # Call MCP tools via orchestrator
        # Return structured result
        pass
```

**Deliverables**:
- 3 working specialized agents
- Agent-specific test suites
- Integration with MCP orchestrator
- Example queries for each agent

**Test Queries**:
```python
# Chemical Agent
test_queries = [
    "What is the molecular formula of ibuprofen?",
    "Calculate molecular weight of caffeine",
    "Find compounds similar to aspirin"
]

# Literature Agent
test_queries = [
    "Find recent papers on CRISPR",
    "Summarize research on Alzheimer's biomarkers",
    "Who published on immunotherapy in 2024?"
]

# Clinical Trials Agent
test_queries = [
    "Find active trials for multiple sclerosis",
    "Show recruiting trials in Boston",
    "What are endpoints for pembrolizumab trials?"
]
```

---

#### Week 4: Second Set of Agents

**Tasks**:

1. **Data Analysis Agent**
   - [ ] `agents/data_analysis_agent.py`
   - [ ] Connect to Data Analysis MCP
   - [ ] Implement statistical calculations
   - [ ] Add sequence analysis capabilities

2. **Gene/Protein Agent**
   - [ ] `agents/gene_protein_agent.py`
   - [ ] Connect to BioMCP (genes, variants)
   - [ ] Connect to Web Knowledge MCP
   - [ ] Implement gene lookup, variant search
   - [ ] Add pathway information retrieval

3. Agent Integration & Testing
   - [ ] Full integration test suite
   - [ ] Performance benchmarking
   - [ ] Error handling validation

**Deliverables**:
- Complete set of 5 specialized agents
- Comprehensive test coverage (>80%)
- Performance benchmarks
- Agent capability matrix

---

### Phase 3: Advanced Orchestration (Week 5)

**Objectives**: Implement intelligent routing and multi-agent collaboration

**Tasks**:

1. **Query Classification & Intent Detection**
   - [ ] `orchestration/query_classifier.py`
   - [ ] NLP-based intent detection
   - [ ] Domain classification (chemical, clinical, literature, etc.)
   - [ ] Complexity assessment (simple, medium, complex)

2. **Task Decomposition**
   - [ ] `orchestration/task_planner.py`
   - [ ] Break complex queries into subtasks
   - [ ] Identify dependencies between tasks
   - [ ] Determine parallel vs. sequential execution

3. **Agent Selection Logic**
   - [ ] `orchestration/agent_selector.py`
   - [ ] Capability-based matching
   - [ ] Load balancing across agents
   - [ ] Fallback strategies

4. **Result Synthesis**
   - [ ] `orchestration/result_synthesizer.py`
   - [ ] Combine results from multiple agents
   - [ ] Format coherent responses
   - [ ] Add citations and metadata

**Query Classifier Implementation**:
```python
class QueryClassifier:
    def __init__(self, llm):
        self.llm = llm

    async def classify(self, query: str) -> QueryIntent:
        """Classify query intent and requirements"""

        prompt = f"""Analyze this query and extract:
        1. Primary domain (chemical, literature, clinical, gene, data)
        2. Secondary domains (if any)
        3. Query type (lookup, search, analysis, comparison)
        4. Complexity (simple, medium, complex)
        5. Required agents

        Query: {query}

        Response format (JSON):
        {{
            "primary_domain": "...",
            "secondary_domains": [...],
            "query_type": "...",
            "complexity": "...",
            "required_agents": [...],
            "reasoning": "..."
        }}
        """

        response = await self.llm.ainvoke(prompt)
        return QueryIntent.parse(response)
```

**Task Decomposition Example**:
```python
# Query: "Find clinical trials for drugs targeting BRCA1 mutations"

decomposed_tasks = [
    Task(
        id="task_1",
        description="Get BRCA1 gene information and mutations",
        agent="gene_protein_agent",
        dependencies=[],
        priority=1
    ),
    Task(
        id="task_2",
        description="Find drugs targeting BRCA1",
        agent="chemical_agent",
        dependencies=["task_1"],
        priority=2
    ),
    Task(
        id="task_3",
        description="Search clinical trials for identified drugs",
        agent="clinical_agent",
        dependencies=["task_2"],
        priority=3
    )
]
```

**Deliverables**:
- Working query classifier (>90% accuracy on test set)
- Task decomposition for complex queries
- Multi-agent coordination workflows
- Result synthesis with proper attribution

---

### Phase 4: MCP Orchestration Enhancement (Week 6)

**Objectives**: Add advanced MCP features (failover, advanced caching, monitoring)

**Tasks**:

1. **Failover & Retry Logic**
   - [ ] `orchestration/failover_handler.py`
   - [ ] Implement exponential backoff
   - [ ] Circuit breaker pattern
   - [ ] Backup server configuration

2. **Advanced Caching**
   - [ ] Add Redis cache (L2)
   - [ ] Implement semantic cache key generation
   - [ ] Add cache warming strategies
   - [ ] Implement cache invalidation

3. **Load Balancing**
   - [ ] `orchestration/load_balancer.py`
   - [ ] Implement multiple strategies (round-robin, least-loaded, hybrid)
   - [ ] Track server load metrics
   - [ ] Dynamic strategy selection

4. **Monitoring & Metrics**
   - [ ] `orchestration/metrics_collector.py`
   - [ ] Prometheus integration
   - [ ] Custom metrics dashboard
   - [ ] Alerting rules

**Failover Configuration**:
```yaml
failover:
  tool_mappings:
    compound_search:
      primary: "pubchem"
      backup: ["web_knowledge"]
      max_attempts: 3

    literature_search:
      primary: "literature"
      backup: ["biomcp"]
      max_attempts: 2

  retry_policy:
    base_delay: 1.0
    max_delay: 30.0
    exponential_base: 2.0
```

**Deliverables**:
- Automatic failover with 99% success rate
- Redis cache with 60%+ hit rate
- Load balancer with multiple strategies
- Metrics dashboard showing real-time stats

---

### Phase 5: UI/UX Enhancement (Week 7)

**Objectives**: Update Streamlit UI to showcase multi-agent capabilities

**Tasks**:

1. **Multi-Agent Visualization**
   - [ ] Agent activity timeline
   - [ ] Task decomposition view
   - [ ] Intermediate results display
   - [ ] Agent reasoning trace

2. **Enhanced Query Interface**
   - [ ] Query suggestions based on capabilities
   - [ ] Domain selector (optional override)
   - [ ] Advanced options (force cache refresh, select agents)

3. **Results Presentation**
   - [ ] Tabbed results by agent
   - [ ] Comparison view for multi-source results
   - [ ] Citation and metadata display
   - [ ] Export options (JSON, PDF)

4. **Performance Dashboard**
   - [ ] Real-time metrics
   - [ ] Agent performance stats
   - [ ] MCP server health
   - [ ] Cache hit rates

**UI Mockup Structure**:
```
┌─────────────────────────────────────────────────────────────┐
│  Team 2 Multi-Agent MCP System                              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Query: Find trials for BRCA1-targeting drugs        │  │
│  │  [Send] [Advanced Options ▼]                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Agent Execution Timeline:                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  [Gene Agent]────────■ (2.3s)                        │  │
│  │       └─> [Chemical Agent]────■ (3.1s)               │  │
│  │             └─> [Clinical Agent]────■ (4.5s)         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Results:                                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  [Gene Info] [Drug List] [Clinical Trials] [Summary] │  │
│  │                                                       │  │
│  │  BRCA1 Information (Gene Agent):                     │  │
│  │  - Function: DNA repair, tumor suppressor            │  │
│  │  - Common mutations: 185delAG, 5382insC              │  │
│  │                                                       │  │
│  │  Targeting Drugs (Chemical Agent):                   │  │
│  │  1. Olaparib (PubChem CID: 23725625)                 │  │
│  │  2. Rucaparib (PubChem CID: 9931954)                 │  │
│  │                                                       │  │
│  │  Clinical Trials (Clinical Agent):                   │  │
│  │  Found 15 active trials:                             │  │
│  │  • NCT03544607 - Olaparib in BRCA1+ breast cancer   │  │
│  │  • NCT02282020 - Rucaparib maintenance therapy      │  │
│  │  [View All Trials]                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Sidebar:                                                   │
│  ┌─────────────────┐                                        │
│  │ System Status   │                                        │
│  │ ● 5/5 Agents OK │                                        │
│  │ ● 5/5 MCPs OK   │                                        │
│  │ Cache: 67% hit  │                                        │
│  │ Avg time: 3.2s  │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

**Streamlit Code Structure**:
```python
# app.py (enhanced)

def display_agent_timeline(execution_trace):
    """Visualize agent execution timeline"""
    fig = px.timeline(
        execution_trace,
        x_start="start_time",
        x_end="end_time",
        y="agent_name",
        color="status"
    )
    st.plotly_chart(fig)

def display_multi_agent_results(results):
    """Show results from multiple agents"""
    tabs = st.tabs([r["agent_name"] for r in results])
    for tab, result in zip(tabs, results):
        with tab:
            st.markdown(f"**{result['agent_name']}**")
            st.json(result["data"])
            st.caption(f"Completed in {result['duration']:.2f}s")
```

**Deliverables**:
- Enhanced Streamlit UI with agent visualization
- Interactive agent timeline
- Tabbed results view
- Performance metrics sidebar
- Query history with replay

---

### Phase 6: Testing, Optimization & Documentation (Week 8)

**Objectives**: Finalize system, optimize performance, complete documentation

**Tasks**:

1. **Comprehensive Testing**
   - [ ] End-to-end integration tests
   - [ ] Load testing (concurrent users)
   - [ ] Failure scenario testing
   - [ ] Performance regression tests

2. **Performance Optimization**
   - [ ] Profile bottlenecks
   - [ ] Optimize MCP connection pooling
   - [ ] Tune cache TTLs
   - [ ] Parallel execution optimization

3. **Documentation**
   - [ ] User guide with examples
   - [ ] Agent development guide
   - [ ] MCP server integration guide
   - [ ] API documentation
   - [ ] Deployment guide

4. **Production Readiness**
   - [ ] Error handling audit
   - [ ] Logging standardization
   - [ ] Configuration management
   - [ ] Security review

**Test Scenarios**:
```python
# End-to-end tests
test_cases = [
    {
        "name": "Simple single-agent query",
        "query": "What is the molecular weight of aspirin?",
        "expected_agents": ["chemical_agent"],
        "max_time": 5.0
    },
    {
        "name": "Complex multi-agent query",
        "query": "Find trials for BRCA1-targeting drugs",
        "expected_agents": ["gene_protein_agent", "chemical_agent", "clinical_agent"],
        "max_time": 15.0
    },
    {
        "name": "Literature search",
        "query": "Recent papers on immunotherapy for melanoma",
        "expected_agents": ["literature_agent"],
        "max_time": 10.0
    }
]

# Load testing
async def load_test():
    """Simulate 10 concurrent users"""
    queries = [generate_random_query() for _ in range(10)]
    results = await asyncio.gather(*[
        orchestrator.run(query) for query in queries
    ])
    assert all(r["status"] == "success" for r in results)
```

**Performance Targets**:
- Single-agent queries: < 5s average
- Multi-agent queries: < 15s average
- Cache hit rate: > 60%
- System uptime: > 99%
- Concurrent users: 10+ without degradation

**Deliverables**:
- Complete test suite (unit, integration, load)
- Optimized system meeting performance targets
- Comprehensive documentation
- Production deployment guide

---

## Project File Structure

```
BU-Senior-Design-EMD-Serono/
│
├── streamlit-app/
│   ├── app.py                          # Enhanced Streamlit UI
│   ├── config.py                       # Configuration
│   ├── requirements.txt                # Dependencies
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py              # Base agent class
│   │   ├── agent_state.py             # State definitions
│   │   ├── orchestrator_agent.py      # Main coordinator
│   │   ├── chemical_agent.py          # Chemical compound specialist
│   │   ├── literature_agent.py        # Literature specialist
│   │   ├── clinical_agent.py          # Clinical trials specialist
│   │   ├── data_analysis_agent.py     # Data analysis specialist
│   │   └── gene_protein_agent.py      # Gene/protein specialist
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── mcp_orchestrator.py        # MCP orchestrator core
│   │   ├── tool_registry.py           # Tool discovery
│   │   ├── server_router.py           # Server selection
│   │   ├── health_monitor.py          # Health monitoring
│   │   ├── cache_manager.py           # Multi-level caching
│   │   ├── load_balancer.py           # Load balancing
│   │   ├── failover_handler.py        # Failover & retry
│   │   ├── query_classifier.py        # Query classification
│   │   ├── task_planner.py            # Task decomposition
│   │   ├── agent_selector.py          # Agent selection
│   │   ├── result_synthesizer.py      # Result aggregation
│   │   └── metrics_collector.py       # Metrics & monitoring
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── components.py              # Reusable UI components
│   │   ├── visualizations.py          # Charts & graphs
│   │   └── formatters.py              # Result formatters
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_agents.py
│   │   │   ├── test_orchestration.py
│   │   │   └── test_mcp_layer.py
│   │   ├── integration/
│   │   │   ├── test_end_to_end.py
│   │   │   └── test_multi_agent.py
│   │   └── load/
│   │       └── test_performance.py
│   │
│   └── utils/
│       ├── logging_config.py
│       ├── error_handlers.py
│       └── validators.py
│
├── servers/                            # MCP servers
│   ├── pubchem/
│   ├── biomcp/
│   ├── literature/
│   ├── data_analysis/
│   └── web_knowledge/
│
├── config/
│   ├── mcp_config.yaml                # MCP server configs
│   ├── agent_config.yaml              # Agent configs
│   └── orchestrator_config.yaml       # Orchestration configs
│
├── docs/
│   ├── MULTI_AGENT_ARCHITECTURE.md    # Architecture doc
│   ├── MCP_ORCHESTRATION_LAYER.md     # MCP layer doc
│   ├── IMPLEMENTATION_PLAN.md         # This document
│   ├── USER_GUIDE.md                  # User documentation
│   ├── DEVELOPER_GUIDE.md             # Developer docs
│   └── API_REFERENCE.md               # API documentation
│
└── scripts/
    ├── setup.sh                       # Setup script
    ├── run_tests.sh                   # Test runner
    └── deploy.sh                      # Deployment script
```

---

## Dependencies & Requirements

### Python Packages
```txt
# Core
streamlit>=1.31.0
python>=3.11

# LLM & Agents
langchain>=0.1.0
langchain-core>=0.1.0
langgraph>=0.0.20
langchain-ollama>=0.0.1

# MCP
mcp>=0.1.0

# Data & Utils
pydantic>=2.0.0
asyncio
aiohttp
httpx

# Caching
redis>=5.0.0

# Monitoring
prometheus-client>=0.19.0
loguru>=0.7.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
locust>=2.15.0  # Load testing

# Visualization
plotly>=5.18.0
pandas>=2.1.0
```

### System Requirements
- **Python**: 3.11+
- **Ollama**: Running locally with llama3.2 model
- **Redis**: For L2 caching (optional but recommended)
- **Node.js**: For MCP servers
- **Memory**: 8GB+ RAM recommended
- **CPU**: 4+ cores recommended

---

## Risk Management

### Technical Risks

| Risk                           | Impact | Probability | Mitigation                                    |
|--------------------------------|--------|-------------|-----------------------------------------------|
| LangGraph learning curve       | High   | Medium      | Start with simple workflows, extensive docs   |
| MCP connection stability       | High   | Medium      | Implement robust failover & retry logic       |
| Performance degradation        | Medium | Medium      | Aggressive caching, load testing              |
| Agent coordination complexity  | High   | High        | Start simple, iterate, extensive logging      |
| Ollama model limitations       | Medium | Medium      | Test with multiple models, allow swapping     |

### Operational Risks

| Risk                           | Impact | Probability | Mitigation                                    |
|--------------------------------|--------|-------------|-----------------------------------------------|
| MCP server downtime            | High   | Low         | Health monitoring, automatic failover         |
| Memory leaks from long sessions| Medium | Medium      | Connection pooling, periodic cleanup          |
| Cache invalidation issues      | Low    | Low         | Conservative TTLs, manual refresh option      |
| Concurrent user conflicts      | Low    | Low         | Session isolation, rate limiting              |

---

## Success Criteria

### Functional Requirements
- ✅ Support 5+ specialized agents
- ✅ Handle 15+ distinct query types
- ✅ Automatic query classification (>90% accuracy)
- ✅ Multi-agent collaboration for complex queries
- ✅ Seamless MCP server integration
- ✅ Automatic failover and retry

### Performance Requirements
- ✅ Single-agent query: < 5s average response time
- ✅ Multi-agent query: < 15s average response time
- ✅ Cache hit rate: > 60%
- ✅ System uptime: > 99%
- ✅ Support 10+ concurrent users

### Quality Requirements
- ✅ Test coverage: > 80%
- ✅ Code documentation: > 90%
- ✅ User satisfaction: > 4.5/5
- ✅ Error rate: < 1%

---

## Timeline Summary

| Phase | Duration | Key Deliverables                              |
|-------|----------|-----------------------------------------------|
| 1     | 2 weeks  | MCP & Agent orchestration foundation          |
| 2     | 2 weeks  | 5 specialized agents                          |
| 3     | 1 week   | Advanced orchestration logic                  |
| 4     | 1 week   | MCP enhancements (failover, caching)          |
| 5     | 1 week   | Enhanced UI/UX                                |
| 6     | 1 week   | Testing, optimization, documentation          |
| **Total** | **8 weeks** | **Production-ready multi-agent system**   |

---

## Next Steps

1. **Review & Approval**
   - Review architecture documents
   - Get stakeholder sign-off
   - Prioritize features for MVP

2. **Environment Setup**
   - Set up development environment
   - Install dependencies
   - Configure MCP servers

3. **Kick off Phase 1**
   - Begin Week 1 tasks
   - Set up project structure
   - Initialize Git repository with proper structure

4. **Establish Development Workflow**
   - Set up CI/CD pipeline
   - Define code review process
   - Create issue tracking

**Ready to begin implementation!**
