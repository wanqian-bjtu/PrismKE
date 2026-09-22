from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import orjson
import pytest

from prismke.core.errors import GraphIntegrityError
from prismke.core.ids import canonical_hash
from prismke.domain import Claim, EvidenceKind, EvidenceRef, GraphRevision, Modality
from prismke.persistence.file_evidence import FileEvidenceStore
from prismke.persistence.legacy_evidence import (
    SAMPLE_CLAIM_ID,
    SAMPLE_EVIDENCE_ID,
    closure_commit,
    legacy_snapshot,
    restore_sample_evidence,
    verify_active_claims,
)


def make_claim(claim_id: str, evidence_id: str) -> Claim:
    return Claim(
        id=claim_id,
        subject_id="entity:test",
        relation_id="described_as",
        object_literal="test",
        confidence=0.9,
        evidence_ids=[evidence_id],
    )


def test_closure_commit_pins_claim_content_and_preserves_history() -> None:
    claim = make_claim("claim:governance:abc", "evidence:governance:abc")
    manifest = {
        "parent_id": "revision:head",
        "governance": [
            {"id": claim.id, "fingerprint": canonical_hash(claim.model_dump(mode="json"))}
        ],
    }
    commit = closure_commit(manifest, [claim])
    assert commit.claims[0].tx_to is not None
    assert claim.tx_to is None
    assert commit.claims[0].status == claim.status
    assert commit.revision.parent_id == "revision:head"
    assert commit.revision.changes[0].before == claim.model_dump(mode="json")
    assert commit.revision.changes[0].after == commit.claims[0].model_dump(mode="json")
    with pytest.raises(GraphIntegrityError, match="changed"):
        closure_commit(manifest, [claim.model_copy(update={"object_literal": "modified"})])
    with pytest.raises(GraphIntegrityError, match="changed"):
        closure_commit(manifest, [])


@pytest.mark.asyncio
async def test_snapshot_rejects_unexpected_or_closed_governance_claim() -> None:
    store = SimpleNamespace(list_claims=AsyncMock(return_value=[]))
    source = SimpleNamespace()
    with pytest.raises(GraphIntegrityError, match="counts"):
        await legacy_snapshot(store, source)
    governance = [
        make_claim(f"claim:governance:{index}", f"evidence:governance:{index}")
        for index in range(9)
    ]
    historical = [
        make_claim(f"claim:test:{index}", f"evidence:test:{index}").model_copy(
            update={"tx_to": governance[0].tx_from}
        )
        for index in range(16)
    ]
    governance[0] = governance[0].model_copy(update={"tx_to": governance[0].tx_from})
    store.list_claims.return_value = governance + historical
    with pytest.raises(GraphIntegrityError, match="no longer an active"):
        await legacy_snapshot(store, source)


@pytest.mark.asyncio
async def test_snapshot_pins_all_fixture_sources() -> None:
    governance = [
        make_claim(f"claim:governance:{index}", f"evidence:governance:{index}")
        for index in range(9)
    ]
    historical = [
        make_claim(f"claim:test:{index}", f"evidence:test:{index}").model_copy(
            update={"relation_id": "name", "tx_to": governance[0].tx_from}
        )
        for index in range(16)
    ]
    sample = make_claim(SAMPLE_CLAIM_ID, SAMPLE_EVIDENCE_ID)
    sample_ref = EvidenceRef(
        id=SAMPLE_EVIDENCE_ID,
        kind=EvidenceKind.TEXT_SPAN,
        document_id="doc:sample",
        source_hash="a" * 64,
        modality=Modality.TEXT,
    )
    rows = []
    for claims, filename, digest in (
        (governance, "governance.md", "c" * 64),
        (historical, "test.md", "b" * 64),
    ):
        for claim in claims:
            ref = sample_ref.model_copy(
                update={"id": claim.evidence_ids[0], "source_hash": digest}
            )
            rows.append(
                {
                    "claim_id": claim.id,
                    "evidence_id": ref.id,
                    "filename": filename,
                    "content_hash": digest,
                    "evidence_payload": orjson.dumps(ref.model_dump(mode="json")),
                }
            )
    result = SimpleNamespace(data=AsyncMock(return_value=rows))
    session = MagicMock()
    session.__aenter__.return_value = session
    session.run = AsyncMock(return_value=result)
    store = SimpleNamespace(
        database="neo4j",
        driver=SimpleNamespace(session=MagicMock(return_value=session)),
        list_claims=AsyncMock(return_value=governance + historical + [sample]),
        get_evidence=AsyncMock(return_value=sample_ref),
        latest_revision=AsyncMock(return_value=GraphRevision(id="revision:head", run_id="old")),
    )
    source = SimpleNamespace(
        verify=AsyncMock(return_value=True), get=AsyncMock(return_value=sample_ref)
    )
    snapshot = await legacy_snapshot(store, source)
    assert len(snapshot["governance"]) == 9
    assert len(snapshot["historical_closed_ids"]) == 16
    assert snapshot["active_claim_count"] == 10
    rows[0]["content_hash"] = "a" * 64
    with pytest.raises(GraphIntegrityError, match="fixture provenance"):
        await legacy_snapshot(store, source)


@pytest.mark.asyncio
async def test_sample_evidence_copy_and_tamper_detection(tmp_path: Path) -> None:
    source = FileEvidenceStore(tmp_path / "source")
    target = FileEvidenceStore(tmp_path / "target")
    blob = b"sample original evidence"
    digest = sha256(blob).hexdigest()
    assert await source.put_blob(blob, "text/plain") == digest
    ref = EvidenceRef(
        id=SAMPLE_EVIDENCE_ID,
        kind=EvidenceKind.TEXT_SPAN,
        document_id="doc:sample",
        source_hash=digest,
        modality=Modality.TEXT,
        char_start=0,
        char_end=6,
    )
    await source.put_ref(ref)
    store = SimpleNamespace(get_evidence=AsyncMock(return_value=ref))
    await restore_sample_evidence(store, source, target)
    assert await target.get(ref.id) == ref
    assert await target.verify(ref.id)
    target._blob_path(digest).write_bytes(b"tampered")
    assert not await target.verify(ref.id)


@pytest.mark.asyncio
async def test_active_verification_excludes_only_explicit_closures(tmp_path: Path) -> None:
    target = FileEvidenceStore(tmp_path / "evidence")
    blob = b"sample"
    digest = await target.put_blob(blob, "text/plain")
    ref = EvidenceRef(
        id=SAMPLE_EVIDENCE_ID,
        kind=EvidenceKind.TEXT_SPAN,
        document_id="doc:sample",
        source_hash=digest,
        modality=Modality.TEXT,
    )
    await target.put_ref(ref)
    sample = make_claim(SAMPLE_CLAIM_ID, ref.id)
    legacy = make_claim("claim:governance:abc", "evidence:governance:abc")
    store = SimpleNamespace(
        list_claims=AsyncMock(return_value=[sample, legacy]),
        get_evidence=AsyncMock(return_value=ref),
    )
    assert await verify_active_claims(store, target, exclude_ids={legacy.id}) == 1
    with pytest.raises(GraphIntegrityError, match="evidence"):
        await verify_active_claims(store, target)
