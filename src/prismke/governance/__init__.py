"""Entity and claim governance services."""

from prismke.governance.alignment import MultimodalAlignmentService
from prismke.governance.claim_normalization import (
    collect_mentions,
    merge_supporting_claims,
    normalize_claims,
)
from prismke.governance.conflicts import detect_conflicts
from prismke.governance.entity_resolution import EntityResolver, ResolutionBundle
from prismke.governance.risk import route_by_risk

__all__ = [
    "EntityResolver",
    "ResolutionBundle",
    "collect_mentions",
    "detect_conflicts",
    "merge_supporting_claims",
    "normalize_claims",
    "route_by_risk",
    "MultimodalAlignmentService",
]
