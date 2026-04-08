# BU-Senior-Design-EMD-Serono
---

# MCP-Based Multi-Agent AI System for Drug Development Intelligence

## Overview

This project aims to develop a **Model Context Protocol (MCP)**–enabled multi-agent AI system designed to **gather, normalize, and summarize drug development information** across diverse biomedical data sources. The system is built for **EMD Serono’s Competitive Intelligence (CI)** workflows to accelerate evidence-based decision-making and improve visibility across all four clinical trial phases.

---

## Objectives

* **Aggregate and standardize** data from literature, patents, chemical databases, regulatory filings, and scientific news.
* **Leverage multi-agent collaboration** for automated retrieval, synthesis, and summarization of drug development information.
* **Integrate MCP servers** to enable interoperability between models, data pipelines, and tool providers.
* **Develop an observability layer** that ensures auditability, transparency, and compliance in all agent actions.

---

## System Architecture

### Chat Interface (Left Panel)

The primary interaction point. Users ask questions about drugs, targets, or therapeutic areas. Queries flow through the **MCPAgent**, which operates an agentic tool-calling loop:

```
User question -> MCPAgent -> LLM decides which MCP tool to call
    -> Execute tool (PubChem, BioMCP, literature, etc.)
    -> Feed result back to LLM -> Repeat up to 10 iterations
    -> Final synthesized answer
```

All MCP tool calls are mediated through the **Context Forge Gateway** for governance, audit logging, compliance checks, and rate limiting.

### Report Generation Panel (Right Panel) — Multi-Agent MCP Orchestration

A dedicated panel separated from the chat interface for generating structured pharmaceutical reports. The panel automatically detects the drug or target being discussed in the chat and allows the user to generate formal reports on demand.

**How it works:**

1. **Drug Detection** — The `drug_extractor` module analyzes conversation history using the LLM to identify the primary drug/compound/target being discussed. Results are cached and only re-extracted when new messages are added.

2. **Report Type Selection** — Users select from available report types (currently Competitive Intelligence; extensible to Target CV, Clinical Summary, Biomarker Landscape, etc.).

3. **Multi-Agent Report Generation** — Clicking "Generate Report" invokes the `ReportAgent`, which orchestrates a full multi-agent workflow:

   ```
   ReportAgent creates 5 specialized agents (shared MCPOrchestrator + LLM)
       |
       v
   All 18 EMD sections dispatched IN PARALLEL (asyncio.gather)
       |
       |   For each section (e.g., Section 9: Competitive Landscape):
       |       |
       |       v
       |   _gather_agent_data() — dispatches to 1-3 agents IN PARALLEL
       |       |
       |       +---> ClinicalAgent.process()
       |       |         calls MCP tools: trial_searcher, openfda_adverse_searcher, etc.
       |       +---> ChemicalAgent.process()
       |       |         calls MCP tools: search_compounds_by_name, drug_getter, etc.
       |       +---> LiteratureAgent.process()
       |                 calls MCP tools: article_searcher, search_pubmed, etc.
       |       |
       |       v
       |   _synthesize_section() — LLM writes section using real MCP data
       |       + EMD template structure + agent expert analyses
       |
       v
   _compile_report() — stitches 18 sections into final document
   ```

   Every specialized agent follows a **3-phase pattern**:
   - **Phase 1 — Gather**: Call MCP tools in parallel via `_call_mcp_tools_parallel()`
   - **Phase 2 — Synthesize**: Feed real MCP data into LLM for expert analysis
   - **Phase 3 — Fallback**: If MCP tools fail, produce LLM-only output gracefully

   All MCP tool calls flow through the **MCPOrchestrator** → **Context Forge Gateway** for governance.

4. **Download** — Generated reports can be downloaded as `.md` files with descriptive filenames (e.g., `CI_Report_Pembrolizumab_2026-04-07.md`).

**Report format reference:** The EMD report structure covers 18 sections including Executive Summary & 6R Framework, Target/Biomarker Information, Molecular Pathways, Competitive Landscape, Regulatory/Commercial Overview, Development Trends, Risks & Recommendations, and more. See [`streamlit-app/docs/EMD_report_format.md`](streamlit-app/docs/EMD_report_format.md) for the full template.

### Specialized Agents

All agents extend `BaseAgent` and call **real MCP tools** via the MCPOrchestrator:

| Agent | Domain | MCP Tools Used |
|-------|--------|----------------|
| **ChemicalAgent** | Compounds, molecular properties, drug safety | `search_compounds_by_name`, `drug_getter`, `openfda_label_searcher` |
| **ClinicalAgent** | Clinical trials, FDA data, regulatory | `trial_searcher`, `openfda_adverse_searcher`, `openfda_approval_searcher`, `openfda_label_searcher`, `nci_intervention_searcher`, `disease_getter` |
| **LiteratureAgent** | Publications, preprints, citations | `article_searcher`, `search_pubmed`, `search_medrxiv_preprints`, `search_biorxiv_preprints` |
| **GeneAgent** | Genes, variants, protein interactions, biomarkers | `gene_getter`, `search_opentargets`, `get_protein_interactions`, `nci_biomarker_searcher`, `variant_searcher` |
| **DataAgent** | Statistical analysis, data visualization | LLM-only (jupyter/duckdb MCPs not in main config) |
| **ReportAgent** | EMD-format report orchestration | Delegates to all agents above |

### MCP Servers

| Server | Data Source |
|--------|------------|
| `pubchem` | Chemical compound data (PubChem) |
| `biomcp` | Comprehensive biomedical research (PubMed, clinical trials, variants, genes) |
| `literature` | PubMed articles, abstracts, citations |
| `data_analysis` | Statistics, correlations, sequence analysis, molecular descriptors |
| `web_knowledge` | Wikipedia, clinical trials, gene info, drug information |
| `medrxiv` | Medical preprint search and metadata |
| `opentargets` | Target-disease associations and drug data |
| `stringdb` | Protein-protein interaction networks |
| `biorxiv` | Biology preprint search and metadata |

### Governance Layer (Context Forge Gateway)

All MCP tool calls are routed through the Context Forge Gateway which provides:
- **Rate limiting** — Per-user limits (configurable, default 100 calls/hour)
- **Compliance checks** — PII/PHI detection, prohibited term filtering
- **Audit logging** — Immutable request/response records (SQLite-backed)
- **Service health monitoring** — Heartbeat checks and failover
- **Source attribution** — Data lineage tracking

### LLM Configuration

The system supports multiple LLM providers, selectable at runtime:
- **Standard** — Anthropic Claude Sonnet (default)
- **Merck Enterprise** — Azure OpenAI / AWS Bedrock
- **Ollama** — Local LLM (qwen3, llama3, deepseek, etc.)

The report generation panel respects whichever provider the user has selected.

---

## Documentation
* **[Merck Startup Guide](MERCK_STARTUP_GUIDE.md)** – **Recommended for EMD Serono/Merck users.**
* **[Installation Guide](docs/INSTALLATION.md)** – General setup instructions.
* **[Fix Log](docs/claude_fix_log.md)** – Detailed history of recent system fixes.
* **[EMD Report Format](streamlit-app/docs/EMD_report_format.md)** – The 18-section report structure template.

---

## Contributors
* **Rohan Hegde**, **Akash Prabu**, **Moumit Bhattacharjee**, **Takumi Tomono** – Project Collaborators
* **Dr. Parantu Shah** – Mentor

