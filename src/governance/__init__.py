"""Entity and claim governance services."""

from src.governance.alignment import MultimodalAlignmentService
from src.governance.claim_normalization import (
    collect_mentions,
    merge_supporting_claims,
    normalize_claims,
)
from src.governance.conflicts import detect_conflicts
from src.governance.entity_index import EntityIndexReport, rebuild_entity_index
from src.governance.entity_operations import EntityGovernanceService
from src.governance.entity_resolution import (
    EntityResolver,
    ResolutionBundle,
    SemanticEntityResolver,
    entity_embedding_text,
)
from src.governance.risk import route_by_risk

__all__ = [
    "EntityResolver",
    "EntityGovernanceService",
    "EntityIndexReport",
    "SemanticEntityResolver",
    "ResolutionBundle",
    "entity_embedding_text",
    "rebuild_entity_index",
    "collect_mentions",
    "detect_conflicts",
    "merge_supporting_claims",
    "normalize_claims",
    "route_by_risk",
    "MultimodalAlignmentService",
]
