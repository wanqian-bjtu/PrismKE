"""Atomic local graph persistence and future Neo4j adapter boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import orjson

from prismke.errors import EvidenceRequiredError
from prismke.models import CanonicalEntity, Claim, ConflictSet, GraphRevision


class JSONGraphStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.path = directory / "graph.json"
        self.directory.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(
                {
                    "entities": {},
                    "claims": {},
                    "conflicts": {},
                    "revisions": [],
                }
            )

    def _read(self) -> dict[str, Any]:
        return cast(dict[str, Any], orjson.loads(self.path.read_bytes()))

    def _write(self, payload: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        temporary.replace(self.path)

    async def list_entities(self) -> list[CanonicalEntity]:
        data = self._read()
        return [CanonicalEntity.model_validate(item) for item in data["entities"].values()]

    async def list_claims(self) -> list[Claim]:
        data = self._read()
        return [Claim.model_validate(item) for item in data["claims"].values()]

    async def latest_revision(self) -> GraphRevision | None:
        revisions = self._read()["revisions"]
        return GraphRevision.model_validate(revisions[-1]) if revisions else None

    async def upsert_entity(self, entity: CanonicalEntity) -> None:
        data = self._read()
        entities = data["entities"]
        entities[entity.id] = entity.model_dump(mode="json")
        self._write(data)

    async def append_claim(self, claim: Claim) -> None:
        if not claim.evidence_ids:
            raise EvidenceRequiredError(f"claim {claim.id} has no evidence")
        data = self._read()
        claims = data["claims"]
        current = claims.get(claim.id)
        if current:
            merged = Claim.model_validate(current)
            merged.evidence_ids = sorted(set(merged.evidence_ids + claim.evidence_ids))
            merged.source_candidate_ids = sorted(
                set(merged.source_candidate_ids + claim.source_candidate_ids)
            )
            merged.confidence = max(merged.confidence, claim.confidence)
            claim = merged
        claims[claim.id] = claim.model_dump(mode="json")
        self._write(data)

    async def open_conflict(self, conflict: ConflictSet) -> None:
        data = self._read()
        data["conflicts"][conflict.id] = conflict.model_dump(mode="json")
        self._write(data)

    async def commit_revision(self, revision: GraphRevision) -> None:
        data = self._read()
        revisions = data["revisions"]
        if not any(item["id"] == revision.id for item in revisions):
            revisions.append(revision.model_dump(mode="json"))
        self._write(data)


class Neo4jGraphStore:
    """Reserved interface for the Neo4j milestone."""

    def __init__(self, *_: object, **__: object) -> None:
        raise NotImplementedError("Neo4j persistence is deferred until PrismKE v0.2")
