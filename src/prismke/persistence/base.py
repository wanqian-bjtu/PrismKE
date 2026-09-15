"""Persistence extension boundaries."""

from __future__ import annotations

from typing import Protocol

from prismke.domain import (
    CanonicalEntity,
    Claim,
    DocumentIR,
    EvidenceRef,
    GraphCommit,
    GraphRevision,
)


class GraphStore(Protocol):
    async def list_entities(self) -> list[CanonicalEntity]: ...

    async def list_claims(self) -> list[Claim]: ...

    async def latest_revision(self) -> GraphRevision | None: ...

    async def commit(self, transaction: GraphCommit) -> None: ...


class EvidenceStore(Protocol):
    async def put_document(self, document: DocumentIR) -> None: ...

    async def put_blob(self, content: bytes, media_type: str) -> str: ...

    async def put_ref(self, evidence: EvidenceRef) -> None: ...

    async def get_blob(self, blob_hash: str) -> bytes: ...

    async def crop(self, evidence_id: str) -> bytes: ...

    async def get(self, evidence_id: str) -> EvidenceRef: ...

    async def exists(self, evidence_id: str) -> bool: ...

    async def verify(self, evidence_id: str) -> bool: ...
