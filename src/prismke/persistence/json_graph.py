"""Atomic local graph persistence and future Neo4j boundary."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import orjson
from filelock import FileLock

from prismke.core.errors import EvidenceRequiredError, GraphIntegrityError
from prismke.domain import CanonicalEntity, Claim, GraphCommit, GraphRevision


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
        return {"entities": {}, "claims": {}, "conflicts": {}, "revisions": []}

    def _read(self) -> dict[str, Any]:
        return cast(dict[str, Any], orjson.loads(self.path.read_bytes()))

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

    async def list_entities(self) -> list[CanonicalEntity]:
        with self.lock:
            data = self._read()
        return [CanonicalEntity.model_validate(item) for item in data["entities"].values()]

    async def list_claims(self) -> list[Claim]:
        with self.lock:
            data = self._read()
        return [Claim.model_validate(item) for item in data["claims"].values()]

    async def latest_revision(self) -> GraphRevision | None:
        with self.lock:
            revisions = self._read()["revisions"]
        return GraphRevision.model_validate(revisions[-1]) if revisions else None

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
            if existing_revision != revision_payload:
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

        for entity in transaction.entities:
            data["entities"][entity.id] = entity.model_dump(mode="json")
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
        for claim in transaction.claims:
            entity_refs = {claim.subject_id}
            if claim.object_entity_id:
                entity_refs.add(claim.object_entity_id)
            if not entity_refs <= known_entities:
                raise GraphIntegrityError(f"claim {claim.id} references missing entities")
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
            updated, is_noop = self._apply(data, transaction)
            if is_noop:
                return
            self._write_atomic(updated)


class Neo4jGraphStore:
    """Reserved interface for the Neo4j milestone."""

    def __init__(self, *_: object, **__: object) -> None:
        raise NotImplementedError("Neo4j persistence is deferred until PrismKE v0.2")
