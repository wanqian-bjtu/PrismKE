"""Explicit synthetic schema/evidence for pre-v0.5 storage test fixtures.

This prepares test data, not an alternate validation policy. New boundary tests
use the unwrapped production GraphStore and deliberately omit this preparation.
"""

from pathlib import Path

from prismke.core.ids import canonical_hash
from prismke.domain import (
    CommitValidationContext,
    EntityTypeDef,
    EvidenceKind,
    EvidenceRef,
    GraphCommit,
    GraphDocument,
    Modality,
    OutputSchema,
    RelationDef,
)
from prismke.persistence import FileEvidenceStore
from prismke.persistence import JSONGraphStore as ProductionJSONGraphStore

SCHEMA = OutputSchema(
    schema_id="storage-fixtures",
    version="1",
    entity_types=[
        EntityTypeDef(id="Thing"),
        EntityTypeDef(id="Software"),
        EntityTypeDef(id="Organization"),
    ],
    relations=[
        RelationDef(id=r)
        for r in ["r", "name", "version", "developed_by", "related_to", "described_as"]
    ],
)


async def prepare_fixture_commit(store: object, transaction: GraphCommit) -> None:
    if transaction.validation_context is not None or not transaction.claims:
        return
    evidence_store = getattr(store, "evidence_store", None)
    if evidence_store is None:
        directory = getattr(store, "directory", Path("runtime/test-fixtures"))
        evidence_store = FileEvidenceStore(directory / "fixture-evidence")
        store.evidence_store = evidence_store
    blob_hash = await evidence_store.put_blob(b"Synthetic storage fixture evidence.", "text/plain")
    known = {ref.id: ref for ref in transaction.evidence}
    refs = []
    for eid in sorted({e for c in transaction.claims for e in c.evidence_ids}):
        ref = known.get(eid) or EvidenceRef(
            id=eid,
            kind=EvidenceKind.TEXT_SPAN,
            document_id="document:fixture",
            source_hash=blob_hash,
            modality=Modality.TEXT,
        )
        ref.source_hash = blob_hash
        await evidence_store.put_ref(ref)
        refs.append(ref)
    transaction.evidence = refs
    known_documents = {d.id: d for d in transaction.documents}
    for ref in refs:
        known_documents.setdefault(
            ref.document_id,
            GraphDocument(
                id=ref.document_id,
                filename="fixture.txt",
                content_hash=blob_hash,
                media_type="text/plain",
            ),
        )
    for document in known_documents.values():
        document.content_hash = blob_hash
    transaction.documents = list(known_documents.values())
    schema_id = canonical_hash(SCHEMA.model_dump(mode="json"))
    transaction.validation_context = CommitValidationContext(
        schemas={schema_id: SCHEMA}, claim_schema_ids={c.id: schema_id for c in transaction.claims}
    )
    transaction.revision.validation_context = transaction.validation_context


class JSONGraphStore(ProductionJSONGraphStore):
    async def commit(self, transaction: GraphCommit) -> None:
        await prepare_fixture_commit(self, transaction)
        await super().commit(transaction)
