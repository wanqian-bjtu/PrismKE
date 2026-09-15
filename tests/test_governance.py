from __future__ import annotations

from prismke.governance import (
    EntityResolver,
    collect_mentions,
    detect_conflicts,
    normalize_claims,
    route_by_risk,
)
from prismke.models import (
    CandidateClaim,
    Claim,
    ClaimStatus,
    EntityMention,
    Modality,
)
from prismke.schema import SchemaIndex, load_schema


def candidate(confidence: float = 0.9) -> CandidateClaim:
    subject = EntityMention(
        id="mention:s",
        name="Prism KE",
        entity_type="software",
        modality=Modality.TEXT,
        evidence_ids=["ev:1"],
    )
    obj = EntityMention(
        id="mention:o",
        name="OpenAI",
        entity_type="Organization",
        modality=Modality.TEXT,
        evidence_ids=["ev:1"],
    )
    return CandidateClaim(
        id="candidate:1",
        subject=subject,
        relation="created_by",
        object=obj,
        confidence=confidence,
        evidence_ids=["ev:1"],
    )


def test_alias_linking_and_relation_normalization(schema_path) -> None:  # type: ignore[no-untyped-def]
    schema = SchemaIndex(load_schema(schema_path))
    item = candidate()
    resolver = EntityResolver(schema, [])
    bundle = resolver.resolve(collect_mentions([item]))
    entities = {entity.id: entity for entity in bundle.entities}
    claims = normalize_claims([item], schema, entities, bundle.mention_to_entity)
    assert bundle.mention_to_entity["mention:s"] == "entity:prismke"
    assert claims[0].relation_id == "developed_by"


def test_conflicting_objects_are_preserved() -> None:
    first = Claim(
        id="claim:1",
        subject_id="entity:s",
        relation_id="status",
        object_literal="active",
        confidence=0.9,
        evidence_ids=["ev:1"],
    )
    second = first.model_copy(
        update={"id": "claim:2", "object_literal": "inactive", "evidence_ids": ["ev:2"]}
    )
    conflicts = detect_conflicts([second], [first])
    assert conflicts[0].claim_ids == ["claim:1", "claim:2"]


def test_risk_routing_has_three_bands() -> None:
    base = Claim(
        id="claim:high",
        subject_id="entity:s",
        relation_id="r",
        object_literal="v",
        confidence=0.9,
        evidence_ids=["ev:1"],
    )
    medium = base.model_copy(update={"id": "claim:medium", "confidence": 0.7})
    low = base.model_copy(update={"id": "claim:low", "confidence": 0.2})
    claims, reviews = route_by_risk("run:1", [base, medium, low], [])
    assert [claim.status for claim in claims] == [
        ClaimStatus.AUTO_APPROVED,
        ClaimStatus.REVIEW_REQUIRED,
        ClaimStatus.REJECTED,
    ]
    assert [task.claim_id for task in reviews] == ["claim:medium"]
