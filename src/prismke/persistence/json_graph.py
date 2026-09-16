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

from prismke.core.errors import EvidenceRequiredError, GraphIntegrityError
from prismke.core.ids import stable_id
from prismke.domain import (
    CanonicalEntity,
    Claim,
    EntityEmbedding,
    EvidenceRef,
    GraphChange,
    GraphCommit,
    GraphHealth,
    GraphNeighborhood,
    GraphRevision,
    RevisionDiff,
)


class JSONGraphStore:
    def __init__(self, directory: Path) -> None:
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
        self, vector: list[float], entity_type: str, top_k: int
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
            if (
                not entity.active
                or entity.entity_type != entity_type
                or embedding_payload is None
            ):
                continue
            embedding = EntityEmbedding.model_validate(embedding_payload)
            if len(embedding.vector) != len(vector):
                continue
            candidate_norm = math.sqrt(
                sum(value * value for value in embedding.vector)
            ) or 1.0
            score = sum(
                left * right for left, right in zip(vector, embedding.vector, strict=True)
            ) / (query_norm * candidate_norm)
            matches.append((entity, max(-1.0, min(1.0, score))))
        return sorted(matches, key=lambda item: item[1], reverse=True)[:top_k]

    async def list_claims(self) -> list[Claim]:
        with self.lock:
            data = self._read()
        return [Claim.model_validate(item) for item in data["claims"].values()]

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
        merged = Claim.model_validate(current)
        merged.evidence_ids = sorted(set(merged.evidence_ids + incoming.evidence_ids))
        merged.source_candidate_ids = sorted(
            set(merged.source_candidate_ids + incoming.source_candidate_ids)
        )
        merged.confidence = max(merged.confidence, incoming.confidence)
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
            data["entities"][entity.id] = entity.model_dump(mode="json")
        for operation in transaction.entity_operations:
            data["entity_operations"][operation.id] = operation.model_dump(mode="json")
        for embedding in transaction.entity_embeddings:
            data["entity_embeddings"][embedding.entity_id] = embedding.model_dump(mode="json")
        for claim in transaction.claims:
            if not claim.evidence_ids:
                raise EvidenceRequiredError(f"claim {claim.id} has no evidence")
            current = data["claims"].get(claim.id)
            if current:
                claim = self._merge_claim(current, claim)
            data["claims"][claim.id] = claim.model_dump(mode="json")
        for conflict in transaction.conflicts:
            data["conflicts"][conflict.id] = conflict.model_dump(mode="json")

        known_entities = set(data["entities"])
        known_claims = set(data["claims"])
        known_conflicts = set(data["conflicts"])
        known_evidence = set(data["evidence"])
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
                raise GraphIntegrityError(f"claim {claim.id} references missing evidence")
        if not set(transaction.revision.entity_ids) <= known_entities:
            raise GraphIntegrityError("revision references missing entities")
        if not set(transaction.revision.claim_ids) <= known_claims:
            raise GraphIntegrityError("revision references missing claims")
        if not set(transaction.revision.conflict_ids) <= known_conflicts:
            raise GraphIntegrityError("revision references missing conflicts")
        for conflict in transaction.conflicts:
            if not set(conflict.claim_ids) <= known_claims:
                raise GraphIntegrityError(f"conflict {conflict.id} references missing claims")

        revisions.append(revision_payload)
        return data, False

    async def commit(self, transaction: GraphCommit) -> None:
        with self.lock:
            data = self._read()
            updated, is_noop = self._apply(deepcopy(data), transaction)
            if is_noop:
                return
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
        )

    async def rollback_revision(self, revision_id: str) -> GraphRevision:
        with self.lock:
            data = self._read()
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
            timestamp = datetime.now(UTC)
            inverse: list[GraphChange] = []
            for change in reversed(target.changes):
                bucket_name = {
                    "entity": "entities",
                    "claim": "claims",
                    "conflict": "conflicts",
                    "entity_operation": "entity_operations",
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
                changes=inverse,
                created_at=timestamp,
            )
            existing = next(
                (item for item in data["revisions"] if item["id"] == compensation.id), None
            )
            if existing is not None:
                return GraphRevision.model_validate(existing)
            data["revisions"].append(compensation.model_dump(mode="json"))
            self._write_atomic(data)
            return compensation

    async def close(self) -> None:
        return None
