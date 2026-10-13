"""Atomic local graph persistence with revisions and compensating rollback."""

from __future__ import annotations

import math
import os
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import orjson
from filelock import FileLock

from src.core.errors import EvidenceRequiredError, GraphIntegrityError
from src.core.ids import stable_id
from src.domain import (
    CanonicalEntity,
    Claim,
    EntityEmbedding,
    EvidenceRef,
    GraphChange,
    GraphCommit,
    GraphHealth,
    GraphMediaContent,
    GraphMediaOccurrence,
    GraphMediaRelation,
    GraphNeighborhood,
    GraphRevision,
    RevisionDiff,
    VisualAssertion,
    VisualReviewEvent,
    visual_value_matches,
)
from src.governance.review_guards import verify_correction
from src.governance.validation import ValidationService
from src.governance.validation.context import (
    bind_commit_provenance,
    context_for_claims,
    final_state_commit,
)
from src.persistence.base import EvidenceStore


class JSONGraphStore:
    def __init__(self, directory: Path, *, evidence_store: EvidenceStore | None = None) -> None:
        self.evidence_store = evidence_store
        self.directory = directory
        self.path = directory / "graph.json"
        self.lock = FileLock(str(directory / "graph.lock"))
        self.directory.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_atomic(self._empty_graph())

    @staticmethod
    def _empty_graph() -> dict[str, Any]:
        return {
            "documents": {},
            "evidence": {},
            "entities": {},
            "entity_embeddings": {},
            "entity_operations": {},
            "claims": {},
            "conflicts": {},
            "media_contents": {},
            "media_occurrences": {},
            "media_relations": {},
            "visual_assertions": {},
            "visual_review_events": {},
            "revisions": [],
        }

    @staticmethod
    def _upgrade(data: dict[str, Any]) -> dict[str, Any]:
        for key, default in JSONGraphStore._empty_graph().items():
            data.setdefault(key, deepcopy(default))
        return data

    def _read(self) -> dict[str, Any]:
        return self._upgrade(cast(dict[str, Any], orjson.loads(self.path.read_bytes())))

    def snapshot(self) -> dict[str, Any]:
        """Return a detached snapshot for migration and diagnostics."""
        with self.lock:
            return deepcopy(self._read())

    def _write_atomic(self, payload: dict[str, Any]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("wb") as stream:
                stream.write(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    async def healthcheck(self) -> GraphHealth:
        try:
            with self.lock:
                self._read()
        except (OSError, orjson.JSONDecodeError, TypeError, ValueError) as exc:
            return GraphHealth(backend="json", healthy=False, message=str(exc))
        return GraphHealth(backend="json", healthy=True)

    async def list_entities(self) -> list[CanonicalEntity]:
        with self.lock:
            data = self._read()
        return [CanonicalEntity.model_validate(item) for item in data["entities"].values()]

    async def get_entity(self, entity_id: str) -> CanonicalEntity | None:
        with self.lock:
            payload = self._read()["entities"].get(entity_id)
        return CanonicalEntity.model_validate(payload) if payload is not None else None

    async def search_entities(
        self,
        vector: list[float],
        entity_type: str,
        top_k: int,
        model_fingerprint: str | None = None,
    ) -> list[tuple[CanonicalEntity, float]]:
        if not vector or top_k < 1:
            return []
        with self.lock:
            data = self._read()
        query_norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        matches: list[tuple[CanonicalEntity, float]] = []
        for entity_id, payload in data["entities"].items():
            entity = CanonicalEntity.model_validate(payload)
            embedding_payload = data["entity_embeddings"].get(entity_id)
            if not entity.active or entity.entity_type != entity_type or embedding_payload is None:
                continue
            embedding = EntityEmbedding.model_validate(embedding_payload)
            if (
                len(embedding.vector) != len(vector)
                or model_fingerprint is not None
                and embedding.model_fingerprint != model_fingerprint
            ):
                continue
            candidate_norm = math.sqrt(sum(value * value for value in embedding.vector)) or 1.0
            score = sum(
                left * right for left, right in zip(vector, embedding.vector, strict=True)
            ) / (query_norm * candidate_norm)
            matches.append((entity, max(-1.0, min(1.0, score))))
        return sorted(matches, key=lambda item: (-round(item[1], 12), item[0].id))[:top_k]

    async def list_entity_embeddings(self) -> list[EntityEmbedding]:
        with self.lock:
            payloads = self._read()["entity_embeddings"].values()
            return [EntityEmbedding.model_validate(item) for item in payloads]

    async def upsert_entity_embeddings(self, embeddings: list[EntityEmbedding]) -> None:
        with self.lock:
            data = self._read()
            unknown = {item.entity_id for item in embeddings} - set(data["entities"])
            if unknown:
                raise GraphIntegrityError(f"embeddings reference missing entities: {unknown}")
            for embedding in embeddings:
                data["entity_embeddings"][embedding.entity_id] = embedding.model_dump(mode="json")
            self._write_atomic(data)

    async def list_claims(self) -> list[Claim]:
        with self.lock:
            data = self._read()
        return [Claim.model_validate(item) for item in data["claims"].values()]

    async def list_media_occurrences(self) -> list[GraphMediaOccurrence]:
        with self.lock:
            payloads = self._read()["media_occurrences"].values()
            return [GraphMediaOccurrence.model_validate(item) for item in payloads]

    async def list_media_contents(self) -> list[GraphMediaContent]:
        with self.lock:
            payloads = self._read()["media_contents"].values()
            return [GraphMediaContent.model_validate(item) for item in payloads]

    async def get_media_occurrence(self, occurrence_id: str) -> GraphMediaOccurrence | None:
        with self.lock:
            payload = self._read()["media_occurrences"].get(occurrence_id)
        return GraphMediaOccurrence.model_validate(payload) if payload is not None else None

    async def list_media_relations(self) -> list[GraphMediaRelation]:
        with self.lock:
            payloads = self._read()["media_relations"].values()
            return [GraphMediaRelation.model_validate(item) for item in payloads]

    async def list_visual_assertions(self) -> list[VisualAssertion]:
        with self.lock:
            payloads = self._read()["visual_assertions"].values()
            return [VisualAssertion.model_validate(item) for item in payloads]

    async def latest_revision(self) -> GraphRevision | None:
        with self.lock:
            revisions = self._read()["revisions"]
        return GraphRevision.model_validate(revisions[-1]) if revisions else None

    async def list_revisions(self, limit: int = 50) -> list[GraphRevision]:
        if limit < 1:
            return []
        with self.lock:
            revisions = self._read()["revisions"][-limit:]
        return [GraphRevision.model_validate(item) for item in reversed(revisions)]

    async def get_claim(self, claim_id: str) -> Claim | None:
        with self.lock:
            payload = self._read()["claims"].get(claim_id)
        return Claim.model_validate(payload) if payload is not None else None

    async def get_evidence(self, evidence_id: str) -> EvidenceRef | None:
        with self.lock:
            payload = self._read()["evidence"].get(evidence_id)
        return EvidenceRef.model_validate(payload) if payload is not None else None

    async def get_neighborhood(self, entity_id: str, depth: int = 1) -> GraphNeighborhood:
        if depth < 1 or depth > 3:
            raise ValueError("depth must be between 1 and 3")
        with self.lock:
            data = self._read()
        if entity_id not in data["entities"]:
            raise KeyError(f"entity not found: {entity_id}")
        seen = {entity_id}
        frontier = {entity_id}
        selected_claims: dict[str, Claim] = {}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for payload in data["claims"].values():
                claim = Claim.model_validate(payload)
                if claim.tx_to is not None:
                    continue
                endpoints = {claim.subject_id}
                if claim.object_entity_id:
                    endpoints.add(claim.object_entity_id)
                if endpoints & frontier:
                    selected_claims[claim.id] = claim
                    next_frontier.update(endpoints - seen)
            seen.update(next_frontier)
            frontier = next_frontier
            if not frontier:
                break
        entities = [CanonicalEntity.model_validate(data["entities"][item]) for item in sorted(seen)]
        return GraphNeighborhood(
            center_entity_id=entity_id,
            depth=depth,
            entities=entities,
            claims=list(selected_claims.values()),
        )

    @staticmethod
    def _merge_claim(current: dict[str, Any], incoming: Claim) -> Claim:
        previous = Claim.model_validate(current)
        merged = incoming.model_copy(deep=True)
        merged.evidence_ids = sorted(set(previous.evidence_ids + incoming.evidence_ids))
        merged.source_candidate_ids = sorted(
            set(previous.source_candidate_ids + incoming.source_candidate_ids)
        )
        merged.confidence = max(previous.confidence, incoming.confidence)
        merged.source_run_ids = sorted(set(previous.source_run_ids + incoming.source_run_ids))
        return merged

    def _apply(self, data: dict[str, Any], transaction: GraphCommit) -> tuple[dict[str, Any], bool]:
        revisions = data["revisions"]
        existing_revision = next(
            (item for item in revisions if item["id"] == transaction.revision.id), None
        )
        revision_payload = transaction.revision.model_dump(mode="json")
        if existing_revision is not None:
            if GraphRevision.model_validate(existing_revision) != transaction.revision:
                raise GraphIntegrityError(
                    f"revision id already exists with different content: {transaction.revision.id}"
                )
            return data, True

        latest_id = revisions[-1]["id"] if revisions else None
        if transaction.revision.parent_id != latest_id:
            raise GraphIntegrityError(
                f"revision parent mismatch: expected {latest_id}, "
                f"got {transaction.revision.parent_id}"
            )

        for document in transaction.documents:
            data["documents"][document.id] = document.model_dump(mode="json")
        for evidence in transaction.evidence:
            if evidence.document_id not in data["documents"]:
                raise GraphIntegrityError(
                    f"evidence {evidence.id} references missing document {evidence.document_id}"
                )
            data["evidence"][evidence.id] = evidence.model_dump(mode="json")
        for entity in transaction.entities:
            previous = data["entities"].get(entity.id)
            if previous is not None and (
                CanonicalEntity.model_validate(previous).embedding_source()
                != entity.embedding_source()
            ):
                data["entity_embeddings"].pop(entity.id, None)
            data["entities"][entity.id] = entity.model_dump(mode="json")
        for operation in transaction.entity_operations:
            data["entity_operations"][operation.id] = operation.model_dump(mode="json")
        for embedding in transaction.entity_embeddings:
            data["entity_embeddings"][embedding.entity_id] = embedding.model_dump(mode="json")
        for claim in transaction.claims:
            if not claim.evidence_ids:
                raise EvidenceRequiredError(f"claim {claim.id} has no evidence")
            current = data["claims"].get(claim.id)
            if current and transaction.correction_guard is None:
                claim = self._merge_claim(current, claim)
            data["claims"][claim.id] = claim.model_dump(mode="json")
        for conflict in transaction.conflicts:
            data["conflicts"][conflict.id] = conflict.model_dump(mode="json")
        for event in transaction.visual_review_events:
            previous = data["visual_review_events"].get(event.id)
            payload = event.model_dump(mode="json")
            if previous is not None and previous != payload:
                raise GraphIntegrityError(
                    f"visual review event already exists with different content: {event.id}"
                )
            data["visual_review_events"][event.id] = payload
        for content in transaction.media_contents:
            previous = data["media_contents"].get(content.id)
            payload = content.model_dump(mode="json")
            if previous is not None and previous != payload:
                raise GraphIntegrityError(
                    f"immutable media content changed: {content.id}"
                )
            duplicate = next(
                (
                    item_id
                    for item_id, item in data["media_contents"].items()
                    if item["content_hash"] == content.content_hash and item_id != content.id
                ),
                None,
            )
            if duplicate:
                raise GraphIntegrityError(
                    f"duplicate media content hash: {content.content_hash}"
                )
            data["media_contents"][content.id] = payload
        for occurrence in transaction.media_occurrences:
            data["media_occurrences"][occurrence.id] = occurrence.model_dump(mode="json")
        for relation in transaction.media_relations:
            data["media_relations"][relation.id] = relation.model_dump(mode="json")
        for assertion in transaction.visual_assertions:
            data["visual_assertions"][assertion.id] = assertion.model_dump(mode="json")

        known_entities = set(data["entities"])
        known_claims = set(data["claims"])
        known_conflicts = set(data["conflicts"])
        known_evidence = set(data["evidence"])
        known_contents = set(data["media_contents"])
        known_occurrences = set(data["media_occurrences"])
        known_review_events = set(data["visual_review_events"])
        review_events = data["visual_review_events"]
        if not {item.entity_id for item in transaction.entity_embeddings} <= known_entities:
            raise GraphIntegrityError("embedding references missing entity")
        for operation in transaction.entity_operations:
            if not set(operation.source_entity_ids + operation.target_entity_ids) <= known_entities:
                raise GraphIntegrityError(
                    f"entity operation {operation.id} references missing entities"
                )
        for claim in transaction.claims:
            entity_refs = {claim.subject_id}
            if claim.object_entity_id:
                entity_refs.add(claim.object_entity_id)
            if not entity_refs <= known_entities:
                raise GraphIntegrityError(f"claim {claim.id} references missing entities")
            if transaction.evidence and not set(claim.evidence_ids) <= known_evidence:
                raise GraphIntegrityError(
                    f"UNKNOWN_EVIDENCE: claim {claim.id} references missing evidence"
                )
        if not set(transaction.revision.entity_ids) <= known_entities:
            raise GraphIntegrityError("revision references missing entities")
        if not set(transaction.revision.claim_ids) <= known_claims:
            raise GraphIntegrityError("revision references missing claims")
        if not set(transaction.revision.conflict_ids) <= known_conflicts:
            raise GraphIntegrityError("revision references missing conflicts")
        for conflict in transaction.conflicts:
            if not set(conflict.claim_ids) <= known_claims:
                raise GraphIntegrityError(f"conflict {conflict.id} references missing claims")
        for occurrence in transaction.media_occurrences:
            if occurrence.document_id not in data["documents"]:
                raise GraphIntegrityError(
                    f"media occurrence {occurrence.id} references missing document"
                )
            if occurrence.media_content_id not in known_contents:
                raise GraphIntegrityError(
                    f"media occurrence {occurrence.id} references missing content"
                )
            if occurrence.evidence_id not in known_evidence:
                raise GraphIntegrityError(
                    f"media occurrence {occurrence.id} references missing evidence"
                )
        for relation in transaction.media_relations:
            if relation.occurrence_id not in known_occurrences:
                raise GraphIntegrityError(
                    f"media relation {relation.id} references missing occurrence"
                )
            if not set(relation.evidence_ids) <= known_evidence:
                raise GraphIntegrityError(
                    f"media relation {relation.id} references missing evidence"
                )
            if relation.target_entity_id and relation.target_entity_id not in known_entities:
                raise GraphIntegrityError(
                    f"media relation {relation.id} references missing entity"
                )
            if relation.target_claim_id:
                claim_payload = data["claims"].get(relation.target_claim_id)
                if claim_payload is None:
                    raise GraphIntegrityError(
                        f"media relation {relation.id} references missing claim"
                    )
                claim = Claim.model_validate(claim_payload)
                occurrence = GraphMediaOccurrence.model_validate(
                    data["media_occurrences"][relation.occurrence_id]
                )
                if claim.status not in {"approved", "auto_approved"}:
                    raise GraphIntegrityError("SUPPORTS requires an approved claim")
                if occurrence.evidence_id not in claim.evidence_ids:
                    raise GraphIntegrityError("SUPPORTS evidence does not support target claim")
            if relation.relation_type == "DEPICTS":
                event_payload = review_events.get(relation.approved_review_event_id or "")
                if event_payload is None:
                    raise GraphIntegrityError("DEPICTS requires an approved visual review")
                event = VisualReviewEvent.model_validate(event_payload)
                if (
                    event.decision != "approve"
                    or event.target_type != "media_relation"
                    or event.target_id != relation.source_candidate_id
                ):
                    raise GraphIntegrityError("DEPICTS review event does not approve relation")
        for assertion in transaction.visual_assertions:
            if assertion.occurrence_id not in known_occurrences:
                raise GraphIntegrityError(
                    f"visual assertion {assertion.id} references missing occurrence"
                )
            if assertion.subject_entity_id not in known_entities:
                raise GraphIntegrityError(
                    f"visual assertion {assertion.id} references missing entity"
                )
            if not set(assertion.evidence_ids) <= known_evidence:
                raise GraphIntegrityError(
                    f"visual assertion {assertion.id} references missing evidence"
                )
            if assertion.approved_review_event_id not in known_review_events:
                raise GraphIntegrityError("visual assertion requires an approved visual review")
            assertion_event = VisualReviewEvent.model_validate(
                review_events[assertion.approved_review_event_id]
            )
            if (
                assertion_event.decision != "approve"
                or assertion_event.target_type != "visual_assertion"
                or assertion_event.target_id != assertion.source_candidate_id
            ):
                raise GraphIntegrityError(
                    "visual assertion review event does not approve assertion"
                )
            definitions = {
                item.id: item
                for schema in (
                    transaction.validation_context.schemas.values()
                    if transaction.validation_context
                    else []
                )
                for item in schema.attributes
            }
            definition = definitions.get(assertion.predicate)
            if definition is None:
                raise GraphIntegrityError(
                    f"visual assertion predicate is not in schema: {assertion.predicate}"
                )
            if not visual_value_matches(assertion.normalized_value, definition.value_type):
                raise GraphIntegrityError(
                    f"visual assertion value type is invalid: {assertion.id}"
                )
        if not set(transaction.revision.media_content_ids) <= known_contents:
            raise GraphIntegrityError("revision references missing media content")
        if not set(transaction.revision.media_occurrence_ids) <= known_occurrences:
            raise GraphIntegrityError("revision references missing media occurrence")
        if not set(transaction.revision.media_relation_ids) <= set(data["media_relations"]):
            raise GraphIntegrityError("revision references missing media relation")
        if not set(transaction.revision.visual_assertion_ids) <= set(data["visual_assertions"]):
            raise GraphIntegrityError("revision references missing visual assertion")

        revisions.append(revision_payload)
        return data, False

    async def commit(self, transaction: GraphCommit) -> None:
        bind_commit_provenance(transaction)
        transaction = transaction.model_copy(deep=True)
        if self.evidence_store is None and transaction.media_contents:
            raise GraphIntegrityError("media commit requires an evidence store")
        if self.evidence_store is not None:
            from hashlib import sha256

            for content in transaction.media_contents:
                payload = await self.evidence_store.get_blob(content.blob_hash)
                if sha256(payload).hexdigest() != content.content_hash:
                    raise GraphIntegrityError(
                        f"media content hash verification failed: {content.id}"
                    )
            for occurrence in transaction.media_occurrences:
                if not await self.evidence_store.verify(occurrence.evidence_id):
                    raise GraphIntegrityError(
                        f"media occurrence evidence is invalid: {occurrence.id}"
                    )
        with self.lock:
            data = self._read()
            if transaction.revision.id not in {r["id"] for r in data["revisions"]}:
                verify_correction(
                    transaction,
                    {
                        **{f"entity:{k}": v for k, v in data["entities"].items()},
                        **{f"claim:{k}": v for k, v in data["claims"].items()},
                    },
                )
            updated, is_noop = self._apply(deepcopy(data), transaction)
            if is_noop:
                return
            final_transaction = final_state_commit(
                transaction,
                {k: Claim.model_validate(v) for k, v in updated["claims"].items()},
                {k: CanonicalEntity.model_validate(v) for k, v in data["entities"].items()},
                [GraphRevision.model_validate(r) for r in reversed(data["revisions"])],
            )
            await ValidationService().commit(
                final_transaction,
                {k: CanonicalEntity.model_validate(v) for k, v in updated["entities"].items()},
                {k: EvidenceRef.model_validate(v) for k, v in updated["evidence"].items()},
                set(updated["documents"]),
                self.evidence_store,
            )
            self._write_atomic(updated)

    async def diff_revisions(self, from_id: str, to_id: str) -> RevisionDiff:
        with self.lock:
            revisions = [GraphRevision.model_validate(item) for item in self._read()["revisions"]]
        positions = {revision.id: index for index, revision in enumerate(revisions)}
        if from_id not in positions or to_id not in positions:
            raise KeyError("revision not found")
        if positions[from_id] > positions[to_id]:
            raise ValueError("from revision must not be newer than to revision")
        selected = revisions[positions[from_id] + 1 : positions[to_id] + 1]
        return RevisionDiff(
            from_revision_id=from_id,
            to_revision_id=to_id,
            changes=[change for revision in selected for change in revision.changes],
            legacy_id_only=any(not revision.changes for revision in selected),
            entity_ids=sorted({item for revision in selected for item in revision.entity_ids}),
            claim_ids=sorted({item for revision in selected for item in revision.claim_ids}),
            conflict_ids=sorted({item for revision in selected for item in revision.conflict_ids}),
            media_content_ids=sorted(
                {item for revision in selected for item in revision.media_content_ids}
            ),
            media_occurrence_ids=sorted(
                {item for revision in selected for item in revision.media_occurrence_ids}
            ),
            media_relation_ids=sorted(
                {item for revision in selected for item in revision.media_relation_ids}
            ),
            visual_assertion_ids=sorted(
                {item for revision in selected for item in revision.visual_assertion_ids}
            ),
        )

    async def rollback_revision(self, revision_id: str) -> GraphRevision:
        with self.lock:
            data = self._read()
            previous_entities = {
                k: CanonicalEntity.model_validate(v) for k, v in data["entities"].items()
            }
            target_payload = next(
                (item for item in data["revisions"] if item["id"] == revision_id), None
            )
            if target_payload is None:
                raise KeyError(f"revision not found: {revision_id}")
            target = GraphRevision.model_validate(target_payload)
            if not target.changes:
                raise GraphIntegrityError(
                    "legacy revision has no snapshots and cannot be rolled back"
                )
            latest = GraphRevision.model_validate(data["revisions"][-1])
            if latest.run_id == f"rollback:{revision_id}":
                return latest
            buckets = {
                "entity": "entities",
                "claim": "claims",
                "conflict": "conflicts",
                "entity_operation": "entity_operations",
                "media_content": "media_contents",
                "media_occurrence": "media_occurrences",
                "media_relation": "media_relations",
                "visual_assertion": "visual_assertions",
            }
            for change in target.changes:
                if data[buckets[change.resource_type]].get(change.resource_id) != change.after:
                    raise GraphIntegrityError("STALE_ROLLBACK_RESOURCE: re-preview required")
            timestamp = datetime.now(UTC)
            inverse: list[GraphChange] = []
            rollback_order = {
                "entity_operation": 0,
                "claim": 1,
                "conflict": 2,
                "entity": 3,
                "visual_assertion": 0,
                "media_relation": 0,
                "media_occurrence": 1,
                "media_content": 4,
            }
            ordered_changes = sorted(
                reversed(target.changes),
                key=lambda item: rollback_order[item.resource_type],
            )
            for change in ordered_changes:
                bucket_name = {
                    "entity": "entities",
                    "claim": "claims",
                    "conflict": "conflicts",
                    "entity_operation": "entity_operations",
                    "media_content": "media_contents",
                    "media_occurrence": "media_occurrences",
                    "media_relation": "media_relations",
                    "visual_assertion": "visual_assertions",
                }[change.resource_type]
                bucket = data[bucket_name]
                current = bucket.get(change.resource_id)
                if change.action == "create":
                    if change.resource_type == "claim" and current is not None:
                        current["tx_to"] = timestamp.isoformat().replace("+00:00", "Z")
                    elif change.resource_type == "entity" and current is not None:
                        active_claims = [
                            claim
                            for claim in data["claims"].values()
                            if claim.get("tx_to") is None
                            and change.resource_id
                            in {claim.get("subject_id"), claim.get("object_entity_id")}
                        ]
                        if active_claims:
                            raise GraphIntegrityError(
                                f"entity {change.resource_id} still has active claim references"
                            )
                        current["active"] = False
                    elif change.resource_type == "conflict" and current is not None:
                        current["status"] = "resolved"
                    elif change.resource_type == "entity_operation" and current is not None:
                        current["status"] = "rolled_back"
                    elif change.resource_type in {
                        "media_occurrence",
                        "media_relation",
                        "visual_assertion",
                    } and current is not None:
                        current["active"] = False
                        current["tx_to"] = timestamp.isoformat().replace("+00:00", "Z")
                    elif change.resource_type == "media_content":
                        # Retain immutable content while historical occurrences may refer to it.
                        current = deepcopy(current)
                    inverse.append(
                        GraphChange(
                            resource_type=change.resource_type,
                            resource_id=change.resource_id,
                            action="close",
                            before=deepcopy(change.after),
                            after=deepcopy(current),
                        )
                    )
                elif change.before is not None:
                    bucket[change.resource_id] = deepcopy(change.before)
                    inverse.append(
                        GraphChange(
                            resource_type=change.resource_type,
                            resource_id=change.resource_id,
                            action="restore",
                            before=deepcopy(current),
                            after=deepcopy(change.before),
                        )
                    )
            compensation = GraphRevision(
                id=stable_id("revision", "rollback", revision_id, latest.id),
                run_id=f"rollback:{revision_id}",
                parent_id=latest.id,
                entity_ids=sorted(
                    {item.resource_id for item in inverse if item.resource_type == "entity"}
                ),
                claim_ids=sorted(
                    {item.resource_id for item in inverse if item.resource_type == "claim"}
                ),
                conflict_ids=sorted(
                    {item.resource_id for item in inverse if item.resource_type == "conflict"}
                ),
                media_content_ids=sorted(
                    {
                        item.resource_id
                        for item in inverse
                        if item.resource_type == "media_content"
                    }
                ),
                media_occurrence_ids=sorted(
                    {
                        item.resource_id
                        for item in inverse
                        if item.resource_type == "media_occurrence"
                    }
                ),
                media_relation_ids=sorted(
                    {
                        item.resource_id
                        for item in inverse
                        if item.resource_type == "media_relation"
                    }
                ),
                visual_assertion_ids=sorted(
                    {
                        item.resource_id
                        for item in inverse
                        if item.resource_type == "visual_assertion"
                    }
                ),
                changes=inverse,
                created_at=timestamp,
            )
            existing = next(
                (item for item in data["revisions"] if item["id"] == compensation.id), None
            )
            if existing is not None:
                return GraphRevision.model_validate(existing)
            restored_claims = [
                Claim.model_validate(data["claims"][c.resource_id])
                for c in inverse
                if c.resource_type == "claim"
            ]
            context = context_for_claims(
                [GraphRevision.model_validate(r) for r in reversed(data["revisions"])],
                {c.id for c in restored_claims},
            )
            compensation.validation_context = context
            transaction = GraphCommit(
                entities=[
                    CanonicalEntity.model_validate(data["entities"][eid])
                    for eid in compensation.entity_ids
                ],
                claims=restored_claims,
                revision=compensation,
                validation_context=context,
            )
            transaction = final_state_commit(
                transaction,
                {k: Claim.model_validate(v) for k, v in data["claims"].items()},
                previous_entities,
                [GraphRevision.model_validate(r) for r in reversed(data["revisions"])],
            )
            bind_commit_provenance(transaction)
            await ValidationService().commit(
                transaction,
                {k: CanonicalEntity.model_validate(v) for k, v in data["entities"].items()},
                {k: EvidenceRef.model_validate(v) for k, v in data["evidence"].items()},
                set(data["documents"]),
                self.evidence_store,
            )
            data["revisions"].append(compensation.model_dump(mode="json"))
            self._write_atomic(data)
            return compensation

    async def close(self) -> None:
        return None
