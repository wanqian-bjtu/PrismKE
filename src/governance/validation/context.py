"""Reuse recorded schema provenance; never infer a schema from graph data."""

from collections.abc import Iterable

from src.core.ids import canonical_hash
from src.domain import (
    CanonicalEntity,
    Claim,
    CommitValidationContext,
    GraphCommit,
    GraphRevision,
)


def bind_commit_provenance(transaction: GraphCommit) -> None:
    transaction.revision.validation_context = transaction.validation_context
    payload = transaction.model_dump(mode="json", exclude={"revision": {"commit_fingerprint"}})
    for field in (
        "documents",
        "evidence",
        "entities",
        "claims",
        "conflicts",
        "entity_operations",
        "entity_embeddings",
    ):
        payload[field] = sorted(
            payload[field], key=lambda item: item.get("id", item.get("entity_id", ""))
        )
    transaction.revision.commit_fingerprint = canonical_hash(payload)


def final_state_commit(
    transaction: GraphCommit,
    claims: dict[str, Claim],
    previous_entities: dict[str, CanonicalEntity],
    revisions: Iterable[GraphRevision],
) -> GraphCommit:
    changed = {
        e.id
        for e in transaction.entities
        if e.id in previous_entities
        and (
            e.entity_type != previous_entities[e.id].entity_type
            or e.active != previous_entities[e.id].active
        )
    }
    submitted_ids = {c.id for c in transaction.claims}
    additional = {
        c.id
        for c in claims.values()
        if c.tx_to is None
        and c.id not in submitted_ids
        and changed.intersection({c.subject_id, c.object_entity_id})
    }
    context = context_for_claims(revisions, additional)
    if transaction.validation_context is not None:
        context.policy_version = transaction.validation_context.policy_version
        context.schemas.update(transaction.validation_context.schemas)
        context.claim_schema_ids.update(transaction.validation_context.claim_schema_ids)
        context.document_asset_ids.update(transaction.validation_context.document_asset_ids)
    return transaction.model_copy(
        update={
            "validation_context": context,
            "claims": [claims[cid] for cid in sorted(submitted_ids | additional)],
        }
    )


def context_for_claims(
    revisions: Iterable[GraphRevision], claim_ids: set[str]
) -> CommitValidationContext:
    result = CommitValidationContext()
    for revision in revisions:
        context = revision.validation_context
        if context is None or context.policy_version != "validation-v1":
            continue
        result.document_asset_ids.update(context.document_asset_ids)
        for claim_id in claim_ids:
            sid = context.claim_schema_ids.get(claim_id)
            if sid and sid in context.schemas and claim_id not in result.claim_schema_ids:
                result.claim_schema_ids[claim_id] = sid
                result.schemas[sid] = context.schemas[sid]
    return result
