from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

from prismke.core.settings import Settings
from prismke.domain import (
    BBox,
    CandidateClaim,
    DocumentIR,
    EntityMention,
    MediaAsset,
    Modality,
    OCRRequest,
    OutputSchema,
    SchemaIndex,
    SourceDocument,
    VisualExtractionRequest,
)
from prismke.governance import MultimodalAlignmentService
from prismke.parsing import ParserRegistry
from prismke.providers import OpenAICompatibleVLMProvider, PaddleOCRProvider
from prismke.workflow import PrismKEService


def _image(path: Path) -> None:
    Image.new("RGB", (128, 96), "white").save(path)


@pytest.mark.asyncio
async def test_markdown_embedded_image_and_remote_block(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    _image(image)
    markdown = tmp_path / "sample.md"
    markdown.write_text(
        "Fact\n![local](figure.png)\n![remote](https://example.test/image.png)\n",
        encoding="utf-8",
    )
    document = await ParserRegistry(asset_dir=tmp_path / "assets").parse(
        SourceDocument(path=markdown)
    )
    assert len(document.media_assets) == 1
    assert document.media_assets[0].context_text == "local"
    assert any(item.startswith("remote_asset_blocked") for item in document.warnings)


@pytest.mark.asyncio
async def test_html_data_uri_image(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    _image(image)
    encoded = base64.b64encode(image.read_bytes()).decode("ascii")
    html = tmp_path / "sample.html"
    html.write_text(
        f'<p>Context</p><figure><img alt="chart" src="data:image/png;base64,{encoded}">'
        "<figcaption>Caption</figcaption></figure>",
        encoding="utf-8",
    )
    document = await ParserRegistry(asset_dir=tmp_path / "assets").parse(SourceDocument(path=html))
    assert document.media_assets[0].origin == "html_embedded"
    assert "chart" in document.media_assets[0].context_text


@pytest.mark.asyncio
async def test_vlm_region_evidence_with_mock_transport(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    _image(image)
    asset = MediaAsset(
        id="media:1",
        path=str(image),
        media_type="image/png",
        width=128,
        height=96,
        evidence_id="ev:asset",
        blob_hash="a" * 64,
    )
    document = DocumentIR(
        id="doc:1",
        source_path=str(image),
        source_hash="a" * 64,
        media_type="image/png",
        media_assets=[asset],
    )
    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["messages"][0]["content"][1]["type"] == "image_url"
        payload = {
            "observations": [{"label": "A", "confidence": 0.9, "bbox": [0.1, 0.2, 0.8, 0.9]}],
            "claims": [
                {
                    "subject": "A",
                    "relation": "r",
                    "object": "B",
                    "subject_type": "Thing",
                    "confidence": 0.9,
                    "observation_index": 0,
                }
            ],
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(payload)}}]}
        )

    provider = OpenAICompatibleVLMProvider(
        "https://example.test/v1", "secret", "vision", transport=httpx.MockTransport(handler)
    )
    result = await provider.extract(
        VisualExtractionRequest(document=document, output_schema=schema, asset=asset)
    )
    assert result.observations[0].bbox is not None
    assert result.candidates[0].modalities == [Modality.IMAGE]
    assert result.evidence[0].media_asset_id == asset.id


def test_cross_modal_support_merges_evidence() -> None:
    def candidate(identifier: str, modality: Modality, evidence: str) -> CandidateClaim:
        subject = EntityMention(
            id=f"mention:{identifier}",
            name="PrismKE",
            entity_type="Thing",
            modality=modality,
            evidence_ids=[evidence],
        )
        return CandidateClaim(
            id=identifier,
            subject=subject,
            relation="created_by",
            object="Team",
            confidence=0.8,
            evidence_ids=[evidence],
            modalities=[modality],
        )

    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])
    merged, records = MultimodalAlignmentService().align(
        [candidate("text", Modality.TEXT, "ev:text")],
        [candidate("vision", Modality.IMAGE, "ev:image")],
        SchemaIndex(schema),
    )
    assert len(merged) == 1
    assert merged[0].confidence == pytest.approx(0.85)
    assert set(merged[0].evidence_ids) == {"ev:text", "ev:image"}
    assert records[0].decision == "support"


def test_vlm_configuration_is_strict(tmp_path: Path) -> None:
    service = PrismKEService(Settings(runtime_dir=tmp_path / "runtime"))
    with pytest.raises(Exception, match="PRISMKE_VLM_API_KEY"):
        service.vlm_provider("openai-compatible")


@pytest.mark.asyncio
async def test_paddle_provider_converts_lines_to_bbox(tmp_path: Path) -> None:
    image = tmp_path / "ocr.png"
    _image(image)
    asset = MediaAsset(
        id="media:ocr",
        path=str(image),
        media_type="image/png",
        width=128,
        height=96,
        evidence_id="ev:asset",
        blob_hash="b" * 64,
        requires_ocr=True,
    )
    document = DocumentIR(
        id="doc:ocr",
        source_path=str(image),
        source_hash="b" * 64,
        media_type="image/png",
        media_assets=[asset],
    )

    class Result:
        json = {
            "res": {
                "rec_texts": ["PrismKE"],
                "rec_scores": [0.93],
                "rec_polys": [[[10, 20], [90, 20], [90, 50], [10, 50]]],
            }
        }

    class Engine:
        def predict(self, path: str):  # type: ignore[no-untyped-def]
            assert path == str(image)
            return [Result()]

    provider = PaddleOCRProvider()
    provider._engine = Engine()
    result = await provider.recognize(OCRRequest(document=document))
    assert result.text_blocks[0].text == "PrismKE"
    assert result.text_blocks[0].modality == Modality.OCR
    assert result.evidence[0].bbox == BBox(x0=10, y0=20, x1=90, y1=50)
