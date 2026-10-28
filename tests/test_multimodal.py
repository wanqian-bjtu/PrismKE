from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import pytest
from docx import Document
from docx.shared import Inches
from PIL import Image

from src.core.settings import Settings
from src.domain import (
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
    TextBlock,
    VisualExtractionRequest,
)
from src.governance import MultimodalAlignmentService
from src.parsing import ParserRegistry, select_analysis_assets
from src.providers import OpenAICompatibleVLMProvider, PaddleOCRProvider
from src.workflow import PrismKEService


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
    assert "alt: chart" in document.media_assets[0].context_text
    assert "figcaption: Caption" in document.media_assets[0].context_text
    text_refs = [item for item in document.evidence if item.source_locator]
    assert text_refs
    assert all(item.source_locator["document_kind"] == "continuous_html" for item in text_refs)
    assert text_refs[0].source_locator["selector"] == "p:nth-of-type(1)"
    assert text_refs[0].source_locator["character_range"] == [0, len("Context")]


@pytest.mark.asyncio
async def test_html_image_context_is_local_not_entire_parent(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    _image(image)
    encoded = base64.b64encode(image.read_bytes()).decode("ascii")
    html = tmp_path / "sample.html"
    html.write_text(
        "<html><body><div>Distant page content</div><p>Previous fact</p>"
        f'<img alt="diagram" title="release" '
        f'src="data:image/png;base64,{encoded}">'
        "<p>Next fact</p><div>Unrelated footer</div></body></html>",
        encoding="utf-8",
    )
    document = await ParserRegistry(asset_dir=tmp_path / "assets").parse(SourceDocument(path=html))
    context = document.media_assets[0].context_text
    assert "alt: diagram" in context
    assert "title: release" in context
    assert "nearby: Previous fact" in context
    assert "nearby: Next fact" in context
    assert "Distant page content" not in context
    assert "Unrelated footer" not in context


@pytest.mark.asyncio
async def test_docx_embedded_image_keeps_paragraph_context(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    _image(image)
    path = tmp_path / "sample.docx"
    docx = Document()
    paragraph = docx.add_paragraph("PrismKE architecture")
    paragraph.add_run().add_picture(str(image), width=Inches(1))
    docx.save(path)
    document = await ParserRegistry(asset_dir=tmp_path / "assets").parse(SourceDocument(path=path))
    assert document.text_blocks[0].text == "PrismKE architecture"
    assert document.media_assets[0].origin == "docx_embedded"
    assert document.media_assets[0].context_text == "PrismKE architecture"


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
            200,
            json={
                "id": "req-vision-safe",
                "model": "qwen3.7-flash",
                "usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 40,
                    "total_tokens": 240,
                },
                "choices": [{"message": {"content": json.dumps(payload)}}],
            },
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
    assert result.call_records[0].provider == "vlm"
    assert result.call_records[0].total_tokens == 240
    assert result.call_records[0].estimated_cost_cny is not None


@pytest.mark.asyncio
async def test_vlm_prioritizes_image_ocr_and_flags_context_only_claims(
    tmp_path: Path,
) -> None:
    image = tmp_path / "conflict.png"
    _image(image)
    asset = MediaAsset(
        id="media:conflict",
        path=str(image),
        media_type="image/png",
        width=128,
        height=96,
        evidence_id="ev:asset",
        blob_hash="c" * 64,
        context_text="nearby: AtlasFlow was developed by Harbor Research.",
    )
    document = DocumentIR(
        id="doc:conflict",
        source_path=str(image),
        source_hash="c" * 64,
        media_type="image/png",
        media_assets=[asset],
    )
    ocr_block = TextBlock(
        id="block:ocr",
        text="AtlasFlow developed by Contoso AI",
        evidence_id="ev:ocr",
        modality=Modality.OCR,
        source_media_asset_id=asset.id,
    )
    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        prompt = body["messages"][0]["content"][0]["text"]
        assert "IMAGE-DERIVED OCR (PRIMARY)" in prompt
        assert "AUXILIARY DOCUMENT CONTEXT (UNTRUSTED)" in prompt
        assert "Never replace visible image content with auxiliary context" in prompt
        assert prompt.index("IMAGE-DERIVED OCR (PRIMARY)") < prompt.index(
            "AUXILIARY DOCUMENT CONTEXT (UNTRUSTED)"
        )
        payload = {
            "observations": [
                {
                    "label": "Contoso AI",
                    "description": "Visible developer name",
                    "confidence": 0.98,
                    "bbox": [0.4, 0.4, 0.8, 0.7],
                }
            ],
            "claims": [
                {
                    "subject": "AtlasFlow",
                    "relation": "developed_by",
                    "object": "Contoso AI",
                    "subject_type": "Software",
                    "object_type": "Organization",
                    "confidence": 0.96,
                    "observation_index": 0,
                },
                {
                    "subject": "AtlasFlow",
                    "relation": "developed_by",
                    "object": "Harbor Research",
                    "subject_type": "Software",
                    "object_type": "Organization",
                    "confidence": 0.9,
                },
            ],
        }
        return httpx.Response(
            200,
            json={
                "id": "req-conflict",
                "model": "qwen3.7-flash",
                "usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 80,
                    "total_tokens": 280,
                },
                "choices": [{"message": {"content": json.dumps(payload)}}],
            },
        )

    provider = OpenAICompatibleVLMProvider(
        "https://example.test/v1", "secret", "vision", transport=httpx.MockTransport(handler)
    )
    result = await provider.extract(
        VisualExtractionRequest(
            document=document,
            output_schema=schema,
            asset=asset,
            ocr_blocks=[ocr_block],
        )
    )
    visible, context_only = result.candidates
    assert isinstance(visible.object, EntityMention)
    assert visible.object.name == "Contoso AI"
    assert not visible.context_only_visual_claim
    assert context_only.context_only_visual_claim
    assert any(item.startswith("context_only_visual_claim") for item in result.warnings)


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
    assert merged[0].cross_modal_support
    assert records[0].decision == "support"


def test_ocr_and_image_support_does_not_double_count_confidence() -> None:
    def candidate(identifier: str, modality: Modality, evidence: str) -> CandidateClaim:
        return CandidateClaim(
            id=identifier,
            subject=EntityMention(
                id=f"mention:{identifier}",
                name="VisionDesk",
                entity_type="Software",
                modality=modality,
                evidence_ids=[evidence],
            ),
            relation="developed_by",
            object="Northstar Labs",
            confidence=0.8,
            evidence_ids=[evidence],
            modalities=[modality],
        )

    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])
    merged, records = MultimodalAlignmentService().align(
        [candidate("ocr", Modality.OCR, "ev:ocr")],
        [candidate("vision", Modality.IMAGE, "ev:image")],
        SchemaIndex(schema),
    )
    assert merged[0].confidence == 0.8
    assert not merged[0].cross_modal_support
    assert records[0].decision == "support"


def test_cross_modal_candidates_with_shared_subject_are_related() -> None:
    def candidate(identifier: str, relation: str, modality: Modality) -> CandidateClaim:
        return CandidateClaim(
            id=identifier,
            subject=EntityMention(
                id=f"mention:{identifier}",
                name="PrismKE",
                entity_type="System",
                modality=modality,
                evidence_ids=[f"ev:{identifier}"],
            ),
            relation=relation,
            object="Value",
            confidence=0.8,
            evidence_ids=[f"ev:{identifier}"],
            modalities=[modality],
        )

    schema = OutputSchema(schema_id="s", version="1", entity_types=[], relations=[])
    _, records = MultimodalAlignmentService().align(
        [candidate("text", "created_by", Modality.TEXT)],
        [candidate("vision", "shown_with", Modality.IMAGE)],
        SchemaIndex(schema),
    )
    related = [record for record in records if record.decision == "related"]
    assert len(related) == 1
    assert related[0].candidate_ids == ["text", "vision"]
    assert related[0].reasons == ["shared_subject_different_relation"]


def test_vlm_configuration_is_strict(tmp_path: Path) -> None:
    service = PrismKEService(
        Settings(
            _env_file=None,
            runtime_dir=tmp_path / "runtime",
            vlm_api_key=None,
            vlm_model=None,
        )
    )
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


@pytest.mark.asyncio
async def test_paddle_provider_skips_engine_for_document_without_assets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = PaddleOCRProvider()

    def unexpected_engine() -> object:
        raise AssertionError("OCR engine should not initialize")

    monkeypatch.setattr(provider, "_get_engine", unexpected_engine)
    result = await provider.recognize(
        OCRRequest(
            document=DocumentIR(
                id="doc:text-only",
                source_path="text.md",
                source_hash="d" * 64,
                media_type="text/markdown",
            )
        )
    )
    assert result.text_blocks == []


def test_scanned_pdf_render_suppresses_duplicate_embedded_asset() -> None:
    embedded = MediaAsset(
        id="media:embedded",
        path="embedded.png",
        media_type="image/png",
        page_number=1,
        evidence_id="ev:embedded",
        origin="pdf_embedded",
    )
    rendered = MediaAsset(
        id="media:rendered",
        path="rendered.png",
        media_type="image/png",
        page_number=1,
        evidence_id="ev:rendered",
        origin="pdf_page_render",
        requires_ocr=True,
    )
    document = DocumentIR(
        id="doc:scan",
        source_path="scan.pdf",
        source_hash="c" * 64,
        media_type="application/pdf",
        media_assets=[embedded, rendered],
    )
    assert select_analysis_assets(document) == [rendered]
