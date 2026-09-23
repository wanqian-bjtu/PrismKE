"""Confidence and conflict-based review routing."""

from src.core.ids import stable_id
from src.domain import Claim, ClaimStatus, ConflictSet, ReviewTask


def route_by_risk(
    run_id: str,
    claims: list[Claim],
    conflicts: list[ConflictSet],
) -> tuple[list[Claim], list[ReviewTask]]:
    conflict_claims = {claim_id for conflict in conflicts for claim_id in conflict.claim_ids}
    reviews: list[ReviewTask] = []
    for claim in claims:
        if claim.status in {ClaimStatus.APPROVED, ClaimStatus.REJECTED}:
            continue
        reasons: list[str] = []
        if claim.id in conflict_claims:
            reasons.append("conflicting_claim")
        if claim.coarse_visual_evidence and not claim.cross_modal_support:
            reasons.append("coarse_visual_evidence")
        if claim.context_only_visual_claim:
            reasons.append("context_only_visual_claim")
        if claim.uncalibrated_visual_confidence:
            reasons.append("uncalibrated_visual_confidence")
        if claim.confidence < 0.55:
            claim.status = ClaimStatus.REJECTED
        elif claim.confidence < 0.85:
            reasons.append("medium_confidence")
            claim.status = ClaimStatus.REVIEW_REQUIRED
        elif reasons:
            claim.status = ClaimStatus.REVIEW_REQUIRED
        else:
            claim.status = ClaimStatus.AUTO_APPROVED
        if claim.status == ClaimStatus.REVIEW_REQUIRED:
            reviews.append(
                ReviewTask(
                    id=stable_id("review", run_id, claim.id, *reasons),
                    run_id=run_id,
                    claim_id=claim.id,
                    reasons=reasons,
                )
            )
    return claims, reviews
