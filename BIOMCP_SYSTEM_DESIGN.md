# BioMCP System Design & Integration

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [BioMCP's Role in the System](#biomcps-role-in-the-system)
3. [Integration Layers](#integration-layers)
4. [Communication Flow](#communication-flow)
5. [Technical Implementation](#technical-implementation)
6. [Data Flow Examples](#data-flow-examples)
7. [Comparison with Other Servers](#comparison-with-other-servers)

---

## System Architecture Overview

### High-Level System Layers

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: PRESENTATION LAYER                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │          Streamlit Web UI (app.py)                      │ │
│ │  - User input/output                                    │ │
│ │  - Query visualization                                  │ │
│ │  - Results display                                      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: AGENT ORCHESTRATION LAYER                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │       Custom ReAct Agent (agent.py)                     │ │
│ │  - Query understanding                                  │ │
│ │  - Tool selection logic                                 │ │
│ │  - Reasoning/Acting loop                                │ │
│ │  - LLM interaction (Ollama/Llama 3.2)                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: TOOL ABSTRACTION LAYER                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │       MCP Tool Wrapper (mcp_tools.py)                   │ │
│ │  - LangChain Tool abstraction                           │ │
│ │  - Async/threading management                           │ │
│ │  - Tool registry & discovery                            │ │
│ │  - Error handling & retries                             │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: MCP PROTOCOL LAYER                                │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   MCP    │  │   MCP    │  │   MCP    │  │   MCP    │  │
│  │  Client  │  │  Client  │  │  Client  │  │  Client  │  │
│  │(PubChem) │  │ (BioMCP) │  │  (Lit.)  │  │  (Data)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │ stdio       │ stdio       │ stdio       │ stdio   │
│       ↕             ↕             ↕             ↕         │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
┌───────┼─────────────┼─────────────┼─────────────┼─────────┐
│ LAYER 5: MCP SERVER LAYER                                 │
│       │             │             │             │         │
│  ┌────▼─────┐  ┌───▼──────┐  ┌───▼──────┐  ┌───▼──────┐ │
│  │ PubChem  │  │  BioMCP  │  │Literature│  │   Data   │ │
│  │  Server  │  │  Server  │  │  Server  │  │ Analysis │ │
│  │ (Node.js)│  │ (Python) │  │(Node.js) │  │(Node.js) │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 6: EXTERNAL API LAYER                                │
│                                                             │
│  ┌──────────┐  ┌──────────────────────────────────────┐   │
│  │ PubChem  │  │      BioMCP Data Sources:            │   │
│  │REST API  │  │  - PubMed/PubTator3                  │   │
│  └──────────┘  │  - ClinicalTrials.gov                │   │
│                │  - NCI Clinical Trials Search API    │   │
│  ┌──────────┐  │  - MyVariant.info                    │   │
│  │ PubMed   │  │  - cBioPortal                        │   │
│  │ E-utils  │  │  - MyGene.info                       │   │
│  └──────────┘  │  - MyChem.info                       │   │
│                │  - OncoKB                             │   │
│  ┌──────────┐  │  - AlphaGenome                       │   │
│  │Wikipedia │  │  - OpenFDA                           │   │
│  │   API    │  └──────────────────────────────────────┘   │
│  └──────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## BioMCP's Role in the System

### Core Function
**BioMCP is a specialized biomedical research aggregator** that acts as a **unified gateway** to multiple biomedical databases and APIs.

### Key Responsibilities

#### 1. **Data Source Aggregation**
BioMCP consolidates access to 9+ biomedical data sources:
- **PubMed & PubTator3** (literature with entity recognition)
- **ClinicalTrials.gov & NCI CTS** (clinical trials)
- **MyVariant.info** (genetic variants)
- **cBioPortal** (cancer genomics)
- **MyGene.info & MyChem.info** (gene/drug information)
- **OncoKB** (oncology knowledge)
- **AlphaGenome** (variant effect prediction)
- **OpenFDA** (FDA drug and safety data)

#### 2. **Tool Provisioning**
Provides **24 specialized tools** categorized as:
- **Core Tools** (3): Think, Search, Fetch
- **Article Tools** (2): Article search and retrieval
- **Trial Tools** (6): Clinical trial operations
- **Variant Tools** (2): Genetic variant queries
- **NCI Tools** (6): Organization, intervention, biomarker, disease
- **Entity Tools** (3): Gene, disease, drug getters
- **FDA Tools** (2): Drug and recall information

#### 3. **Query Intelligence**
- **Cross-domain search** - Single query can search articles, trials, or variants
- **Entity recognition** - Identifies genes, diseases, drugs in text
- **Advanced filtering** - Complex search parameters (phase, status, location)
- **Structured results** - Normalized output format across all sources

---

## Integration Layers

### Layer 1: Configuration Layer (`config.py`)

```python
MCP_SERVERS = {
    "biomcp": {
        "command": "python",           # ← Executor: Python interpreter
        "args": ["-m", "biomcp", "run"], # ← Module to run
        "description": "BioMCP server - Comprehensive biomedical research"
    }
}
```

**What happens here:**
- System defines how to **launch** BioMCP
- `python -m biomcp run` tells Python to execute the BioMCP module
- This runs within the **virtual environment's Python interpreter**

---

### Layer 2: Process Management Layer (`mcp_tools.py`)

```python
async def connect(self):
    """Establish connection to the MCP server."""
    # 1. Create server parameters
    server_params = StdioServerParameters(
        command=self.server_config["command"],  # "python"
        args=self.server_config["args"]         # ["-m", "biomcp", "run"]
    )

    # 2. Start BioMCP as a subprocess with stdio pipes
    self._context_manager = stdio_client(server_params)
    self.read_stream, self.write_stream = await self._context_manager.__aenter__()

    # 3. Create MCP session
    self.session = ClientSession(self.read_stream, self.write_stream)
    await self.session.__aenter__()

    # 4. Initialize and discover tools
    await self.session.initialize()
    response = await self.session.list_tools()
    self._tools_cache = response.tools  # ← BioMCP returns 24 tools
```

**What happens here:**
1. **Process spawning**: System spawns `python -m biomcp run` as child process
2. **Pipe creation**: Creates stdin/stdout pipes for communication
3. **Session establishment**: MCP client-server handshake
4. **Tool discovery**: BioMCP advertises its 24 available tools

---

### Layer 3: Tool Wrapping Layer (`mcp_tools.py`)

```python
def get_langchain_tools(self) -> List[Tool]:
    """Convert MCP tools to LangChain tools."""
    langchain_tools = []

    for mcp_tool in self._tools_cache:  # 24 BioMCP tools
        tool_name = mcp_tool.name       # e.g., "article_searcher"
        tool_description = mcp_tool.description

        # Create LangChain Tool wrapper
        def make_tool_func(name: str, wrapper_instance):
            def tool_func(arguments: str) -> str:
                # Parse JSON arguments
                args_dict = json.loads(arguments)

                # Execute tool in separate thread (for Streamlit)
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            wrapper_instance.call_tool(name, args_dict)
                        )
                    )
                    result = future.result(timeout=60)
                return result
            return tool_func

        langchain_tool = Tool(
            name=tool_name,
            func=make_tool_func(tool_name, self),
            description=tool_description
        )
        langchain_tools.append(langchain_tool)

    return langchain_tools
```

**What happens here:**
- Each BioMCP tool becomes a **LangChain Tool**
- Tool functions wrap async MCP calls
- Threading ensures compatibility with Streamlit
- Agent can now call `article_searcher({"query": "CRISPR"})`

---

### Layer 4: Agent Execution Layer (`agent.py`)

```python
class MCPAgent:
    def __init__(self, tools: List[Tool]):
        self.tools = tools  # Includes 24 BioMCP tools
        self.tools_dict = {tool.name: tool for tool in tools}

    def query(self, question: str):
        # Agent reasoning loop
        for iteration in range(MAX_ITERATIONS):
            # LLM decides which tool to use
            response = self.llm.invoke(prompt)

            # Parse action (e.g., "article_searcher")
            action_name, action_input = self._parse_action(response)

            # Execute BioMCP tool
            if action_name in self.tools_dict:
                tool = self.tools_dict[action_name]
                observation = tool.func(json.dumps(action_input))

                # Continue reasoning with observation
                conversation += f"OBSERVATION: {observation}"
```

**What happens here:**
- Agent has access to all 24 BioMCP tools
- LLM (Llama 3.2) decides when to use BioMCP tools
- Agent executes tool and gets results
- Results feed back into reasoning loop

---

## Communication Flow

### Detailed Message Flow: User Query → BioMCP → Response

```
User: "Find clinical trials for breast cancer"
  │
  ▼
┌─────────────────────────────────────────┐
│ Streamlit UI (app.py)                   │
│ - Captures user input                   │
│ - Sends to agent                        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ ReAct Agent (agent.py)                  │
│ Step 1: Analyze query                   │
│   "This is about clinical trials"       │
│ Step 2: Select tool                     │
│   "Use trial_searcher from BioMCP"      │
│ Step 3: Prepare parameters              │
│   {"condition": "breast cancer"}        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ MCP Tool Wrapper (mcp_tools.py)         │
│ Step 1: Get tool function               │
│   tool = tools_dict["trial_searcher"]   │
│ Step 2: Create thread for async call    │
│   ThreadPoolExecutor.submit()           │
└──────────────┬──────────────────────────┘
               │
               ▼ (in separate thread)
┌─────────────────────────────────────────┐
│ MCP Client Session (mcp SDK)            │
│ Step 1: Create JSON-RPC request         │
│   {                                     │
│     "method": "tools/call",             │
│     "params": {                         │
│       "name": "trial_searcher",         │
│       "arguments": {                    │
│         "condition": "breast cancer"    │
│       }                                 │
│     }                                   │
│   }                                     │
│ Step 2: Send via stdout pipe            │
└──────────────┬──────────────────────────┘
               │ (stdio pipe)
               ▼
┌─────────────────────────────────────────┐
│ BioMCP Server Process                   │
│ (python -m biomcp run)                  │
│                                         │
│ Step 1: Receive JSON-RPC request        │
│ Step 2: Route to trial_searcher handler │
│ Step 3: Execute search logic            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ ClinicalTrials.gov API                  │
│ GET /api/v2/studies?cond=breast+cancer │
│                                         │
│ Returns JSON with trial data            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ BioMCP Server Process                   │
│ Step 4: Parse API response              │
│ Step 5: Format as MCP result            │
│   {                                     │
│     "content": [{                       │
│       "type": "text",                   │
│       "text": "{\"trials\": [...]}"     │
│     }]                                  │
│   }                                     │
│ Step 6: Send via stdin pipe             │
└──────────────┬──────────────────────────┘
               │ (stdio pipe)
               ▼
┌─────────────────────────────────────────┐
│ MCP Client Session                      │
│ Step 3: Receive JSON-RPC response       │
│ Step 4: Extract text content            │
│ Step 5: Return to calling thread        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ MCP Tool Wrapper                        │
│ Step 3: Get result from thread          │
│ Step 4: Return to agent                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ ReAct Agent                             │
│ Step 4: Receive observation             │
│   "Found 10 trials for breast cancer"   │
│ Step 5: Continue reasoning              │
│   "I have the answer now"               │
│ Step 6: Format final answer             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Streamlit UI                            │
│ - Display results to user               │
│ - Show reasoning process                │
└─────────────────────────────────────────┘
```

---

## Technical Implementation

### 1. BioMCP as a Subprocess

```
┌─────────────────────────────────────────────┐
│ Main Python Process (Streamlit)             │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ Asyncio Event Loop                 │    │
│  │  - MCP Client Sessions             │    │
│  │  - Stdio Stream Management         │    │
│  └────────────────────────────────────┘    │
│                    │                        │
│                    │ spawn subprocess       │
│                    ▼                        │
│  ┌────────────────────────────────────┐    │
│  │ Subprocess: python -m biomcp run   │────┼──→ Child Process
│  │                                    │    │
│  │ stdin  ←────────┐                  │    │
│  │ stdout ─────────┤  Pipes           │    │
│  │ stderr ─────────┘                  │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**Why subprocess?**
- **Isolation**: BioMCP runs in separate process, crashes don't affect main app
- **Resource management**: Can be killed/restarted independently
- **Protocol compliance**: MCP specification uses stdio transport
- **Language flexibility**: Can be any language (Python, Node.js, etc.)

---

### 2. Stdio Protocol Communication

**Message Format (JSON-RPC 2.0):**

**Request (Main App → BioMCP):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "article_searcher",
    "arguments": {
      "query": "BRCA1 breast cancer",
      "max_results": 10
    }
  }
}
```

**Response (BioMCP → Main App):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"articles\": [{\"pmid\": \"12345\", \"title\": \"...\"}]}"
      }
    ]
  }
}
```

**Protocol Features:**
- **Bidirectional**: Both sides can send requests
- **Asynchronous**: Multiple requests in flight
- **Type-safe**: Schema validation via Pydantic
- **Error handling**: Structured error responses

---

### 3. Threading Model

```python
# Streamlit runs in main thread
# MCP operations need async handling

Main Thread (Streamlit)
  │
  ├─ Agent.query() called
  │   │
  │   └─ tool.func() called
  │       │
  │       └─ Creates Worker Thread
  │           │
  │           ├─ New Event Loop
  │           │   │
  │           │   └─ asyncio.run(call_tool())
  │           │       │
  │           │       └─ Send to BioMCP via stdio
  │           │           │
  │           │           └─ Wait for response
  │           │               │
  │           │               └─ Return result
  │           │
  │           └─ Thread.join()
  │               │
  │               └─ Result back to main thread
  │
  └─ Continue agent reasoning
```

**Why this model?**
- **Streamlit limitation**: Cannot use async in main thread
- **MCP requirement**: SDK is fully async
- **Solution**: Run MCP calls in worker threads with new event loops
- **Benefit**: Clean separation, no blocking

---

## Data Flow Examples

### Example 1: Simple Query

**Query**: "What is BRCA1?"

```
User Input: "What is BRCA1?"
    │
    ▼
Agent: Analyze query
    │ → Decision: This is about a gene
    │ → Tool selection: gene_getter
    │
    ▼
MCP Wrapper: Prepare call
    │ → args = {"gene_symbol": "BRCA1"}
    │
    ▼
BioMCP Server: Receive request
    │ → Route to gene_getter
    │ → Call MyGene.info API
    │
    ▼
MyGene.info API: Return gene data
    │
    ▼
BioMCP Server: Format response
    │ → {
    │     "symbol": "BRCA1",
    │     "description": "BRCA1 DNA repair associated",
    │     "chromosome": "17",
    │     ...
    │   }
    │
    ▼
Agent: Receive observation
    │ → "BRCA1 is a gene on chromosome 17..."
    │ → Decision: I have the answer
    │
    ▼
Final Answer: "BRCA1 (BRCA1 DNA repair associated) is a gene
              located on chromosome 17. It encodes a nuclear
              phosphoprotein involved in DNA repair..."
```

---

### Example 2: Multi-Step Query

**Query**: "Find clinical trials for drugs targeting BRCA1"

```
User Input: "Find clinical trials for drugs targeting BRCA1"
    │
    ▼
Agent Iteration 1:
    │ → Thought: "I need to find BRCA1 first"
    │ → Action: gene_getter("BRCA1")
    │ → Observation: "BRCA1 is a DNA repair gene..."
    │
    ▼
Agent Iteration 2:
    │ → Thought: "Now I need drugs targeting BRCA1"
    │ → Action: article_searcher("BRCA1 drugs inhibitors")
    │ → Observation: "Found articles about olaparib, talazoparib..."
    │
    ▼
Agent Iteration 3:
    │ → Thought: "Now search trials for these drugs"
    │ → Action: trial_searcher({"intervention": "olaparib"})
    │ → Observation: "Found 50 trials testing olaparib..."
    │
    ▼
Agent Iteration 4:
    │ → Thought: "I have enough information"
    │ → Final Answer: "I found several clinical trials for BRCA1-
    │                   targeting drugs. The main drugs are:
    │                   1. Olaparib (50 trials)
    │                   2. Talazoparib (23 trials)
    │                   ..."
```

---

## Comparison with Other Servers

### BioMCP vs PubChem Server

| Aspect | BioMCP | PubChem |
|--------|--------|---------|
| **Language** | Python | Node.js |
| **Transport** | Stdio | Stdio |
| **Process Model** | Subprocess | Subprocess |
| **Tool Count** | 24 tools | 2 tools |
| **Data Sources** | 9+ APIs | 1 API |
| **Domain** | Biomedical research | Chemical compounds |
| **Complexity** | High (entity recognition, cross-domain) | Low (direct API wrapper) |
| **Package** | biomcp-python (external) | Custom implementation |

---

### Why BioMCP is Special

#### 1. **Package-Based Implementation**
```
PubChem:  Custom MCP server written from scratch
BioMCP:   Pre-built package (pip install biomcp-python)

Advantage: Maintained by experts, more features, regular updates
```

#### 2. **Multi-API Aggregation**
```
PubChem:  1 API endpoint (PubChem PUG REST)
BioMCP:   9+ API endpoints (PubMed, NIH, FDA, etc.)

Advantage: One tool access point for all biomedical data
```

#### 3. **Intelligent Features**
```
PubChem:  Simple API wrapper
BioMCP:   - Entity recognition (genes, diseases, drugs)
          - Cross-domain search
          - Advanced filtering
          - Structured outputs

Advantage: Smarter queries, better results
```

#### 4. **Specialized Tools**
```
PubChem:  2 generic tools (search, get properties)
BioMCP:   24 specialized tools (trials by phase, biomarker search, etc.)

Advantage: More precise queries, less agent confusion
```

---

## System Integration Benefits

### 1. **Unified Interface**
Agent sees all tools the same way (LangChain Tool interface):
```python
# Agent doesn't know/care that these are different servers:
tool1 = tools["search_compounds_by_name"]  # PubChem
tool2 = tools["article_searcher"]          # BioMCP
tool3 = tools["search_pubmed"]             # Literature server

# All called the same way:
result1 = tool1({"name": "aspirin"})
result2 = tool2({"query": "BRCA1"})
result3 = tool3({"query": "diabetes"})
```

### 2. **Graceful Degradation**
```python
# If BioMCP fails to connect:
- System continues with other servers
- Agent still has 21+ tools from other servers
- User can still do chemical, literature, data analysis queries
```

### 3. **Independent Scaling**
```
Each MCP server is independent:
- Can restart BioMCP without affecting PubChem
- Can add more BioMCP instances for load balancing
- Can upgrade BioMCP package without touching other code
```

### 4. **Clean Separation of Concerns**
```
Layer 1 (UI):           Knows nothing about BioMCP
Layer 2 (Agent):        Only knows tool names/descriptions
Layer 3 (MCP Wrapper):  Handles connection/communication
Layer 4 (BioMCP):       Handles biomedical logic

Each layer is replaceable/upgradeable independently
```

---

## Summary

### BioMCP's Role: **Biomedical Data Gateway**

**What it does:**
- Aggregates 9+ biomedical APIs into 24 specialized tools
- Provides entity recognition and intelligent search
- Enables cross-domain biomedical queries
- Handles complex filtering and structured outputs

**How it integrates:**
- Runs as **subprocess** (`python -m biomcp run`)
- Communicates via **stdio pipes** (JSON-RPC 2.0)
- Wrapped as **LangChain Tools** for agent consumption
- Executed in **worker threads** for Streamlit compatibility

**Why it's important:**
- **Comprehensive**: Access to all major biomedical databases
- **Intelligent**: Entity recognition, advanced search
- **Reliable**: Maintained package, not custom code
- **Extensible**: Easy to add more data sources
- **Professional**: Used by research institutions

**System Design Pattern:**
```
Thin Client (Agent) + Rich Server (BioMCP)

Agent:    Simple reasoning loop, tool selection
BioMCP:   Complex data aggregation, API management

This keeps agent logic simple while providing
powerful biomedical research capabilities.
```

---

## Future Enhancements

### Planned BioMCP Improvements

1. **Caching Layer**
   - Cache frequent queries (genes, diseases)
   - Reduce API calls
   - Faster responses

2. **Batch Operations**
   - Query multiple genes at once
   - Bulk trial searches
   - Parallel API calls

3. **Custom Filters**
   - User-defined search filters
   - Saved search templates
   - Query history

4. **Authentication**
   - API key management
   - Rate limit handling
   - Premium features (OncoKB, cBioPortal tokens)

---

**Last Updated**: November 2025
**Version**: 1.0
**System**: BU Senior Design EMD Serono
