# Installation Guide

Complete guide to set up and run the Dual Orchestration System on any machine.

---

## Prerequisites

### Required Software

1. **Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **Node.js 18+** (for MCP servers)
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version` and `npm --version`

3. **Git**
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_ORG/BU-Senior-Design-EMD-Serono.git
cd BU-Senior-Design-EMD-Serono
```

---

## Step 2: Set Up Python Environment

### Create Virtual Environment

```bash
cd streamlit-app
python -m venv venv
```

### Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies installed:**
- `streamlit` - Web UI framework
- `mcp` - Model Context Protocol SDK
- `langchain` - LLM framework
- `aiohttp`, `asyncio` - Async operations

---

## Step 3: Set Up MCP Servers

MCP servers provide access to external data sources (PubChem, Literature, etc.).

### Install Node Dependencies for Each MCP Server

```bash
# PubChem MCP
cd ../servers/pubchem
npm install

# Literature MCP
cd ../literature
npm install

# Data Analysis MCP
cd ../data_analysis
npm install

# Web Knowledge MCP
cd ../web_knowledge
npm install

# Return to streamlit-app directory
cd ../../streamlit-app
```

---

## Step 4: Run the Application

### Start Streamlit

```bash
# Make sure you're in streamlit-app directory
# With virtual environment activated

streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.X.X:8501
```

### Open in Browser

The app will automatically open in your default browser at `http://localhost:8501`

---

## Step 5: Navigate to Demo

1. In the Streamlit app, look at the **left sidebar**
2. Click on **"🧪 Dual Orchestration Lab"**
3. Click **"🔌 Connect to MCPs"** button to connect to real data sources

---

## Verify Installation

### Check MCP Connections

After clicking "Connect to MCPs", you should see:
- ✓ **pubchem**: Connected
- ✓ **literature**: Connected
- ✓ **data_analysis**: Connected
- ✓ **web_knowledge**: Connected

**Note:** Some MCPs (like biomcp) may timeout but the system will gracefully fall back to simulated mode.

### Run Test Query

1. In the "Quick Demo" tab
2. Enter query: "What is the molecular formula of aspirin?"
3. Click **Execute**
4. You should see:
   - Query type detected
   - Agent assignment (Chemical Agent)
   - MCP selected (pubchem)
   - Real results from PubChem

---

## Troubleshooting

### Issue: Python package installation fails

**Solution:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Issue: MCP servers won't connect

**Solution:**
1. Verify Node.js is installed: `node --version`
2. Check MCP server dependencies:
   ```bash
   cd servers/pubchem
   npm install
   ```
3. Test MCP server manually:
   ```bash
   node index.js
   # Should output: "PubChem MCP server running on stdio"
   # Press Ctrl+C to exit
   ```

### Issue: Port 8501 already in use

**Solution:**
```bash
streamlit run app.py --server.port 8502
```

### Issue: "Module not found" errors

**Solution:**
Ensure virtual environment is activated:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Then verify
which python  # Should point to venv
```

---

## Directory Structure

After installation, your directory should look like:

```
BU-Senior-Design-EMD-Serono/
├── streamlit-app/
│   ├── venv/                    # Python virtual environment
│   ├── app.py                   # Main Streamlit app
│   ├── pages/                   # Multi-page app
│   │   └── 2_🧪_Dual_Orchestration_Lab.py
│   ├── orchestration/           # Orchestration logic
│   ├── agents/                  # Agent implementations
│   ├── models/                  # Data models
│   ├── mcp_tools.py            # MCP wrapper
│   └── requirements.txt        # Python dependencies
├── servers/                     # MCP servers
│   ├── pubchem/
│   │   ├── index.js
│   │   └── node_modules/
│   ├── literature/
│   ├── data_analysis/
│   └── web_knowledge/
└── docs/                       # Documentation

```

---

## Next Steps

- Read [DEMO_QUICKSTART.md](DEMO_QUICKSTART.md) for demo walkthrough
- See [DUAL_ORCHESTRATION_ARCHITECTURE.md](DUAL_ORCHESTRATION_ARCHITECTURE.md) for technical details
- Check [DUAL_ORCHESTRATION_README.md](DUAL_ORCHESTRATION_README.md) for feature overview

---

## Need Help?

- Check the troubleshooting section above
- Review error messages in the terminal where Streamlit is running
- Ensure all prerequisites are properly installed
- Verify MCP servers are working independently before running the full app
