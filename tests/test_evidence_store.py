from __future__ import annotations

from pathlib import Path

import pytest

from prismke.domain import SourceDocument
from prismke.parsing import ParserRegistry
from prismke.persistence import FileEvidenceStore


@pytest.mark.asyncio
async def test_evidence_round_trip_and_blob_addressing(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("evidence", encoding="utf-8")
    document = await ParserRegistry().parse(SourceDocument(path=source))
    store = FileEvidenceStore(tmp_path / "evidence")
    await store.put_document(document)
    evidence = await store.get(document.evidence[0].id)
    assert evidence.document_id == document.id
    assert await store.verify(evidence.id)
    assert (store.blobs_dir / document.source_hash[:2] / document.source_hash).is_file()


@pytest.mark.asyncio
async def test_tampered_evidence_metadata_fails_verification(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("evidence", encoding="utf-8")
    document = await ParserRegistry().parse(SourceDocument(path=source))
    store = FileEvidenceStore(tmp_path / "evidence")
    await store.put_document(document)
    ref_path = store._ref_path(document.evidence[0].id)
    ref_path.write_text("{}", encoding="utf-8")
    assert not await store.verify(document.evidence[0].id)
