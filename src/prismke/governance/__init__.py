"""Entity and claim governance services."""

from prismke.governance.alignment import MultimodalAlignmentService
from prismke.governance.claim_normalization import (
    collect_mentions,
    merge_supporting_claims,
    normalize_claims,
)
from prismke.governance.conflicts import detect_conflicts
from prismke.governance.entity_index import EntityIndexReport, rebuild_entity_index
from prismke.governance.entity_operations import EntityGovernanceService
from prismke.governance.entity_resolution import (
    EntityResolver,
    ResolutionBundle,
    SemanticEntityResolver,
    entity_embedding_text,
)
from prismke.governance.risk import route_by_risk

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
