# MCP Servers & Tools - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technologies](#technologies)
4. [MCP Servers](#mcp-servers)
5. [Complete Tool Reference](#complete-tool-reference)
6. [API Endpoints & Data Sources](#api-endpoints--data-sources)
7. [Setup & Configuration](#setup--configuration)
8. [Testing & Verification](#testing--verification)
9. [Troubleshooting](#troubleshooting)
10. [Future Enhancements](#future-enhancements)

---

## Overview

This system provides a **multi-agent research platform** with **5 specialized MCP (Model Context Protocol) servers** offering over **35+ tools** across chemical, biological, literature, data analysis, and web knowledge domains.

### Key Capabilities
- **Chemical compound analysis** (PubChem)
- **Biomedical research** (PubMed, clinical trials, variants, genes)
- **Scientific literature search** (PubMed, citations)
- **Statistical & sequence analysis** (correlations, DNA/protein analysis)
- **Web knowledge retrieval** (Wikipedia, gene information, clinical trials)

### System Statistics
- **Total MCP Servers**: 5
- **Total Tools Available**: 35+
- **Programming Languages**: Python, Node.js
- **Data Sources**: 15+ APIs and databases
- **Transport Protocol**: stdio (standard input/output)

---

## Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────┐
│         Streamlit UI (User Interface)               │
│         - Natural language input                    │
│         - Results visualization                     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│         Custom ReAct Agent (Ollama + Llama 3.2)     │
│         - Query understanding                       │
│         - Tool selection & execution                │
│         - Result synthesis                          │
└──────┬──────┬──────┬──────┬──────────────────────────┘
       │      │      │      │
       ▼      ▼      ▼      ▼      ▼
   ┌───────┬───────┬────────┬────────┬──────────┐
   │PubChem│BioMCP │Literatu│  Data  │   Web    │
   │  MCP  │  MCP  │re  MCP │Analysis│Knowledge │
   │Server │Server │ Server │  MCP   │   MCP    │
   └───┬───┴───┬───┴────┬───┴───┬────┴─────┬────┘
       │       │        │       │          │
       ▼       ▼        ▼       ▼          ▼
  ┌────────┬────────┬────────┬────────┬────────────┐
  │PubChem │PubMed  │PubMed  │In-Proc │Wikipedia   │
  │REST API│PubTator│E-utils │Calc    │NCBI APIs   │
  │        │Clin.gov│API     │        │Clin. Trials│
  └────────┴────────┴────────┴────────┴────────────┘
```

### MCP Communication Flow

```
User Query → Streamlit → Agent → MCP Wrapper → MCP Server (stdio) → External API → Results
```

Each MCP server runs as a separate process communicating via stdio protocol with the Python agent through the MCP SDK.

---

## Technologies

### Core Framework
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11.9+ | Core application & agent logic |
| **Node.js** | v20.16.0+ | MCP server runtime |
| **Streamlit** | 1.32.0+ | Web UI framework |
| **Ollama** | 0.12.6+ | Local LLM runtime |
| **Llama 3.2** | latest | Language model for agent |

### Agent & AI Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| **LangChain Core** | 1.0.1+ | Tool abstractions |
| **LangChain Ollama** | 0.1.0+ | Ollama LLM integration |
| **Custom ReAct Agent** | - | Hand-built agent (no LangChain agents) |

### MCP Integration
| Technology | Version | Purpose |
|------------|---------|---------|
| **MCP SDK (Python)** | 0.9.0+ | Python MCP client |
| **MCP SDK (Node.js)** | 1.20.0+ | Node.js MCP server framework |
| **biomcp-python** | 0.7.1+ | Biomedical MCP tools |
| **Stdio Transport** | - | Process communication |

### External APIs & Data Sources
| API/Service | Purpose | Rate Limits |
|-------------|---------|-------------|
| **PubChem PUG REST** | Chemical compound data | ~5 requests/second |
| **NCBI E-utilities** | PubMed, Gene, literature | 3 req/sec (no key), 10 req/sec (with key) |
| **PubTator3** | Biomedical entity recognition | Via BioMCP |
| **ClinicalTrials.gov API** | Clinical trial data | Public, no auth required |
| **MyVariant.info** | Variant annotations | Via BioMCP |
| **cBioPortal** | Cancer genomics | Via BioMCP |
| **Wikipedia REST API** | General knowledge | Public, rate-limited |
| **MyGene.info** | Gene information | Public API |
| **AlphaGenome** | Variant effect prediction | Via BioMCP |

---

## MCP Servers

### 1. PubChem MCP Server
**Location**: `servers/pubchem/`
**Language**: Node.js
**Status**: ✅ Active

**Description**: Chemical compound database integration

**Tools Provided** (2):
- `search_compounds_by_name`
- `get_compound_properties`

**Data Source**: PubChem PUG REST API
**Transport**: stdio

---

### 2. BioMCP Server
**Location**: `servers/bio/`
**Language**: Python (wrapper)
**Package**: biomcp-python
**Status**: ✅ Active

**Description**: Comprehensive biomedical research platform with 24 specialized tools

**Tools Provided** (24):

**Core Tools:**
- `think` - Sequential reasoning for biomedical analysis
- `search` - Cross-domain search (articles, trials, variants)
- `fetch` - Retrieve complete details for items

**Article Tools:**
- `article_searcher` - PubMed/PubTator3 and preprint search
- `article_getter` - Detailed article retrieval (PMID/DOI)

**Trial Tools:**
- `trial_searcher` - ClinicalTrials.gov or NCI CTS API
- `trial_getter` - Complete trial information
- `trial_protocol_getter` - Protocol-only retrieval
- `trial_references_getter` - Trial publications
- `trial_outcomes_getter` - Outcome measures and results
- `trial_locations_getter` - Site locations and contacts

**Variant Tools:**
- `variant_searcher` - MyVariant.info database
- `variant_getter` - Comprehensive variant annotations

**NCI-Specific Tools:**
- `enci_organization_searcher/getter` - NCI organization database
- `enci_intervention_searcher/getter` - Drug and device info
- `enci_biomarker_searcher` - Trial eligibility biomarkers
- `enci_disease_searcher` - Cancer condition vocabulary

**Gene/Disease/Drug Tools:**
- `gene_getter` - Real-time gene info (MyGene.info)
- `disease_getter` - Disease definitions and synonyms
- `drug_getter` - Drug/chemical annotations (MyChem.info)

**Data Sources**: PubMed, PubTator3, ClinicalTrials.gov, NCI CTS, MyVariant.info, cBioPortal, OncoKB, AlphaGenome
**Transport**: stdio

---

### 3. Literature MCP Server
**Location**: `servers/literature/`
**Language**: Node.js
**Status**: ✅ Active

**Description**: Scientific literature search and retrieval

**Tools Provided** (5):
- `search_pubmed` - Search PubMed by keywords
- `get_pubmed_abstract` - Retrieve full abstract by PMID
- `search_pubmed_by_author` - Search by author name
- `get_related_articles` - Find related articles
- `search_by_doi` - Retrieve article by DOI

**Data Source**: NCBI E-utilities API (PubMed)
**Transport**: stdio

---

### 4. Data Analysis MCP Server
**Location**: `servers/data_analysis/`
**Language**: Node.js
**Status**: ✅ Active

**Description**: Statistical calculations, correlations, sequence analysis, and molecular descriptors

**Tools Provided** (6):
- `calculate_statistics` - Mean, median, std dev, etc.
- `calculate_correlation` - Pearson correlation coefficient
- `perform_linear_regression` - Linear regression with R²
- `analyze_sequence` - DNA/protein sequence composition
- `calculate_molecular_descriptors` - Lipinski's Rule of Five
- `convert_units` - Scientific unit conversions

**Data Source**: In-process calculations (no external API)
**Transport**: stdio

---

### 5. Web/Knowledge MCP Server
**Location**: `servers/web_knowledge/`
**Language**: Node.js
**Status**: ✅ Active

**Description**: Web knowledge retrieval, Wikipedia, clinical trials, and gene information

**Tools Provided** (8):
- `search_wikipedia` - Search Wikipedia articles
- `get_wikipedia_page` - Get full Wikipedia page content
- `search_clinical_trials` - Search ClinicalTrials.gov
- `get_clinical_trial_details` - Get trial details by NCT ID
- `search_patents` - Patent search (limited)
- `get_drugbank_info` - Basic drug information
- `get_gene_info` - NCBI Gene database information
- `convert_identifiers` - Convert biomedical identifiers

**Data Sources**: Wikipedia REST API, ClinicalTrials.gov API v2, NCBI E-utilities, PubChem
**Transport**: stdio

---

## Complete Tool Reference

### PubChem Server Tools

#### `search_compounds_by_name`
**Description**: Search for chemical compounds by name

**Parameters**:
```json
{
  "name": "string (required)",       // e.g., "caffeine"
  "max_results": "number (optional)" // default: 5
}
```

**Returns**:
```json
{
  "cids": [2519, ...],
  "count": 10,
  "source": "PubChem PUG REST API"
}
```

**Example**:
```
Query: search_compounds_by_name name="aspirin" max_results=3
```

**Endpoint**: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON`

---

#### `get_compound_properties`
**Description**: Retrieve detailed properties for a compound by CID

**Parameters**:
```json
{
  "cid": "number (required)" // PubChem Compound ID
}
```

**Returns**:
```json
{
  "CID": 2519,
  "MolecularFormula": "C8H10N4O2",
  "MolecularWeight": 194.19,
  "IUPACName": "...",
  "IsomericSMILES": "...",
  "InChI": "...",
  "InChIKey": "...",
  "Link": "https://pubchem.ncbi.nlm.nih.gov/compound/2519"
}
```

**Endpoint**: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/{props}/JSON`

---

### BioMCP Server Tools

#### `search` (Core Tool)
**Description**: Cross-domain biomedical searching

**Parameters**:
```json
{
  "query": "string (required)",         // Natural language or field-specific
  "domain": "string (required)",        // "article", "trial", or "variant"
  "get_schema": "boolean (optional)",   // Retrieve searchable fields
  "explain_query": "boolean (optional)" // Show query parsing
}
```

**Returns**: Domain-specific results with cBioPortal integration

**Examples**:
```
- Search articles about BRCA1: domain="article" query="BRCA1"
- Find diabetes trials: domain="trial" query="diabetes"
- Search variants: domain="variant" query="rs123456"
```

---

#### `article_searcher`
**Description**: Search PubMed/PubTator3 and preprints

**Parameters**:
```json
{
  "query": "string (required)",
  "max_results": "number (optional)",
  "filters": "object (optional)"
}
```

**Data Source**: PubMed, PubTator3, bioRxiv, medRxiv

---

#### `trial_searcher`
**Description**: Search ClinicalTrials.gov or NCI CTS API

**Parameters**:
```json
{
  "condition": "string (optional)",
  "intervention": "string (optional)",
  "phase": "string (optional)",
  "status": "string (optional)"
}
```

**Data Source**: ClinicalTrials.gov, NCI Clinical Trials Search API

---

#### `gene_getter`
**Description**: Retrieve real-time gene information

**Parameters**:
```json
{
  "gene_symbol": "string (required)" // e.g., "BRCA1", "TP53"
}
```

**Data Source**: MyGene.info

---

### Literature Server Tools

#### `search_pubmed`
**Description**: Search PubMed database for research articles

**Parameters**:
```json
{
  "query": "string (required)",       // Search keywords
  "max_results": "number (optional)", // default: 10, max: 100
  "sort": "string (optional)"         // "relevance", "date", "cited"
}
```

**Returns**:
```json
{
  "query": "cancer immunotherapy",
  "count": 10,
  "results": [
    {
      "pmid": "12345678",
      "title": "...",
      "authors": "Smith J, Doe A et al.",
      "journal": "Nature",
      "pubdate": "2024",
      "link": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    }
  ]
}
```

**Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`

---

#### `get_pubmed_abstract`
**Description**: Retrieve full abstract and metadata

**Parameters**:
```json
{
  "pmid": "string (required)" // e.g., "12345678"
}
```

**Returns**:
```json
{
  "pmid": "12345678",
  "title": "...",
  "abstract": "Full abstract text...",
  "journal": "Nature",
  "year": "2024",
  "link": "..."
}
```

**Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed`

---

#### `search_pubmed_by_author`
**Description**: Search articles by author name

**Parameters**:
```json
{
  "author": "string (required)",      // e.g., "Smith J"
  "max_results": "number (optional)"  // default: 10
}
```

---

#### `get_related_articles`
**Description**: Find articles related to a given PMID

**Parameters**:
```json
{
  "pmid": "string (required)",
  "max_results": "number (optional)" // default: 5
}
```

**Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi`

---

#### `search_by_doi`
**Description**: Retrieve article by DOI

**Parameters**:
```json
{
  "doi": "string (required)" // e.g., "10.1038/nature12345"
}
```

---

### Data Analysis Server Tools

#### `calculate_statistics`
**Description**: Calculate statistical measures for a dataset

**Parameters**:
```json
{
  "values": "array of numbers (required)" // [1.2, 3.4, 5.6, ...]
}
```

**Returns**:
```json
{
  "statistics": {
    "n": 100,
    "sum": 523.4,
    "mean": 5.234,
    "median": 4.8,
    "variance": 12.3,
    "stdDev": 3.51,
    "min": 0.1,
    "max": 15.7
  }
}
```

---

#### `calculate_correlation`
**Description**: Calculate Pearson correlation coefficient

**Parameters**:
```json
{
  "x": "array of numbers (required)",
  "y": "array of numbers (required)"
}
```

**Returns**:
```json
{
  "correlation": 0.8542,
  "interpretation": "Strong correlation",
  "direction": "Positive",
  "n": 50
}
```

---

#### `perform_linear_regression`
**Description**: Perform linear regression analysis

**Parameters**:
```json
{
  "x": "array of numbers (required)", // Independent variable
  "y": "array of numbers (required)"  // Dependent variable
}
```

**Returns**:
```json
{
  "regression": {
    "slope": 2.345,
    "intercept": 1.234,
    "rSquared": 0.892,
    "equation": "y = 2.345x + 1.234"
  },
  "interpretation": "The model explains 89.2% of the variance"
}
```

---

#### `analyze_sequence`
**Description**: Analyze DNA or protein sequence composition

**Parameters**:
```json
{
  "sequence": "string (required)",      // Sequence string
  "type": "string (required)"           // "DNA" or "PROTEIN"
}
```

**Returns** (DNA example):
```json
{
  "type": "DNA",
  "length": 150,
  "composition": {
    "A": 40,
    "T": 35,
    "G": 38,
    "C": 37
  },
  "gcContent": "50.00%",
  "atContent": "50.00%",
  "molecularWeight": "49500.00 Da (approx)"
}
```

**Returns** (Protein example):
```json
{
  "type": "Protein",
  "length": 250,
  "composition": {
    "A": 15,
    "G": 20,
    "L": 18,
    ...
  },
  "molecularWeight": "27500.00 Da (approx)",
  "uniqueAminoAcids": 18
}
```

---

#### `calculate_molecular_descriptors`
**Description**: Calculate Lipinski's Rule of Five for drug-likeness

**Parameters**:
```json
{
  "molecularWeight": "number (required)",      // Da
  "logP": "number (optional)",                 // Partition coefficient
  "hydrogenBondDonors": "number (optional)",
  "hydrogenBondAcceptors": "number (optional)"
}
```

**Returns**:
```json
{
  "lipinskiRuleOfFive": {
    "molecularWeight": 450.5,
    "logP": 3.2,
    "hydrogenBondDonors": 2,
    "hydrogenBondAcceptors": 8,
    "violations": [],
    "drugLike": true,
    "summary": "Compound passes Lipinski's Rule of Five"
  }
}
```

---

#### `convert_units`
**Description**: Convert between scientific units

**Parameters**:
```json
{
  "value": "number (required)",
  "fromUnit": "string (required)",    // e.g., "mg", "mL", "mM"
  "toUnit": "string (required)",      // Target unit
  "molecularWeight": "number (optional)" // For molarity conversions
}
```

**Supported Conversions**:
- Mass: mg ↔ g ↔ ug
- Volume: mL ↔ L ↔ uL
- Molarity: M ↔ mM ↔ uM
- Mass ↔ Molarity (requires MW)

**Returns**:
```json
{
  "original": "100 mg",
  "converted": "0.100000 g",
  "conversionFactor": "0.001000"
}
```

---

### Web/Knowledge Server Tools

#### `search_wikipedia`
**Description**: Search Wikipedia for articles

**Parameters**:
```json
{
  "query": "string (required)",
  "sentences": "number (optional)" // default: 3
}
```

**Returns**:
```json
{
  "title": "Cancer",
  "summary": "Cancer is a group of diseases...",
  "url": "https://en.wikipedia.org/wiki/Cancer",
  "thumbnail": "https://..."
}
```

**Endpoint**: `https://en.wikipedia.org/api/rest_v1/page/summary/{query}`

---

#### `search_clinical_trials`
**Description**: Search ClinicalTrials.gov

**Parameters**:
```json
{
  "condition": "string (optional)",    // e.g., "breast cancer"
  "intervention": "string (optional)", // e.g., "pembrolizumab"
  "status": "string (optional)",       // "recruiting", "completed"
  "max_results": "number (optional)"   // default: 10, max: 50
}
```

**Returns**:
```json
{
  "query": {...},
  "count": 10,
  "trials": [
    {
      "nctId": "NCT12345678",
      "title": "Study of Drug X in Cancer",
      "status": "Recruiting",
      "condition": "Breast Cancer",
      "intervention": "Drug X",
      "phase": "Phase 3",
      "enrollment": 500,
      "startDate": "2024-01-15",
      "url": "https://clinicaltrials.gov/study/NCT12345678"
    }
  ]
}
```

**Endpoint**: `https://clinicaltrials.gov/api/v2/studies`

---

#### `get_clinical_trial_details`
**Description**: Get detailed information about a clinical trial

**Parameters**:
```json
{
  "nct_id": "string (required)" // e.g., "NCT12345678"
}
```

**Returns**: Comprehensive trial data including eligibility criteria, locations, interventions, outcomes

**Endpoint**: `https://clinicaltrials.gov/api/v2/studies/{nct_id}`

---

#### `get_gene_info`
**Description**: Get gene information from NCBI Gene database

**Parameters**:
```json
{
  "gene_symbol": "string (required)", // e.g., "BRCA1", "TP53"
  "species": "string (optional)"      // default: "human"
}
```

**Returns**:
```json
{
  "geneId": "672",
  "symbol": "BRCA1",
  "description": "BRCA1 DNA repair associated",
  "chromosome": "17",
  "location": "17q21.31",
  "aliases": ["BRCC1", "FANCS", ...],
  "summary": "This gene encodes a nuclear phosphoprotein...",
  "url": "https://www.ncbi.nlm.nih.gov/gene/672"
}
```

**Endpoint**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene`

---

#### `get_drugbank_info`
**Description**: Get basic drug information (via PubChem)

**Parameters**:
```json
{
  "drug_name": "string (required)" // e.g., "aspirin", "metformin"
}
```

**Returns**:
```json
{
  "drug": "aspirin",
  "cid": 2244,
  "molecularFormula": "C9H8O4",
  "molecularWeight": 180.16,
  "iupacName": "2-acetyloxybenzoic acid",
  "pubchemUrl": "https://pubchem.ncbi.nlm.nih.gov/compound/2244"
}
```

---

## API Endpoints & Data Sources

### Complete Endpoint Reference

| API Endpoint | Data Source | Purpose | Authentication |
|--------------|-------------|---------|----------------|
| `https://pubchem.ncbi.nlm.nih.gov/rest/pug/` | PubChem | Chemical compounds | None required |
| `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` | NCBI E-utilities | PubMed, Gene, literature | Optional API key |
| `https://clinicaltrials.gov/api/v2/` | ClinicalTrials.gov | Clinical trials | None required |
| `https://en.wikipedia.org/api/rest_v1/` | Wikipedia | General knowledge | None required |
| Via BioMCP: PubTator3 | PubTator3 | Entity recognition | Via BioMCP |
| Via BioMCP: MyVariant.info | MyVariant | Variant annotations | Via BioMCP |
| Via BioMCP: cBioPortal | cBioPortal | Cancer genomics | Optional token |
| Via BioMCP: OncoKB | OncoKB | Oncology knowledge | Optional token |
| Via BioMCP: MyGene.info | MyGene | Gene information | None required |
| Via BioMCP: MyChem.info | MyChem | Chemical/drug info | None required |

### Rate Limits

| API | Anonymous Limit | Authenticated Limit | Notes |
|-----|----------------|---------------------|-------|
| PubChem PUG REST | ~5 req/sec | Same | May throttle on heavy use |
| NCBI E-utilities | 3 req/sec | 10 req/sec | API key recommended |
| ClinicalTrials.gov | Public | N/A | No explicit limit |
| Wikipedia | Reasonable use | N/A | Rate-limited on abuse |
| BioMCP APIs | Varies | Varies | Depends on backend API |

---

## Setup & Configuration

### Prerequisites

1. **Python 3.11.9+**
2. **Node.js v20.16.0+**
3. **Ollama 0.12.6+** with Llama 3.2 model
4. **Git** (for cloning repository)

### Installation Steps

#### 1. Install Ollama and Pull Model
```bash
# Download Ollama from https://ollama.com/download
# Then pull the model:
ollama pull llama3.2

# Verify:
ollama list
```

#### 2. Setup Python Environment
```bash
cd streamlit-app

# Create virtual environment
python -m venv venv

# Activate (Windows):
venv\Scripts\activate

# Activate (macOS/Linux):
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Setup Node.js MCP Servers
```bash
# Literature server
cd ../servers/literature
npm install

# Data analysis server
cd ../data_analysis
npm install

# Web/knowledge server
cd ../web_knowledge
npm install

# PubChem server (already setup)
cd ../pubchem
# Dependencies already installed
```

#### 4. Verify BioMCP Installation
```bash
cd streamlit-app
venv/Scripts/python -c "import biomcp; print('BioMCP installed successfully')"
```

### Configuration Files

#### `streamlit-app/config.py`
```python
# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# MCP Server configurations
MCP_SERVERS = {
    "pubchem": {
        "command": "node",
        "args": ["../servers/pubchem/index.js"],
        "description": "PubChem MCP server for chemical compound data"
    },
    "biomcp": {
        "command": "python",
        "args": ["../servers/bio/run_biomcp.py"],
        "description": "BioMCP server - Comprehensive biomedical research"
    },
    "literature": {
        "command": "node",
        "args": ["../servers/literature/index.js"],
        "description": "Literature MCP server for PubMed articles"
    },
    "data_analysis": {
        "command": "node",
        "args": ["../servers/data_analysis/index.js"],
        "description": "Data Analysis MCP server for statistics"
    },
    "web_knowledge": {
        "command": "node",
        "args": ["../servers/web_knowledge/index.js"],
        "description": "Web/Knowledge MCP server"
    }
}

# Agent settings
AGENT_MAX_ITERATIONS = 10
AGENT_VERBOSE = True
```

---

## Testing & Verification

### Test Individual MCP Servers

#### Test PubChem Server
```bash
cd servers/pubchem
node index.js
# Server should start and output: "PubChem MCP server running on stdio"
# Press Ctrl+C to exit
```

#### Test Literature Server
```bash
cd servers/literature
node index.js
# Should output: "Literature MCP server running on stdio"
```

#### Test Data Analysis Server
```bash
cd servers/data_analysis
node index.js
# Should output: "Data Analysis MCP server running on stdio"
```

#### Test Web/Knowledge Server
```bash
cd servers/web_knowledge
node index.js
# Should output: "Web/Knowledge MCP server running on stdio"
```

#### Test BioMCP Server
```bash
cd servers/bio
python run_biomcp.py
# Should start BioMCP server
```

### Test Complete Integration

```bash
cd streamlit-app
streamlit run app.py
```

**Expected Startup Output**:
```
Connecting to MCP server: pubchem...
✓ Connected to pubchem, loaded 2 tools
Connecting to MCP server: biomcp...
✓ Connected to biomcp, loaded 24 tools
Connecting to MCP server: literature...
✓ Connected to literature, loaded 5 tools
Connecting to MCP server: data_analysis...
✓ Connected to data_analysis, loaded 6 tools
Connecting to MCP server: web_knowledge...
✓ Connected to web_knowledge, loaded 8 tools

Total tools available: 45
```

### Example Test Queries

Try these queries in the Streamlit interface:

**Chemistry**:
- "What is the molecular formula of caffeine?"
- "Search for aspirin and tell me its molecular weight"

**Biomedical Research**:
- "Find recent articles about CRISPR gene editing"
- "Search for clinical trials for breast cancer"
- "What is the function of the BRCA1 gene?"

**Data Analysis**:
- "Calculate statistics for these values: [1.2, 3.4, 5.6, 7.8, 9.0]"
- "Analyze this DNA sequence: ATCGATCGATCG"
- "Calculate molecular descriptors for a compound with MW=450 and logP=3.2"

**Literature**:
- "Search PubMed for articles about Alzheimer's disease"
- "Get the abstract for PMID 12345678"

**Web/Knowledge**:
- "Search Wikipedia for information about cancer immunotherapy"
- "Find clinical trials for diabetes in Boston"
- "Get information about the TP53 gene"

---

## Troubleshooting

### Common Issues

#### Issue: "Failed to connect to MCP server"
**Symptoms**: Server connection error on startup

**Solutions**:
1. Verify Node.js is installed: `node --version`
2. Check npm dependencies are installed in server directories
3. Test server independently (see Testing section)
4. Check server paths in `config.py`

#### Issue: "BioMCP not found"
**Symptoms**: `ModuleNotFoundError: No module named 'biomcp'`

**Solutions**:
1. Verify installation: `pip show biomcp-python`
2. Reinstall: `pip install biomcp-python`
3. Check virtual environment is activated
4. Verify Python path in bio server wrapper

#### Issue: "Ollama connection failed"
**Symptoms**: Cannot connect to Ollama LLM

**Solutions**:
1. Check Ollama is running: `ollama list`
2. Start Ollama: `ollama serve`
3. Verify model is installed: `ollama pull llama3.2`
4. Check `OLLAMA_BASE_URL` in `config.py`

#### Issue: "No tools were loaded"
**Symptoms**: Agent has no tools available

**Solutions**:
1. Check terminal output for connection errors
2. Verify all servers start independently
3. Check MCP SDK versions match
4. Review server logs for errors

#### Issue: "API rate limit exceeded"
**Symptoms**: Errors from external APIs

**Solutions**:
1. For NCBI E-utilities: Get API key and add to environment
2. Reduce query frequency
3. Implement caching (future enhancement)
4. Use alternative data sources

---

## Future Enhancements

### Phase 1: Orchestration Layer
- [ ] **Multi-agent coordinator** - Supervisor agent that routes queries
- [ ] **Parallel tool execution** - Run independent queries simultaneously
- [ ] **Task decomposition** - Break complex queries into sub-tasks
- [ ] **Result synthesis** - Combine results from multiple agents

### Phase 2: Enhanced Capabilities
- [ ] **Conversation memory** - Remember previous queries
- [ ] **Caching layer** - Cache API responses
- [ ] **Rate limiting** - Intelligent request throttling
- [ ] **Error recovery** - Automatic retry and fallback

### Phase 3: Additional MCP Servers
- [ ] **Protein Structure MCP** - AlphaFold, PDB integration
- [ ] **Pathway Analysis MCP** - KEGG, Reactome pathways
- [ ] **Disease Database MCP** - OMIM, DisGeNET
- [ ] **Drug Interaction MCP** - DrugBank interactions

### Phase 4: UI/UX Improvements
- [ ] **Workflow visualization** - Show agent decision tree
- [ ] **Result export** - Download as PDF/JSON/CSV
- [ ] **Query templates** - Pre-built query patterns
- [ ] **Visualization tools** - Chemical structures, networks

### Phase 5: Advanced Features
- [ ] **Custom tool creation** - User-defined MCP tools
- [ ] **Tool chaining** - Automated multi-step workflows
- [ ] **Batch processing** - Process multiple queries
- [ ] **API authentication** - Secure API key management

---

## Summary

This MCP server infrastructure provides a comprehensive, extensible platform for multi-domain scientific research. With **5 specialized servers** offering **45+ tools**, the system can handle complex queries spanning chemistry, biomedicine, literature, data analysis, and general knowledge.

### Key Achievements
✅ **5 MCP servers** implemented and integrated
✅ **45+ specialized tools** across multiple domains
✅ **15+ external APIs** integrated
✅ **Biomedical research** capabilities via BioMCP
✅ **Statistical analysis** and sequence analysis
✅ **Literature search** with PubMed integration
✅ **Chemical compound** analysis
✅ **Web knowledge** retrieval
✅ **Extensible architecture** for future growth

### Next Steps
1. Test all servers individually
2. Run integration tests
3. Begin Phase 1 orchestration implementation
4. Add conversation memory
5. Implement parallel execution

---

## Contact & Support

For issues, questions, or contributions related to this BU Senior Design EMD Serono project, please contact the project team.

**Documentation Version**: 1.0
**Last Updated**: November 2025
**Project**: BU Senior Design EMD Serono
**Repository**: BU-Senior-Design-EMD-Serono
