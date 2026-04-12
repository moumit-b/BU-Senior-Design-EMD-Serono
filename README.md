# Pharma Research Intelligence System
### MCP-Based Multi-Agent AI for Drug Development Competitive Intelligence

> **New to this repo? Start with [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md).**

---

## Overview

A **Model Context Protocol (MCP)**–powered multi-agent AI system that gathers, normalizes, and synthesizes drug development intelligence across biomedical data sources. Built for EMD Serono's Competitive Intelligence (CI) workflows to accelerate evidence-based decision-making across all clinical trial phases.

The system combines a real-time research chat interface with a structured 18-section report generator, backed by 9 specialized MCP data servers, persistent multi-session chat history (Supabase), and a governance/audit layer.

---

## Features

- **Conversational research chat** with full context history — follow-up questions understand prior turns
- **18-section CI report generation** via parallel multi-agent MCP orchestration
- **Persistent sessions** — chat history and generated reports saved per user in Supabase
- **Report downloads** — `.md` and `.pdf` formats
- **Tool call metrics** — visualize which MCP tools were used per session
- **Governance layer** — rate limiting, compliance checks, audit logging, PII detection
- **Multi-LLM support** — Claude (default), Azure OpenAI, local Ollama models

---

## System Architecture

### Chat Interface

User questions flow through `MCPAgent`, which runs an agentic tool-calling loop with conversation history:

```
User message + conversation history
    -> MCPAgent -> LLM selects MCP tool(s)
    -> Execute tool (PubChem, BioMCP, OpenFDA, etc.)
    -> Feed result back to LLM -> up to 10 iterations
    -> FINAL ANSWER synthesized from real data
```

All tool calls pass through the **Context Forge Gateway** for governance, audit logging, compliance checks, and rate limiting.

### Report Generation Panel

Automatically detects the drug/target being discussed, then generates a structured EMD-format CI report on demand:

```
ReportAgent (18 sections in parallel batches of 3)
    |
    For each section:
        _gather_agent_data() — 1-3 specialized agents in parallel
            ChemicalAgent  -> PubChem, OpenFDA label data
            ClinicalAgent  -> ClinicalTrials.gov, FDA adverse events
            LiteratureAgent-> PubMed, medRxiv, bioRxiv
            GeneAgent      -> Open Targets, STRING-db, NCI biomarkers
        _synthesize_section() — LLM writes section from real MCP data
    |
    _compile_report() -> 18-section markdown document
    -> Saved to Supabase reports table
    -> Available for .md or .pdf download
```

See [`streamlit-app/docs/EMD_report_format.md`](streamlit-app/docs/EMD_report_format.md) for the full 18-section template.

### Specialized Agents

| Agent | Domain | Key MCP Tools |
|-------|--------|---------------|
| **ChemicalAgent** | Compounds, ADMET, drug safety | `search_compounds_by_name`, `drug_getter`, `openfda_label_searcher` |
| **ClinicalAgent** | Trials, FDA data, regulatory | `trial_searcher`, `openfda_adverse_searcher`, `nci_intervention_searcher` |
| **LiteratureAgent** | Publications, preprints | `article_searcher`, `search_pubmed`, `search_medrxiv_preprints` |
| **GeneAgent** | Genes, targets, pathways | `gene_getter`, `search_opentargets`, `get_protein_interactions` |
| **ReportAgent** | CI report orchestration | Delegates to all agents above |

### MCP Servers (9 total)

| Server | Data Source |
|--------|------------|
| `pubchem-augmented` | PubChem — chemical structures and properties |
| `biomcp` | PubMed, ClinicalTrials.gov, OpenFDA, variants, genes |
| `literature` | PubMed articles and abstracts |
| `data_analysis` | Statistics, molecular descriptors |
| `web_knowledge` | Wikipedia, DrugBank, drug/gene info |
| `medrxiv` | Medical preprint search |
| `biorxiv` | Biology preprint search |
| `opentargets` | Target-disease associations |
| `stringdb` | Protein-protein interaction networks |

### Database (Supabase / SQLite fallback)

- `users` — account records
- `chat_sessions` — one row per conversation, scoped to user
- `messages` — full message history with tool call steps
- `reports` — generated CI reports, scoped to session + user

Local fallback uses `streamlit-app/data/sessions.db` (SQLite) when no `SUPABASE_DB_URL` is set.

---

## LLM Configuration

| Profile | Provider | Use case |
|---------|----------|----------|
| Standard | Anthropic Claude Sonnet | Default — get key at console.anthropic.com |
| Merck Enterprise | Azure OpenAI / AWS Bedrock | Corporate network |
| Local | Ollama (qwen3, llama3, etc.) | Offline / no API key |

---

## Documentation

| Document | Purpose |
|----------|---------|
| **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** | Full setup guide — start here |
| **[MERCK_STARTUP_GUIDE.md](MERCK_STARTUP_GUIDE.md)** | EMD Serono / Merck-specific setup (SSL, proxy) |
| **[docs/INSTALLATION.md](docs/INSTALLATION.md)** | Legacy dual-orchestration install reference |
| **[streamlit-app/docs/EMD_report_format.md](streamlit-app/docs/EMD_report_format.md)** | 18-section report template |

---

## Contributors

**Rohan Hegde**, **Akash Prabu**, **Moumit Bhattacharjee**, **Takumi Tomono** — Project Collaborators  
**Dr. Parantu Shah** — Mentor
