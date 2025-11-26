# Dual Orchestration Lab - Demo Guide

## Overview

The **Dual Orchestration Lab** is an interactive Streamlit demo showcasing the dual orchestration architecture with real MCP connections and real-time learning.

**Location:** `streamlit-app/pages/2_🧪_Dual_Orchestration_Lab.py`

> **First Time Setup?** Follow [INSTALLATION.md](INSTALLATION.md) for complete installation instructions from cloning the repo to running the app.

---

## Features

### ✅ What's Working Now

1. **🔌 Real MCP Connections**
   - One-click connection to actual MCP servers
   - Connect to BioMCP, PubChem, Literature, and more
   - Live status monitoring
   - Graceful fallback to simulated mode if connection fails

2. **🚀 Quick Demo Tab**
   - Execute queries with REAL MCP calls or simulation
   - See bidirectional learning in action
   - Choose from preset scenarios or custom queries
   - Live execution visualization
   - Real-time performance tracking

3. **📊 Learning Dashboard Tab**
   - MCP performance metrics (queries, success rate, avg time)
   - Track real vs simulated MCP calls
   - Query type routing intelligence
   - Agent learning insights
   - Updates in real-time as you use the system

4. **🔧 Tool Composer Tab**
   - Create multi-step workflows
   - Define composed tools with multiple MCP steps
   - (Tool execution and reuse - coming soon)

5. **🧠 Research Sessions Tab**
   - Create and manage research sessions
   - Track entities, hypotheses, and insights
   - Multi-turn context preservation
   - Session statistics

---

## How to Run

### 1. Start the Streamlit App

```bash
cd streamlit-app
venv/Scripts/python.exe -m streamlit run app.py
```

### 2. Navigate to the Demo Page

Once Streamlit opens in your browser:
- Look for the sidebar navigation
- Click on **"🧪 Dual Orchestration Lab"**

### 3. Connect to Real MCPs (Recommended)

Before running queries, click the **"🔌 Connect to MCPs"** button at the top of the page.

**What happens:**
- System attempts to connect to all configured MCP servers
- Connection status is displayed for each server
- Successfully connected MCPs will be used for real queries
- Failed connections gracefully fall back to simulated mode

**Tip:** You can expand "MCP Connection Details" to see which servers connected successfully.

### 4. Run Your First Demo

**Option A: Quick Preset Scenarios (with Real MCPs)**

1. In the "Quick Demo" tab, select a preset scenario:
   - **Scenario 1:** Intelligent Query Routing
   - **Scenario 2:** Multi-Step Workflow
   - **Scenario 3:** Research Session

2. Click **Execute**

3. Watch the live execution view showing:
   - Query analysis
   - MCP selection
   - Performance metrics
   - Bidirectional learning feedback
   - Results

**Option B: Custom Query**

1. Select "Custom Query"
2. Enter your own query (examples below)
3. Click **Execute**

---

## Demo Queries

### Inhibitor Search (Routes to BioMCP)
```
Find inhibitors of BRCA1
What are PARP inhibitors for breast cancer?
Show me kinase inhibitors for EGFR
```

### Gene Information (Routes to BioMCP)
```
What is BRCA1?
Tell me about TP53 gene
Find information about EGFR
```

### Chemical Search (Routes to PubChem)
```
What is the molecular formula of aspirin?
Tell me about caffeine structure
Find the molecular weight of ibuprofen
```

### Clinical Trials (Routes to BioMCP)
```
What clinical trials exist for breast cancer?
Show me trials for Olaparib
Find BRCA1-related clinical studies
```

---

## What to Watch For

### 🔌 Real MCP vs Simulated Execution

**The demo intelligently uses real or simulated data:**

- **With MCPs Connected:**
  - You'll see "(REAL)" in the execution spinner
  - Results come from actual MCP servers
  - Performance metrics reflect real latency
  - Learning dashboard shows "✓ X real calls"

- **Without MCPs Connected:**
  - You'll see "(SIMULATED)" in the execution spinner
  - Results are preset demo data
  - Still demonstrates the learning architecture
  - Learning dashboard shows "⊙ Simulated"

### 🔄 Bidirectional Learning in Action

**As you execute queries, you'll see:**

1. **MCP → Agent Learning**
   - System tracks which MCP succeeded (real or simulated)
   - Records actual performance metrics (latency, success rate)
   - Sends recommendation to Agent layer

2. **Agent → MCP Learning**
   - Agent learns MCP preferences for query types
   - Patterns recorded in Performance Knowledge Base
   - Future queries routed more intelligently

3. **Real-Time Dashboard Updates**
   - Switch to "Learning Dashboard" tab
   - See total queries and % that were real MCP calls
   - View MCP performance metrics update
   - View routing intelligence patterns
   - Check agent learnings

### 📈 Performance Metrics

The system tracks:
- **Per-MCP:** Queries executed, success rate, average latency
- **Per-Query-Type:** Which MCP works best for which query type
- **Agent Learning:** What the agents have learned about MCP preferences

### Example Learning Pattern

After running:
1. "Find inhibitors of BRCA1" → Routes to BioMCP → Success
2. "What are PARP inhibitors?" → Routes to BioMCP → Success
3. "Show me kinase inhibitors" → Routes to BioMCP → Success

**Learning Dashboard will show:**
```
Query Type Routing Intelligence:
✓ inhibitor_search → biomcp (learned from 3 queries)

Agent Learning:
- Query Agent: Learned that biomcp is optimal for inhibitor_search
- Query Agent: biomcp excels at inhibitor_search queries
```

---

## Demo Flow for Supervisor

### 5-Minute Walkthrough

**Minute 1: Introduction & Setup**
- "This is the Dual Orchestration Lab showcasing our novel architecture"
- Click **"🔌 Connect to MCPs"** button
- Show connection status as servers connect
- "We're now connected to real biomedical data sources"
- Show the four tabs: Quick Demo, Learning Dashboard, Tool Composer, Research Sessions

**Minute 2: Execute First Query (REAL MCP)**
- Select "Scenario 1: Intelligent Query Routing"
- Click Execute
- Point out:
  - Query analysis detecting "inhibitor_search"
  - System recommending BioMCP
  - **(REAL)** indicator showing actual MCP call
  - Real execution time from actual server
  - Real results displayed from BioMCP
  - Bidirectional learning feedback

**Minute 3: Show Learning Dashboard**
- Switch to "Learning Dashboard" tab
- Show MCP performance metrics
- Show routing intelligence: "inhibitor_search → biomcp"
- Show agent learnings

**Minute 4: Execute Different Query Types**
- Go back to Quick Demo
- Run a chemical search query
- Run a gene information query
- Show how the system routes to different MCPs
- Switch back to dashboard to show updated metrics

**Minute 5: Research Session Demo**
- Go to Research Sessions tab
- Create new session
- Run multi-turn queries (can go back to Quick Demo for this)
- Show entity tracking, hypothesis formation

**Wrap Up:**
"This demonstrates the three novel features:
1. Bidirectional learning between MCP and Agent layers
2. Intelligent routing based on learned patterns
3. Session memory for multi-turn research

Next steps: Real MCP integration, tool composition execution, advanced visualizations"

---

## Current State vs Full Vision

### ✅ Implemented (Phase 1 Complete!)

- Interactive Streamlit demo page
- Four-tab navigation
- **Real MCP server connections** ✅ NEW!
- **One-click MCP connection with status monitoring** ✅ NEW!
- **Actual MCP calls with real data** ✅ NEW!
- Query execution with live updates
- **Real vs simulated mode detection** ✅ NEW!
- Performance tracking and metrics (real and simulated)
- Bidirectional learning visualization
- Learning dashboard with real-time updates
- **Track % of queries using real MCPs** ✅ NEW!
- Query history tracking
- Research session management (basic)

### ⏳ Coming Soon (Phase 2-3)

- Enhanced result parsing (extract entities from MCP responses)
- Tool composition execution (UI is ready, backend pending)
- Auto entity extraction from real results
- Hypothesis formation based on actual data
- Advanced visualizations (entity graphs, workflow diagrams)
- Session persistence and export
- More sophisticated query routing based on learned patterns

---

## Troubleshooting

### Demo Page Not Showing

**Issue:** Don't see "Dual Orchestration Lab" in sidebar

**Fix:**
- Make sure you're running from `streamlit-app/` directory
- Check that `pages/` folder exists
- Verify file is named `2_🧪_Dual_Orchestration_Lab.py`

### Module Import Errors

**Issue:** `ModuleNotFoundError` for orchestration modules

**Fix:**
- Make sure all orchestration modules are in `streamlit-app/orchestration/`
- Check that `__init__.py` exists in orchestration folder
- Verify Python path includes parent directory

### No Metrics Showing

**Issue:** Learning Dashboard shows "No queries executed yet"

**Fix:**
- Go to Quick Demo tab first
- Execute at least one query
- Then return to Learning Dashboard

---

## Next Steps for Development

1. **Connect Real MCPs**
   - Integrate actual MCP server initialization
   - Replace simulated execution with real calls
   - Parse actual results

2. **Tool Composition Backend**
   - Implement composed tool execution
   - Save/load composed tools
   - Tool reuse functionality

3. **Enhanced Visualizations**
   - Entity relationship graphs
   - Workflow execution timelines
   - Performance trend charts

4. **Session Enhancements**
   - Auto entity extraction from results
   - Hypothesis formation logic
   - Proactive suggestions

---

## Files Created

- `streamlit-app/pages/2_🧪_Dual_Orchestration_Lab.py` - Main demo page
- `DEMO_PLAN.md` - Comprehensive demo architecture plan
- `DEMO_QUICKSTART.md` - This quick start guide

---

## Questions?

The demo is designed to be self-explanatory, but key points:

1. **It's interactive** - Try different queries and watch the system learn
2. **It tracks everything** - All metrics update in real-time
3. **It's visual** - Shows the learning process happening
4. **It's reproducible** - Anyone can run it and see the same results

**Goal:** Demonstrate that the dual orchestration architecture isn't just theory - it's a working system that learns and improves with use.
