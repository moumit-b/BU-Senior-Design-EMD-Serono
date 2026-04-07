"""
Specialized Agents Package

Contains all specialized agents for the dual orchestration architecture:
- ChemicalAgent: Chemical compound queries
- ClinicalAgent: Clinical trials and regulatory data
- LiteratureAgent: Scientific literature search
- GeneAgent: Gene and target biology
- DataAgent: Data analysis and statistics
- ReportAgent: Structured report generation (EMD format)

All agents inherit from BaseAgent and follow the same interface.
"""

from .base_agent import BaseAgent, AgentTask, AgentResult, AgentContext
from .chemical_agent import ChemicalAgent
from .clinical_agent import ClinicalAgent
from .literature_agent import LiteratureAgent
from .gene_agent import GeneAgent
from .data_agent import DataAgent
from .report_agent import ReportAgent

__all__ = [
    "BaseAgent",
    "AgentTask",
    "AgentResult",
    "AgentContext",
    "ChemicalAgent",
    "ClinicalAgent",
    "LiteratureAgent",
    "GeneAgent",
    "DataAgent",
    "ReportAgent",
]
