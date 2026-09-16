"""Idempotent JSON graph migration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson
from pydantic import BaseModel, Field

from prismke.core.errors import EvidenceIntegrityError, GraphIntegrityError
from prismke.domain import (
    CanonicalEntity,
    Claim,
    ConflictSet,
    EntityOperation,
    EvidenceRef,
    GraphCommit,
    GraphDocument,
    GraphRevision,
)
from prismke.persistence.base import EvidenceStore, GraphStore


class MigrationReport(BaseModel):
    source: str
    dry_run: bool
    documents: int
    evidence: int
    entities: int
    claims: int
    conflicts: int
    revisions: int
    committed_revisions: int = 0
    warnings: list[str] = Field(default_factory=list)
    blocked_claim_ids: list[str] = Field(default_factory=list)


async def migrate_json_graph(
    source: Path,
    target: GraphStore | None,
    *,
    evidence_store: EvidenceStore | None = None,
    dry_run: bool = False,
) -> MigrationReport:
    payload: dict[str, Any] = orjson.loads(source.read_bytes())
    documents = {
        item_id: GraphDocument.model_validate(item)
        for item_id, item in payload.get("documents", {}).items()
    }
    evidence = {
        item_id: EvidenceRef.model_validate(item)
        for item_id, item in payload.get("evidence", {}).items()
    }
    entities = {
        item_id: CanonicalEntity.model_validate(item)
        for item_id, item in payload.get("entities", {}).items()
    }
    claims = {
        item_id: Claim.model_validate(item) for item_id, item in payload.get("claims", {}).items()
    }
    conflicts = {
        item_id: ConflictSet.model_validate(item)
        for item_id, item in payload.get("conflicts", {}).items()
    }
    revisions = [GraphRevision.model_validate(item) for item in payload.get("revisions", [])]
    warnings: list[str] = []

    if evidence_store is not None:
        for claim in claims.values():
            for evidence_id in claim.evidence_ids:
                if evidence_id in evidence:
                    continue
                try:
                    item = await evidence_store.get(evidence_id)
                except EvidenceIntegrityError:
                    warnings.append(f"missing_evidence:{evidence_id}")
                    continue
                evidence[item.id] = item
                documents.setdefault(
                    item.document_id,
                    GraphDocument(
                        id=item.document_id,
                        filename="legacy-document",
                        content_hash=item.source_hash,
                        media_type="application/octet-stream",
                    ),
                )

    historical_claims = {
        (revision.id, change.resource_id): Claim.model_validate(change.after)
        for revision in revisions
        for change in revision.changes
        if change.resource_type == "claim" and change.after is not None
    }
    blocked = {
        cid
        for revision in revisions
        for cid in revision.claim_ids
        if cid in claims
        and historical_claims.get((revision.id, cid), claims[cid]).tx_to is None
        and (
            revision.validation_context is None
            or revision.validation_context.policy_version != "validation-v1"
            or cid not in revision.validation_context.claim_schema_ids
        )
    }
    warnings.extend(f"missing_schema_context:{cid}" for cid in sorted(blocked))
    report = MigrationReport(
        source=str(source.resolve()),
        dry_run=dry_run,
        documents=len(documents),
        evidence=len(evidence),
        entities=len(entities),
        claims=len(claims),
        conflicts=len(conflicts),
        revisions=len(revisions),
        warnings=sorted(set(warnings)),
        blocked_claim_ids=sorted(blocked),
    )
    if dry_run:
        return report
    if target is None:
        raise ValueError("target graph store is required unless dry_run is enabled")
    if blocked:
        raise GraphIntegrityError(f"MISSING_SCHEMA_CONTEXT: {len(blocked)} 个活动事实不能迁移")

    for index, revision in enumerate(revisions):
        revision_entities = [entities[item] for item in revision.entity_ids if item in entities]
        revision_claims = [claims[item] for item in revision.claim_ids if item in claims]
        revision_conflicts = [
            conflicts[item] for item in revision.conflict_ids if item in conflicts
        ]
        revision_operations = []
        # Replay recorded post-change snapshots rather than copying the final state
        # into every historical revision.
        for change in revision.changes:
            if change.after is None:
                continue
            if change.resource_type == "claim":
                revision_claims = [c for c in revision_claims if c.id != change.resource_id]
                revision_claims.append(Claim.model_validate(change.after))
            elif change.resource_type == "entity":
                revision_entities = [e for e in revision_entities if e.id != change.resource_id]
                revision_entities.append(CanonicalEntity.model_validate(change.after))
            elif change.resource_type == "conflict":
                revision_conflicts = [c for c in revision_conflicts if c.id != change.resource_id]
                revision_conflicts.append(ConflictSet.model_validate(change.after))
            elif change.resource_type == "entity_operation":
                revision_operations.append(EntityOperation.model_validate(change.after))
        evidence_ids = {
            evidence_id for claim in revision_claims for evidence_id in claim.evidence_ids
        }
        revision_evidence = [evidence[item] for item in evidence_ids if item in evidence]
        document_ids = {item.document_id for item in revision_evidence}
        await target.commit(
            GraphCommit(
                documents=[documents[item] for item in document_ids if item in documents],
                evidence=revision_evidence,
                entities=revision_entities,
                claims=revision_claims,
                conflicts=revision_conflicts,
                entity_operations=revision_operations,
                revision=revision,
                validation_context=revision.validation_context,
            )
        )
        report.committed_revisions = index + 1
    return report
