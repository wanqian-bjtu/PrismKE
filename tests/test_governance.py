from __future__ import annotations

from datetime import UTC, datetime

from prismke.domain import (
    CandidateClaim,
    Claim,
    ClaimStatus,
    EntityMention,
    EntityTypeDef,
    Modality,
    OutputSchema,
    RelationDef,
    SchemaIndex,
    load_schema,
)
from prismke.governance import (
    EntityResolver,
    MultimodalAlignmentService,
    collect_mentions,
    detect_conflicts,
    normalize_claims,
    route_by_risk,
)


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


def test_functional_relation_conflicting_objects_are_preserved(schema_path) -> None:  # type: ignore[no-untyped-def]
    output_schema = load_schema(schema_path)
    output_schema.relations[0].functional = True
    output_schema.relations[0].max_cardinality = 1
    schema = SchemaIndex(output_schema)
    first = Claim(
        id="claim:1",
        subject_id="entity:s",
        relation_id="developed_by",
        object_literal="active",
        confidence=0.9,
        evidence_ids=["ev:1"],
    )
    second = first.model_copy(
        update={"id": "claim:2", "object_literal": "inactive", "evidence_ids": ["ev:2"]}
    )
    conflicts = detect_conflicts([second], [first], schema)
    assert conflicts[0].claim_ids == ["claim:1", "claim:2"]


def test_non_functional_relation_allows_multiple_objects(schema_path) -> None:  # type: ignore[no-untyped-def]
    schema = SchemaIndex(load_schema(schema_path))
    first = Claim(
        id="claim:1",
        subject_id="entity:s",
        relation_id="developed_by",
        object_literal="A",
        confidence=0.9,
        evidence_ids=["ev:1"],
    )
    second = first.model_copy(update={"id": "claim:2", "object_literal": "B"})
    assert detect_conflicts([second], [first], schema) == []


def test_non_overlapping_functional_values_do_not_conflict(schema_path) -> None:  # type: ignore[no-untyped-def]
    output_schema = load_schema(schema_path)
    output_schema.relations[0].functional = True
    output_schema.relations[0].max_cardinality = 1
    schema = SchemaIndex(output_schema)
    first = Claim(
        id="claim:1",
        subject_id="entity:s",
        relation_id="developed_by",
        object_literal="A",
        confidence=0.9,
        evidence_ids=["ev:1"],
        valid_from=datetime(2020, 1, 1, tzinfo=UTC),
        valid_to=datetime(2021, 1, 1, tzinfo=UTC),
    )
    second = first.model_copy(
        update={
            "id": "claim:2",
            "object_literal": "B",
            "valid_from": datetime(2021, 1, 1, tzinfo=UTC),
            "valid_to": None,
        }
    )
    assert detect_conflicts([second], [first], schema) == []


def test_inverse_relations_share_claim_identity() -> None:
    schema = SchemaIndex(
        OutputSchema(
            schema_id="family",
            version="1",
            entity_types=[EntityTypeDef(id="Person")],
            relations=[
                RelationDef(
                    id="parent_of",
                    domain=["Person"],
                    range=["Person"],
                    inverse_relation="child_of",
                ),
                RelationDef(
                    id="child_of",
                    domain=["Person"],
                    range=["Person"],
                    inverse_relation="parent_of",
                ),
            ],
        )
    )
    parent = EntityMention(
        id="mention:parent",
        name="A",
        entity_type="Person",
        evidence_ids=["ev:1"],
    )
    child = EntityMention(
        id="mention:child",
        name="B",
        entity_type="Person",
        evidence_ids=["ev:1"],
    )
    candidates = [
        CandidateClaim(
            id="candidate:1",
            subject=parent,
            relation="parent_of",
            object=child,
            confidence=0.9,
            evidence_ids=["ev:1"],
        ),
        CandidateClaim(
            id="candidate:2",
            subject=child,
            relation="child_of",
            object=parent,
            confidence=0.8,
            evidence_ids=["ev:2"],
        ),
    ]
    entities = {
        "entity:a": EntityResolver(schema, []).resolve([parent]).entities[-1],
        "entity:b": EntityResolver(schema, []).resolve([child]).entities[-1],
    }
    entities = {entity.id: entity for entity in entities.values()}
    mapping = {parent.id: next(e.id for e in entities.values() if e.name == "A")}
    mapping[child.id] = next(e.id for e in entities.values() if e.name == "B")
    claims = normalize_claims(candidates, schema, entities, mapping)
    assert len(claims) == 1
    assert claims[0].evidence_ids == ["ev:1", "ev:2"]


def test_inverse_relation_repairs_provider_direction_from_entity_types() -> None:
    schema = SchemaIndex(
        OutputSchema(
            schema_id="software",
            version="1",
            entity_types=[EntityTypeDef(id="Software"), EntityTypeDef(id="Organization")],
            relations=[
                RelationDef(
                    id="developed_by",
                    domain=["Software"],
                    range=["Organization"],
                    inverse_relation="develops",
                ),
                RelationDef(
                    id="develops",
                    domain=["Organization"],
                    range=["Software"],
                    inverse_relation="developed_by",
                ),
            ],
        )
    )
    organization = EntityMention(
        id="mention:organization",
        name="Northstar Labs",
        entity_type="Organization",
        evidence_ids=["ev:1"],
    )
    software = EntityMention(
        id="mention:software",
        name="AuroraGraph",
        entity_type="Software",
        evidence_ids=["ev:1"],
    )
    candidate = CandidateClaim(
        id="candidate:inverse-direction",
        subject=organization,
        relation="developed_by",
        object=software,
        confidence=0.9,
        evidence_ids=["ev:1"],
    )
    bundle = EntityResolver(schema, []).resolve([organization, software])
    entities = {entity.id: entity for entity in bundle.entities}
    claims = normalize_claims([candidate], schema, entities, bundle.mention_to_entity)
    assert claims[0].relation_id == "develops"
    assert claims[0].subject_id == bundle.mention_to_entity[organization.id]
    assert claims[0].object_entity_id == bundle.mention_to_entity[software.id]


def test_symmetric_relation_shares_claim_identity() -> None:
    schema = SchemaIndex(
        OutputSchema(
            schema_id="social",
            version="1",
            entity_types=[EntityTypeDef(id="Person")],
            relations=[
                RelationDef(
                    id="knows",
                    domain=["Person"],
                    range=["Person"],
                    symmetric=True,
                )
            ],
        )
    )
    left = EntityMention(id="mention:left", name="A", entity_type="Person", evidence_ids=["ev:1"])
    right = EntityMention(id="mention:right", name="B", entity_type="Person", evidence_ids=["ev:1"])
    candidates = [
        CandidateClaim(
            id="candidate:1",
            subject=left,
            relation="knows",
            object=right,
            confidence=0.9,
            evidence_ids=["ev:1"],
        ),
        CandidateClaim(
            id="candidate:2",
            subject=right,
            relation="knows",
            object=left,
            confidence=0.8,
            evidence_ids=["ev:2"],
        ),
    ]
    resolver = EntityResolver(schema, [])
    bundle = resolver.resolve([left, right])
    entities = {entity.id: entity for entity in bundle.entities}
    claims = normalize_claims(candidates, schema, entities, bundle.mention_to_entity)
    assert len(claims) == 1


def test_finite_max_cardinality_detects_overflow() -> None:
    schema = SchemaIndex(
        OutputSchema(
            schema_id="limited",
            version="1",
            entity_types=[EntityTypeDef(id="Thing")],
            relations=[RelationDef(id="has_member", max_cardinality=2)],
        )
    )
    claims = [
        Claim(
            id=f"claim:{index}",
            subject_id="entity:s",
            relation_id="has_member",
            object_literal=str(index),
            confidence=0.9,
            evidence_ids=[f"ev:{index}"],
        )
        for index in range(3)
    ]
    conflicts = detect_conflicts(claims, [], schema)
    assert conflicts[0].reason == "relation_max_cardinality_exceeded"
    assert len(conflicts[0].claim_ids) == 3


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


def test_context_only_visual_claim_always_requires_review() -> None:
    claim = Claim(
        id="claim:context-only",
        subject_id="entity:s",
        relation_id="r",
        object_literal="v",
        confidence=0.99,
        evidence_ids=["ev:image"],
        cross_modal_support=True,
        context_only_visual_claim=True,
    )
    claims, reviews = route_by_risk("run:context-only", [claim], [])
    assert claims[0].status == ClaimStatus.REVIEW_REQUIRED
    assert reviews[0].reasons == ["context_only_visual_claim"]


def test_atlasflow_cross_modal_conflict_is_preserved_for_review() -> None:
    schema = SchemaIndex(
        OutputSchema(
            schema_id="software-conflict",
            version="1",
            entity_types=[
                EntityTypeDef(id="Software"),
                EntityTypeDef(id="Organization"),
            ],
            relations=[
                RelationDef(
                    id="developed_by",
                    domain=["Software"],
                    range=["Organization"],
                    functional=True,
                    max_cardinality=1,
                )
            ],
        )
    )

    def conflict_candidate(
        identifier: str,
        organization: str,
        modality: Modality,
    ) -> CandidateClaim:
        evidence_id = f"ev:{identifier}"
        return CandidateClaim(
            id=f"candidate:{identifier}",
            subject=EntityMention(
                id=f"mention:atlasflow:{identifier}",
                name="AtlasFlow",
                entity_type="Software",
                modality=modality,
                evidence_ids=[evidence_id],
            ),
            relation="developed_by",
            object=EntityMention(
                id=f"mention:{organization}:{identifier}",
                name=organization,
                entity_type="Organization",
                modality=modality,
                evidence_ids=[evidence_id],
            ),
            confidence=0.95,
            evidence_ids=[evidence_id],
            modalities=[modality],
        )

    text = conflict_candidate("text", "Harbor Research", Modality.TEXT)
    visual = conflict_candidate("visual", "Contoso AI", Modality.IMAGE)
    candidates, alignments = MultimodalAlignmentService().align([text], [visual], schema)
    assert any(item.decision == "conflict" for item in alignments)

    resolver = EntityResolver(schema, [])
    resolution = resolver.resolve(collect_mentions(candidates))
    entities = {entity.id: entity for entity in resolution.entities}
    claims = normalize_claims(
        candidates,
        schema,
        entities,
        resolution.mention_to_entity,
    )
    conflicts = detect_conflicts(claims, [], schema)
    routed_claims, reviews = route_by_risk("run:atlasflow", claims, conflicts)
    assert len(routed_claims) == 2
    assert len(conflicts) == 1
    assert all(claim.status == ClaimStatus.REVIEW_REQUIRED for claim in routed_claims)
    assert len(reviews) == 2
