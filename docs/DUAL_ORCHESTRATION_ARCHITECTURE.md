# Dual Orchestration Architecture - Technical Specification

**Status:** Core Features Implemented ✅
**Last Updated:** 2025-11-26
**Phase:** Production Demo Ready

---

## Executive Summary

This document details the **dual orchestration architecture** that combines Agent Orchestration with MCP Orchestration to enable emergent research intelligence capabilities.

### Key Novel Features

1. **Bidirectional Learning**: Agents and MCPs teach each other through performance feedback
2. **Dynamic Tool Composition**: Agents create new tools by composing MCP workflows
3. **Research Session Memory**: System maintains context across multi-turn collaborative sessions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI LAYER                        │
│   Chat | Agent Timeline | Performance Dashboard | Session    │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│           AGENT ORCHESTRATION LAYER                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Orchestrator Agent (LangGraph)                      │   │
│  │  - Query analysis & task decomposition               │   │
│  │  - Agent selection & coordination                    │   │
│  │  - Result synthesis                                  │   │
│  │  - NOVEL: Learns from MCP performance feedback       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐   │
│  │ Chemical │Literature│ Clinical │   Data   │   Gene   │   │
│  │  Agent   │  Agent   │  Agent   │  Agent   │  Agent   │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘   │
│                                                              │
│  NOVEL FEATURES:                                             │
│  • Tool Composition Registry (agents create new tools)       │
│  • Cross-Agent Learning (share successful patterns)          │
│  • Session Context Manager (research memory)                 │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│           MCP ORCHESTRATION LAYER                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MCP Orchestrator                                    │   │
│  │  - Intelligent routing (learns best MCP per query)   │   │
│  │  - Multi-level caching                               │   │
│  │  - Performance tracking & feedback                   │   │
│  │  - Health monitoring & failover                      │   │
│  │  - NOVEL: Teaches agents about data source quality   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Components:                                                 │
│  • Performance Tracker (MCP response times, success rates)   │
│  • Source Quality Scorer (data reliability metrics)          │
│  • Cache Intelligence (anticipatory pre-fetching)            │
│  • Composed Tool Executor (runs multi-MCP workflows)         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    MCP SERVERS                               │
│  PubChem │ BioMCP │ Literature │ Clinical Trials │ Web       │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Multi-Agent Orchestration

The system implements true dual orchestration with specialized agents:

**Agent Orchestrator**
- Analyzes incoming queries to determine intent and domain
- Assigns queries to specialized agents based on content
- Coordinates multi-agent workflows when needed

**Specialized Agents**
- **Chemical Agent**: Handles chemistry queries (molecular formulas, compound properties) → Routes to PubChem
- **Clinical Agent**: Handles biomedical queries (genes, proteins, clinical trials) → Routes to BioMCP/Literature

**Query Flow Example:**
```
User: "What is the molecular formula of tylenol?"
  ↓
Agent Orchestrator: Detects chemical query type
  ↓
Chemical Agent: Assigned to handle query
  ↓
MCP Orchestrator: Routes to PubChem with preprocessed query
  ↓
PubChem MCP: Returns compound data (CID 1983)
```

### Persistent Event Loop Architecture

**Challenge:** MCP sessions created in one asyncio event loop become invalid when called from a different event loop.

**Solution:** Persistent event loop running in a dedicated background thread:

```python
class MCPEventLoop:
    """Persistent event loop for all MCP operations."""

    def __init__(self):
        self.loop = None
        self.thread = None

    def start(self):
        """Start event loop in daemon thread."""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

    def run_coroutine(self, coro, timeout=30):
        """Execute coroutine in the persistent loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(timeout=timeout)
```

**Benefits:**
- Single event loop for all MCP operations (connection + tool calls)
- Thread-safe execution via `run_coroutine_threadsafe()`
- Eliminates "Attempted to exit cancel scope in a different task" errors
- Compatible with Streamlit's synchronous execution model

### Query Preprocessing

Intelligent query preprocessing extracts relevant information for MCP-specific formats:

```python
# Example: PubChem expects compound names, not full questions
query = "What is the molecular formula of tylenol?"
# Preprocessed to: "tylenol"

processed_query = re.sub(
    r'\b(what|is|the|molecular|formula|of|structure)\b',
    '',
    query.lower(),
    flags=re.IGNORECASE
).strip().strip('?').strip()
```

---

## Novel Feature 1: Bidirectional Learning & Feedback Loops

### Concept
Agents and MCPs teach each other by observing and learning from interaction patterns.

### Implementation

#### MCP → Agent Learning Flow
```python
# MCP Layer tracks performance per query type
{
  "query_type": "inhibitor_search",
  "mcp_performance": {
    "PubChem": {"success_rate": 0.2, "avg_time": 2.1},
    "BioMCP": {"success_rate": 0.9, "avg_time": 1.5},
    "Wikipedia": {"success_rate": 0.5, "avg_time": 0.8}
  }
}

# Feedback sent to Agent Layer:
"For 'inhibitor' queries, BioMCP has 90% success vs PubChem 20%.
 Recommend: Route inhibitor queries to BioMCP first."

# Chemical Agent learns and updates its prompting:
"When searching for inhibitors, I should prefer BioMCP as it has
 higher success rate for this query type."
```

#### Agent → MCP Learning Flow
```python
# Agent tracks which queries succeed/fail
{
  "agent": "Clinical Agent",
  "observation": "Queries with exact trial IDs succeed 95% vs
                  vague descriptions succeed 30%",
  "recommendation": "Add query preprocessing to extract trial IDs"
}

# MCP Layer learns and adds preprocessing:
def route_query(query, agent_feedback):
    if agent_feedback["query_type"] == "clinical_trial":
        # Extract trial IDs based on agent feedback
        query = preprocess_for_trial_ids(query)
    return query
```

### Data Structures

```python
# Performance Knowledge Base (shared between layers)
class PerformanceKnowledgeBase:
    """Shared learning across Agent and MCP layers."""

    agent_learnings: Dict[str, AgentLearning]
    # e.g., {"Chemical": ["BioMCP best for inhibitors", ...]}

    mcp_learnings: Dict[str, MCPLearning]
    # e.g., {"BioMCP": ["Preprocess with CID extraction", ...]}

    cross_layer_patterns: List[Pattern]
    # e.g., [{"pattern": "Agent X + MCP Y = 90% success", ...}]
```

---

## Novel Feature 2: Dynamic Tool Composition

### Concept
Agents can combine multiple MCP calls into reusable "composed tools" that are cached for future use.

### Example Workflow

```python
# User asks: "Find drugs similar to aspirin but with fewer side effects"

# Chemical Agent realizes this needs a NEW composed tool:

COMPOSED_TOOL = {
  "name": "compare_drug_safety_profiles",
  "description": "Compare drugs by efficacy and safety",
  "steps": [
    {"mcp": "PubChem", "tool": "search_compounds_by_name",
     "input": {"name": "${drug_name}"}},

    {"mcp": "BioMCP", "tool": "find_similar_compounds",
     "input": {"smiles": "${step1.smiles}"}},

    {"mcp": "Literature", "tool": "search_adverse_events",
     "input": {"compounds": "${step2.compounds}"}},

    {"mcp": "DataAnalysis", "tool": "compare_safety_scores",
     "input": {"data": "${step3.results}"}}
  ],
  "cache_for": "7_days",
  "created_by": "Chemical Agent",
  "success_count": 0
}

# This tool is saved to Tool Composition Registry

# FUTURE QUERY: "Compare ibuprofen safety to alternatives"
# Orchestrator finds existing "compare_drug_safety_profiles" tool
# Reuses it automatically (faster response)
```

### Tool Composition Registry

```python
class ToolCompositionRegistry:
    """Registry of composed tools created by agents."""

    def register_composed_tool(
        self,
        name: str,
        steps: List[ToolStep],
        creator_agent: str,
        metadata: Dict
    ):
        """Register a new composed tool."""
        pass

    def find_matching_tool(self, query: str) -> Optional[ComposedTool]:
        """Find existing tool that matches query intent."""
        pass

    def execute_composed_tool(
        self,
        tool: ComposedTool,
        inputs: Dict
    ) -> ToolResult:
        """Execute multi-step tool workflow."""
        pass

    def get_tool_performance(self, tool_name: str) -> ToolMetrics:
        """Get success rate, avg time for composed tool."""
        pass
```

### Benefits
- System **learns new capabilities** through use
- Reduces latency for repeated complex queries
- Agents share sophisticated workflows
- Creates institutional memory of research patterns

---

## Novel Feature 8: Research Session Memory

### Concept
System maintains context across multiple queries to enable collaborative research sessions.

### Session Context Structure

```python
class ResearchSession:
    """Maintains context for multi-turn research collaboration."""

    session_id: str
    user_id: str
    start_time: datetime

    # Research context
    research_goal: str  # e.g., "Find BRCA1 drug candidates"
    entities_discovered: Dict[str, Entity]
    # e.g., {"BRCA1": Gene(...), "Olaparib": Drug(...)}

    hypotheses: List[Hypothesis]
    # e.g., [{"hypothesis": "Protein X is druggable",
    #         "evidence": [...], "confidence": 0.7}]

    # Query history with lineage
    query_history: List[QueryWithContext]
    # Each query knows what it builds upon

    # Agent activity timeline
    agent_timeline: List[AgentAction]
    # Visual representation of which agents did what

    # Discovered insights
    insights: List[Insight]
    # System-generated observations (e.g., "Publication velocity increasing")

    # Proactive suggestions
    next_steps: List[Suggestion]
    # System suggests what to investigate next
```

### Example Session Flow

```
USER (Turn 1): "I want to target amyloid beta for Alzheimer's"

SYSTEM:
- Creates session: research_goal = "Target amyloid beta"
- Entities discovered: {amyloid_beta: Protein(...)}
- Proactive suggestions:
  1. "Should I find existing drugs targeting amyloid beta?"
  2. "Should I analyze the amyloid beta pathway?"
  3. "Should I search for recent clinical trials?"

USER (Turn 2): "Find existing drugs"

SYSTEM:
- Knows context: searching for drugs targeting {amyloid_beta}
- Chemical Agent + Clinical Agent work together
- Updates entities: {Drug1: ..., Drug2: ..., Trial1: ...}
- New hypothesis: "3 drugs in trials, all BACE inhibitors"
- Proactive suggestion: "Most drugs failed. Should I explore
   alternative mechanisms (e.g., prevent aggregation)?"

USER (Turn 3): "Yes, explore alternatives"

SYSTEM:
- Knows context: Looking for non-BACE mechanisms
- Literature Agent + Gene Agent research alternatives
- Updates hypotheses: "Aggregation prevention: 2 approaches found"
- Timeline shows: Gene Agent → Literature Agent → synthesis
- Next suggestion: "Found promising antibody approach.
   Should I check if anyone is developing this?"

USER (Turn 4): "Weekly summary" (asked 1 week later)

SYSTEM:
- Loads session from 1 week ago
- Shows: "Last time you were exploring amyloid aggregation prevention"
- Runs differential update: "2 NEW papers published on this topic"
- Highlights changes: "Company X started Phase 1 trial (this is new!)"
- Suggests: "Shall we continue from here or start a new direction?"
```

### Session Memory Storage

```python
class SessionMemoryManager:
    """Manages research session persistence and retrieval."""

    def create_session(self, user_id: str, initial_query: str) -> ResearchSession:
        """Create new research session."""
        pass

    def update_session(
        self,
        session_id: str,
        new_entities: List[Entity],
        new_insights: List[Insight]
    ):
        """Update session with new discoveries."""
        pass

    def get_session_summary(self, session_id: str) -> SessionSummary:
        """Get executive summary of session progress."""
        pass

    def suggest_next_steps(self, session: ResearchSession) -> List[Suggestion]:
        """AI-generated suggestions for what to investigate next."""
        pass

    def detect_changes(
        self,
        session: ResearchSession,
        days_since: int
    ) -> List[Change]:
        """Detect what changed since last session (new trials, papers, etc.)."""
        pass
```

---

## Integration: How Features Work Together

### Example: Complex Multi-Session Research

```
SESSION 1 - Day 1:
User: "Competitive analysis of PD-1 inhibitors"

[Bidirectional Learning]
- Orchestrator learns: Clinical + Literature agents work well together
- MCP layer learns: Clinical queries need trial ID extraction

[Tool Composition]
- Chemical Agent creates: "competitive_pipeline_analyzer"
- Combines: PubChem + ClinicalTrials + Literature MCPs
- Saves to registry

[Session Memory]
- Entities: {PD-1: Protein, Pembrolizumab: Drug, ...}
- Hypothesis: "5 companies in Phase 3"
- Saves session

---

SESSION 2 - Week later:
User: "Update on PD-1 competitive landscape"

[Session Memory]
- Loads previous session
- Runs differential update

[Tool Composition]
- Finds existing "competitive_pipeline_analyzer" tool
- Reuses it (much faster than re-creating)

[Bidirectional Learning]
- Orchestrator: "This is a monitoring query, use cached results where possible"
- MCP layer: "Cache hit rate 80% for monitoring queries"

RESULT:
- Response in <5 seconds (vs 30 seconds first time)
- Shows only CHANGES since last week
- Proactively suggests: "Company X advanced to Phase 3. Investigate?"
```

---

## Implementation File Structure

```
streamlit-app/
├── orchestration/
│   ├── __init__.py
│   ├── agent_orchestrator.py          # Agent layer orchestration
│   ├── mcp_orchestrator.py            # MCP layer orchestration
│   ├── performance_kb.py              # Bidirectional learning (Novel 1)
│   ├── tool_composer.py               # Dynamic tool composition (Novel 2)
│   └── session_manager.py             # Research session memory (Novel 8)
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                  # Base class for all agents
│   ├── orchestrator_agent.py          # Main orchestrator
│   ├── chemical_agent.py              # Chemical compound specialist
│   ├── literature_agent.py            # Scientific literature specialist
│   ├── clinical_agent.py              # Clinical trials specialist
│   ├── data_agent.py                  # Data analysis specialist
│   └── gene_agent.py                  # Gene/protein specialist
│
├── mcp/
│   ├── __init__.py
│   ├── mcp_router.py                  # Intelligent MCP routing
│   ├── mcp_cache.py                   # Multi-level caching
│   ├── mcp_monitor.py                 # Performance tracking
│   └── mcp_tools.py                   # MCP tool wrappers (existing)
│
├── models/
│   ├── __init__.py
│   ├── session.py                     # ResearchSession data model
│   ├── composed_tool.py               # ComposedTool data model
│   ├── performance.py                 # Performance metrics models
│   └── entities.py                    # Entity models (Drug, Gene, etc.)
│
├── ui/
│   ├── __init__.py
│   ├── chat_interface.py              # Chat UI component
│   ├── agent_timeline.py              # Agent activity visualization
│   ├── performance_dashboard.py       # Performance metrics display
│   └── session_viewer.py              # Research session viewer
│
├── tests/
│   ├── test_orchestration.py
│   ├── test_bidirectional_learning.py
│   ├── test_tool_composition.py
│   └── test_session_memory.py
│
├── app.py                             # Main Streamlit app (updated)
├── agent.py                           # Legacy (keep for reference)
├── config.py                          # Configuration
└── requirements.txt                   # Updated dependencies
```

---

## Testing Strategy

### 1. Unit Tests
- Test each agent independently
- Test MCP orchestrator routing logic
- Test tool composition registry
- Test session memory storage/retrieval

### 2. Integration Tests
- Test agent + MCP orchestration together
- Test bidirectional learning feedback loops
- Test composed tool execution
- Test multi-turn session context

### 3. Scenario Tests
Create realistic research scenarios:

**Scenario 1: Simple Query (Baseline)**
- Query: "What is molecular weight of aspirin?"
- Expected: Single agent, single MCP, <5s response

**Scenario 2: Multi-Agent Complex Query**
- Query: "Find BRCA1-targeting drugs in clinical trials"
- Expected: Gene + Chemical + Clinical agents collaborate, <15s

**Scenario 3: Tool Composition Learning**
- Query 1: "Compare Drug X to alternatives"
- Query 2: "Compare Drug Y to alternatives" (1 hour later)
- Expected: Query 2 reuses composed tool, 50%+ faster

**Scenario 4: Multi-Session Research**
- Session 1: Explore disease X (Day 1)
- Session 2: Continue research (Day 7)
- Expected: System remembers context, shows changes

### 4. Performance Benchmarks

| Metric | Target | Test Method |
|--------|--------|-------------|
| Single agent query | <5s | Automated timer |
| Multi-agent query | <15s | Automated timer |
| Cache hit rate | >60% | Monitor over 100 queries |
| Tool composition reuse | >30% | Track registry usage |
| Session context recall | 100% | Test session reload |

---

## Expansion Paths

### Phase 1 (Current): Core Dual Orchestration
- MCP Orchestrator with routing & caching
- Agent Orchestrator with 5 specialized agents
- Basic LangGraph workflow

### Phase 2: Novel Features Foundation
- Bidirectional learning (performance tracking)
- Tool composition registry (basic)
- Session memory (single session)

### Phase 3: Advanced Intelligence
- Predictive caching (anticipate next query)
- Automated tool composition suggestions
- Multi-session timeline & insights

### Phase 4: Emergent Capabilities
- Hypothesis formation & testing
- Adversarial cross-validation
- Proactive research suggestions
- Autonomous research workflows

---

## Success Metrics

### Quantitative
- [ ] Query response time: <5s (simple), <15s (complex)
- [ ] Cache hit rate: >60%
- [ ] Tool composition reuse: >30% of complex queries
- [ ] Session context accuracy: 100% recall
- [ ] Agent routing accuracy: >90%

### Qualitative
- [ ] System demonstrates learning (improves over time)
- [ ] Composed tools provide measurable value
- [ ] Session memory enables collaborative research
- [ ] Agents+MCPs show emergent intelligence
- [ ] User reports faster, better research workflow

---

## Key Design Principles

1. **Layers are independent but collaborative**
   - Agent layer can work without MCP intelligence
   - MCP layer can work without agent feedback
   - Together, they create emergent capabilities

2. **Learning is gradual and observable**
   - Performance metrics tracked from day 1
   - Learning effects should be measurable
   - Users can see system improving

3. **Composed tools are first-class citizens**
   - Treated like built-in tools
   - Performance tracked separately
   - Can be shared, versioned, improved

4. **Sessions are lightweight but persistent**
   - Don't bloat with unnecessary data
   - Focus on entities, hypotheses, insights
   - Easy to resume after days/weeks

5. **Fail gracefully**
   - If learning fails, fall back to basic routing
   - If composition fails, execute steps individually
   - If session memory fails, work statelessly

---

**Status:** Ready to implement ✅

Next: Begin Phase 1 implementation with MCP Orchestrator foundation.
