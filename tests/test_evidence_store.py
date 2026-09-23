from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.core.ids import stable_id
from src.domain import (
    BBox,
    CoordinateSpace,
    EvidenceKind,
    EvidenceRef,
    LocalizationLevel,
    Modality,
    SourceDocument,
)
from src.parsing import ParserRegistry
from src.persistence import FileEvidenceStore


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


@pytest.mark.asyncio
async def test_visual_region_can_be_exported_as_crop(tmp_path: Path) -> None:
    source = tmp_path / "image.png"
    Image.new("RGB", (100, 80), "white").save(source)
    document = await ParserRegistry(asset_dir=tmp_path / "assets").parse(
        SourceDocument(path=source)
    )
    store = FileEvidenceStore(tmp_path / "evidence")
    await store.put_document(document)
    asset = document.media_assets[0]
    evidence = EvidenceRef(
        id=stable_id("ev", asset.id, "crop"),
        kind=EvidenceKind.VISUAL_REGION,
        document_id=document.id,
        source_hash=asset.blob_hash or document.source_hash,
        modality=Modality.IMAGE,
        bbox=BBox(x0=0.1, y0=0.25, x1=0.6, y1=0.75),
        media_asset_id=asset.id,
        coordinate_space=CoordinateSpace.NORMALIZED,
        canvas_width=100,
        canvas_height=80,
        localization_level=LocalizationLevel.REGION,
    )
    await store.put_ref(evidence)
    cropped_path = tmp_path / "crop.png"
    cropped_path.write_bytes(await store.crop(evidence.id))
    with Image.open(cropped_path) as cropped:
        assert cropped.size == (50, 40)
