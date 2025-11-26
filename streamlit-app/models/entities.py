"""Entity models for research session tracking."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EntityType(Enum):
    """Types of entities tracked in research sessions."""
    DRUG = "drug"
    GENE = "gene"
    PROTEIN = "protein"
    CLINICAL_TRIAL = "clinical_trial"
    DISEASE = "disease"
    PATHWAY = "pathway"
    PUBLICATION = "publication"


@dataclass
class Entity:
    """Base class for all research entities."""
    entity_id: str
    entity_type: EntityType
    name: str
    discovered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_mcp: Optional[str] = None


@dataclass
class Drug(Entity):
    """Drug/compound entity."""
    # Chemical properties
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    pubchem_cid: Optional[int] = None

    # Drug information
    brand_names: List[str] = field(default_factory=list)
    indication: Optional[str] = None
    mechanism_of_action: Optional[str] = None
    development_stage: Optional[str] = None  # e.g., "Phase 3", "Approved"

    def __post_init__(self):
        """Set entity type after initialization."""
        if self.entity_type != EntityType.DRUG:
            object.__setattr__(self, 'entity_type', EntityType.DRUG)


@dataclass
class Gene(Entity):
    """Gene entity."""
    gene_symbol: Optional[str] = None
    gene_id: Optional[str] = None  # e.g., NCBI Gene ID
    chromosome: Optional[str] = None
    function: Optional[str] = None
    associated_diseases: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Set entity type after initialization."""
        if self.entity_type != EntityType.GENE:
            object.__setattr__(self, 'entity_type', EntityType.GENE)


@dataclass
class Protein(Entity):
    """Protein entity."""
    uniprot_id: Optional[str] = None
    sequence: Optional[str] = None
    molecular_weight: Optional[float] = None
    function: Optional[str] = None
    druggability_score: Optional[float] = None

    def __post_init__(self):
        """Set entity type after initialization."""
        if self.entity_type != EntityType.PROTEIN:
            object.__setattr__(self, 'entity_type', EntityType.PROTEIN)


@dataclass
class ClinicalTrial(Entity):
    """Clinical trial entity."""
    nct_id: Optional[str] = None  # ClinicalTrials.gov ID
    title: Optional[str] = None
    phase: Optional[str] = None  # e.g., "Phase 1", "Phase 2"
    status: Optional[str] = None  # e.g., "Recruiting", "Completed"
    condition: Optional[str] = None
    intervention: Optional[str] = None
    sponsor: Optional[str] = None
    enrollment: Optional[int] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None

    def __post_init__(self):
        """Set entity type after initialization."""
        if self.entity_type != EntityType.CLINICAL_TRIAL:
            object.__setattr__(self, 'entity_type', EntityType.CLINICAL_TRIAL)
