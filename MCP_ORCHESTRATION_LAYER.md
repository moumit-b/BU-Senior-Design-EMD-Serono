# MCP Orchestration Layer Architecture

## Overview

This document describes the **MCP Orchestration Layer** that sits between specialized agents and the MCP servers. This layer provides intelligent routing, load balancing, failover, and optimization for MCP server communication.

---

## Complete System Architecture with MCP Orchestration

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                        │
│                      (Streamlit App)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              AGENT ORCHESTRATION LAYER                          │
│                   (Orchestrator Agent)                          │
│  - Query Analysis   - Agent Routing   - Result Synthesis        │
└────────┬──────────────────┬──────────────────┬──────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Chemical    │    │ Literature   │    │  Clinical    │
│   Agent      │    │   Agent      │    │   Agent      │    [More Agents...]
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              MCP ORCHESTRATION LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MCP Orchestrator                                        │   │
│  │  - Tool Discovery & Registry                            │   │
│  │  - Server Selection & Routing                           │   │
│  │  - Load Balancing & Health Monitoring                   │   │
│  │  - Caching & Result Optimization                        │   │
│  │  - Failover & Retry Logic                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────┬──────────────┬──────────────┬──────────────┬───────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP SERVERS LAYER                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ PubChem  │  │  BioMCP  │  │Literature│  │   Data   │        │
│  │  Server  │  │  Server  │  │  Server  │  │ Analysis │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐                                    │
│  │   Web    │  │  Custom  │     [Extensible]                   │
│  │Knowledge │  │   MCP    │                                    │
│  └──────────┘  └──────────┘                                    │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                 │
│  PubChem DB  │  PubMed  │  ClinicalTrials.gov  │  UniProt      │
└─────────────────────────────────────────────────────────────────┘
```

---

## MCP Orchestrator Components

### 1. Tool Discovery & Registry

**Purpose**: Maintain a centralized registry of all available MCP tools

**Features**:
- Dynamic tool discovery on server connection
- Tool metadata storage (capabilities, parameters, latency, reliability)
- Version tracking
- Capability indexing for fast lookup

**Data Structure**:
```python
class ToolRegistry:
    tools: Dict[str, ToolMetadata]
    server_map: Dict[str, List[str]]  # server -> tools
    capability_index: Dict[str, List[str]]  # capability -> tools

class ToolMetadata:
    name: str
    server: str
    description: str
    parameters: Dict[str, ParameterSpec]
    capabilities: List[str]  # ["chemical_search", "structure_lookup"]
    avg_latency: float
    success_rate: float
    last_updated: datetime
    version: str
```

**Operations**:
```python
# Register tools from a server
await registry.register_server("pubchem", tools_list)

# Find tools by capability
tools = registry.find_by_capability("molecular_structure")

# Get tool metadata
metadata = registry.get_tool_metadata("pubchem_compound_search")
```

---

### 2. Server Selection & Routing

**Purpose**: Intelligently route tool requests to the optimal MCP server

**Selection Criteria**:
1. **Capability Match**: Does the server have the required tool?
2. **Server Health**: Is the server available and responsive?
3. **Load Balancing**: Distribute load across available servers
4. **Data Locality**: Prefer servers with cached results
5. **Cost/Performance**: Balance speed vs. resource usage

**Routing Strategies**:

#### A. **Round-Robin** (Default)
- Distribute requests evenly across available servers
- Good for general load balancing

#### B. **Least Loaded**
- Route to server with fewest active requests
- Optimal for varying query complexity

#### C. **Capability-Based**
- Route to server with best capability match
- Some servers may have specialized implementations

#### D. **Hybrid**
- Combine multiple strategies
- Weighted scoring based on health, load, and capability

**Example Routing Logic**:
```python
class MCPRouter:
    def select_server(
        self,
        tool_name: str,
        parameters: Dict,
        strategy: str = "hybrid"
    ) -> str:
        """Select optimal server for tool execution"""

        # Get all servers that provide this tool
        candidate_servers = self.registry.get_servers_for_tool(tool_name)

        if not candidate_servers:
            raise ToolNotFoundError(f"No server provides {tool_name}")

        # Filter by health
        healthy_servers = [
            s for s in candidate_servers
            if self.health_monitor.is_healthy(s)
        ]

        if not healthy_servers:
            # Attempt failover
            return self.failover_handler.get_backup_server(tool_name)

        # Apply selection strategy
        if strategy == "round_robin":
            return self._round_robin_select(healthy_servers)
        elif strategy == "least_loaded":
            return self._least_loaded_select(healthy_servers)
        elif strategy == "hybrid":
            return self._hybrid_select(healthy_servers, tool_name, parameters)
```

---

### 3. Load Balancing & Health Monitoring

**Purpose**: Ensure system reliability and optimal performance

#### Health Monitoring

**Metrics Tracked**:
- Server availability (ping/heartbeat)
- Response time (p50, p95, p99)
- Error rate
- Active connections
- Queue depth

**Health Check Types**:
```python
class HealthMonitor:
    async def passive_monitoring(self, server: str):
        """Monitor based on actual traffic"""
        # Track request success/failure
        # Measure latencies
        # Detect anomalies

    async def active_monitoring(self, server: str):
        """Proactive health checks"""
        # Send periodic ping requests
        # Validate tool availability
        # Check resource usage

    def get_health_score(self, server: str) -> float:
        """Calculate 0-1 health score"""
        availability = self.get_availability(server)  # 0-1
        latency_score = self.get_latency_score(server)  # 0-1
        error_rate_score = 1 - self.get_error_rate(server)  # 0-1

        return (availability * 0.4 +
                latency_score * 0.3 +
                error_rate_score * 0.3)
```

#### Load Balancing

**Load Metrics**:
- Active requests per server
- Queue length
- CPU/Memory usage (if available)
- Historical load patterns

**Load Balancing Algorithm**:
```python
class LoadBalancer:
    def get_load_score(self, server: str) -> float:
        """Calculate load score (lower is better)"""
        active_requests = self.get_active_requests(server)
        queue_depth = self.get_queue_depth(server)
        historical_load = self.get_avg_load(server)

        # Normalize to 0-1 scale
        load_score = (
            (active_requests / MAX_CONCURRENT) * 0.5 +
            (queue_depth / MAX_QUEUE) * 0.3 +
            historical_load * 0.2
        )
        return load_score

    def select_least_loaded(self, servers: List[str]) -> str:
        """Select server with lowest load"""
        return min(servers, key=self.get_load_score)
```

---

### 4. Caching & Result Optimization

**Purpose**: Reduce latency and server load through intelligent caching

#### Multi-Level Cache Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    L1: In-Memory Cache                      │
│  - Hot queries (last 100 queries)                          │
│  - TTL: 5 minutes                                           │
│  - Storage: Python dict with LRU eviction                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ (on miss)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    L2: Redis Cache                          │
│  - Shared across sessions                                  │
│  - TTL: 1 hour (configurable by query type)                │
│  - Storage: Redis with semantic keys                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ (on miss)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    L3: Persistent Cache                     │
│  - Long-lived stable data (compounds, genes)               │
│  - TTL: 24 hours - 30 days                                 │
│  - Storage: SQLite/PostgreSQL                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ (on miss)
                       ▼
                  Execute MCP Tool
```

#### Cache Key Generation

**Semantic Cache Keys**:
```python
class CacheKeyGenerator:
    def generate_key(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate semantic cache key"""

        # Normalize parameters
        normalized = self._normalize_params(parameters)

        # Handle semantic equivalence
        # "aspirin" == "acetylsalicylic acid" == "CID_2244"
        normalized = self._apply_synonyms(normalized)

        # Create deterministic hash
        param_str = json.dumps(normalized, sort_keys=True)
        hash_value = hashlib.sha256(param_str.encode()).hexdigest()[:16]

        return f"{tool_name}:{hash_value}"
```

#### Cache Invalidation Strategies

1. **Time-Based (TTL)**
   - Static data: 7-30 days (e.g., compound structures)
   - Semi-static: 1-7 days (e.g., gene information)
   - Dynamic: 1-24 hours (e.g., literature searches)
   - Real-time: 5-60 minutes (e.g., clinical trial status)

2. **Event-Based**
   - Invalidate on data source updates
   - Clear cache when MCP server version changes

3. **Capacity-Based**
   - LRU eviction when cache is full
   - Priority-based retention (frequently accessed items stay longer)

#### Result Optimization

**Compression**:
```python
class ResultOptimizer:
    def compress_result(self, result: str) -> bytes:
        """Compress large results for caching"""
        if len(result) > 10_000:  # 10KB threshold
            return gzip.compress(result.encode())
        return result.encode()

    def decompress_result(self, data: bytes) -> str:
        """Decompress cached result"""
        try:
            return gzip.decompress(data).decode()
        except:
            return data.decode()
```

**Partial Result Caching**:
```python
# Cache intermediate results for multi-step queries
cache.set(f"{query_id}:step1", result1)
cache.set(f"{query_id}:step2", result2)

# Reuse if query pattern repeats
if cache.exists(f"{new_query_id}:step1"):
    result1 = cache.get(f"{new_query_id}:step1")
    # Skip to step 2
```

---

### 5. Failover & Retry Logic

**Purpose**: Ensure system resilience and handle failures gracefully

#### Failover Strategies

```python
class FailoverHandler:
    def __init__(self):
        self.backup_servers = {
            "pubchem_search": ["pubchem", "web_knowledge"],
            "literature_search": ["literature", "biomcp"],
            # More tool -> server mappings
        }

    async def execute_with_failover(
        self,
        tool_name: str,
        parameters: Dict,
        max_attempts: int = 3
    ):
        """Execute tool with automatic failover"""

        servers = self.get_server_priority_list(tool_name)
        errors = []

        for attempt, server in enumerate(servers[:max_attempts]):
            try:
                logger.info(f"Attempt {attempt+1}: {server}.{tool_name}")
                result = await self.mcp_client.call_tool(
                    server, tool_name, parameters, timeout=30
                )
                return result

            except TimeoutError as e:
                errors.append(f"{server}: Timeout")
                logger.warning(f"{server} timeout, trying next...")
                continue

            except ConnectionError as e:
                errors.append(f"{server}: Connection failed")
                logger.warning(f"{server} connection failed, trying next...")
                # Mark server as unhealthy
                self.health_monitor.mark_unhealthy(server)
                continue

            except ToolNotFoundError:
                errors.append(f"{server}: Tool not found")
                # Don't retry on this type of error
                break

        # All attempts failed
        raise MCPExecutionError(
            f"Failed to execute {tool_name} after {len(servers)} attempts. "
            f"Errors: {errors}"
        )
```

#### Retry Logic

**Exponential Backoff**:
```python
class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ):
        """Execute function with exponential backoff retry"""

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)

            except RetryableError as e:
                if attempt == self.max_retries - 1:
                    raise  # Last attempt, propagate error

                # Calculate delay with jitter
                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                jitter = random.uniform(0, delay * 0.1)
                total_delay = delay + jitter

                logger.info(f"Retry {attempt+1} after {total_delay:.2f}s")
                await asyncio.sleep(total_delay)

            except NonRetryableError:
                raise  # Don't retry
```

**Retry Decision Matrix**:

| Error Type            | Retry? | Max Retries | Strategy        |
|-----------------------|--------|-------------|-----------------|
| Network Timeout       | Yes    | 3           | Exponential     |
| Connection Refused    | Yes    | 2           | Linear          |
| Server Error (5xx)    | Yes    | 3           | Exponential     |
| Rate Limit (429)      | Yes    | 5           | With backoff    |
| Invalid Request (4xx) | No     | 0           | -               |
| Tool Not Found        | No     | 0           | -               |
| Invalid Parameters    | No     | 0           | -               |

#### Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Prevent cascading failures"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        reset_timeout: float = 300.0
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = None

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker"""

        if self.state == "OPEN":
            # Check if we should try again
            if (time.time() - self.last_failure_time) > self.reset_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout
            )

            # Success - reset counter
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failures = 0
            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker opened after {self.failures} failures")

            raise
```

---

## MCP Orchestration Workflows

### Workflow 1: Simple Tool Execution

```
Agent Request
     │
     ▼
┌────────────────────┐
│ MCP Orchestrator   │
└────────┬───────────┘
         │
         ├─→ Check Cache ──→ [Cache Hit] ──→ Return Cached Result
         │                         ↓
         │                    [Cache Miss]
         │                         ↓
         ├─→ Select Server (routing logic)
         │
         ├─→ Check Health (is server available?)
         │
         ├─→ Execute Tool
         │        │
         │        ├─→ [Success] ──→ Cache Result ──→ Return
         │        │
         │        └─→ [Failure] ──→ Retry/Failover
         │                              │
         │                              ├─→ Try Next Server
         │                              └─→ All Failed → Error
```

### Workflow 2: Multi-Server Query (Aggregation)

```
Agent Request: "Find compound info from multiple sources"
     │
     ▼
┌────────────────────┐
│ MCP Orchestrator   │
│ - Decompose query  │
│ - Identify servers │
└────────┬───────────┘
         │
         ├─────────────┬──────────────┬──────────────┐
         │             │              │              │
         ▼             ▼              ▼              ▼
    PubChem        BioMCP      Web Knowledge   Data Analysis
         │             │              │              │
         └─────────────┴──────────────┴──────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │  Aggregate   │
                   │   Results    │
                   └──────┬───────┘
                          │
                          ▼
                  Unified Response
```

### Workflow 3: Failover Scenario

```
Tool Request → Server A (Primary)
                   │
                   ├─→ [Timeout after 30s]
                   │
                   ▼
              Mark A Unhealthy
                   │
                   ▼
              Server B (Backup)
                   │
                   ├─→ [Connection Error]
                   │
                   ▼
              Server C (Tertiary)
                   │
                   ├─→ [Success]
                   │
                   ▼
              Return Result
                   │
                   ▼
         Schedule A Health Check
```

---

## Configuration & Deployment

### MCP Orchestrator Configuration

```yaml
# mcp_orchestrator_config.yaml

orchestrator:
  # Server selection
  routing_strategy: "hybrid"  # round_robin | least_loaded | hybrid

  # Health monitoring
  health_check_interval: 30  # seconds
  unhealthy_threshold: 3  # consecutive failures
  recovery_check_interval: 60  # seconds

  # Load balancing
  max_concurrent_per_server: 10
  max_queue_per_server: 50

  # Caching
  cache_levels:
    - name: "memory"
      enabled: true
      ttl: 300  # 5 minutes
      max_size: 100

    - name: "redis"
      enabled: true
      ttl: 3600  # 1 hour
      url: "redis://localhost:6379"

    - name: "persistent"
      enabled: false
      ttl: 86400  # 24 hours
      db_url: "sqlite:///mcp_cache.db"

  # Failover & retry
  retry:
    max_attempts: 3
    base_delay: 1.0
    max_delay: 30.0
    exponential_base: 2.0

  circuit_breaker:
    enabled: true
    failure_threshold: 5
    timeout: 60
    reset_timeout: 300

# Server definitions
servers:
  pubchem:
    priority: 1
    max_concurrent: 5
    timeout: 30
    backup_servers: ["web_knowledge"]

  biomcp:
    priority: 1
    max_concurrent: 10
    timeout: 45
    backup_servers: []

  literature:
    priority: 1
    max_concurrent: 8
    timeout: 30
    backup_servers: ["biomcp"]

  data_analysis:
    priority: 2
    max_concurrent: 5
    timeout: 60
    backup_servers: []

  web_knowledge:
    priority: 2
    max_concurrent: 10
    timeout: 20
    backup_servers: []
```

### Integration with Agent Layer

```python
# agents/chemical_agent.py

class ChemicalCompoundAgent(BaseAgent):
    def __init__(self, mcp_orchestrator: MCPOrchestrator):
        self.mcp = mcp_orchestrator
        self.llm = OllamaLLM(model="llama3.2")

    async def search_compound(self, compound_name: str):
        """Search for compound using MCP orchestration"""

        # Agent doesn't need to know which server to use
        # MCP orchestrator handles routing, caching, failover
        result = await self.mcp.execute_tool(
            tool_name="compound_search",
            parameters={"query": compound_name},
            preferences={
                "prefer_cache": True,
                "max_latency": 10.0,  # seconds
                "require_fresh": False
            }
        )

        return result
```

---

## Benefits of MCP Orchestration Layer

### 1. Abstraction
- Agents don't need to know about MCP server details
- Simplified agent code
- Easier to add/remove MCP servers

### 2. Reliability
- Automatic failover
- Circuit breakers prevent cascading failures
- Graceful degradation

### 3. Performance
- Intelligent caching reduces latency
- Load balancing optimizes resource usage
- Parallel execution where possible

### 4. Observability
- Centralized monitoring
- Performance metrics
- Error tracking

### 5. Flexibility
- Easy to swap MCP implementations
- A/B testing of different servers
- Gradual rollout of new servers

---

## Monitoring & Metrics

### Key Metrics to Track

```python
class MCPMetrics:
    # Throughput
    requests_per_second: float
    requests_per_server: Dict[str, int]

    # Latency
    avg_latency: float
    p95_latency: float
    p99_latency: float
    latency_by_tool: Dict[str, float]

    # Reliability
    success_rate: float
    error_rate: float
    timeout_rate: float

    # Caching
    cache_hit_rate: float
    cache_size: int

    # Health
    healthy_servers: int
    unhealthy_servers: int
    circuit_breaker_trips: int
```

### Dashboard Visualization

```
MCP Orchestration Dashboard
════════════════════════════════════════════════════════════

Server Health                    Request Distribution
┌─────────────────────┐         ┌─────────────────────┐
│ ● PubChem   (95%)   │         │ PubChem      █████  │
│ ● BioMCP    (88%)   │         │ BioMCP       ███    │
│ ● Literature (92%)  │         │ Literature   ████   │
│ ○ Data Anal (45%)   │         │ Data Anal    ██     │
│ ● Web Know  (98%)   │         │ Web Know     ███    │
└─────────────────────┘         └─────────────────────┘

Cache Performance               Response Times (ms)
┌─────────────────────┐         ┌─────────────────────┐
│ Hit Rate:  67%      │         │ p50:  250ms         │
│ Miss Rate: 33%      │         │ p95:  890ms         │
│ Size: 1.2k entries  │         │ p99: 1450ms         │
│ Evictions: 45/hr    │         │ Max: 2100ms         │
└─────────────────────┘         └─────────────────────┘

Recent Errors                    Failovers (Last Hour)
┌─────────────────────┐         ┌─────────────────────┐
│ 15:23 - Timeout     │         │ 3 failovers         │
│ 15:45 - Conn Error  │         │ 2 circuit breaks    │
│ 16:12 - Rate Limit  │         │ Avg recovery: 12s   │
└─────────────────────┘         └─────────────────────┘
```

---

## Implementation Checklist

- [ ] Core MCP Orchestrator class
- [ ] Tool Registry & Discovery
- [ ] Server Health Monitoring
- [ ] Load Balancer
- [ ] Cache Manager (multi-level)
- [ ] Retry & Failover Handler
- [ ] Circuit Breaker
- [ ] Metrics Collection
- [ ] Configuration Management
- [ ] Integration with Agents
- [ ] Unit Tests
- [ ] Integration Tests
- [ ] Performance Benchmarks
- [ ] Monitoring Dashboard
- [ ] Documentation

---

## Next Steps

1. Review this MCP orchestration design
2. Prioritize features for MVP
3. Begin implementation in parallel with agent orchestration
4. Set up monitoring infrastructure
5. Create test suite for reliability validation

This MCP orchestration layer provides the foundation for a robust, scalable, and performant multi-agent system.
