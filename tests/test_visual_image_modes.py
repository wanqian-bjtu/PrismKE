import base64
import json
from io import BytesIO

import httpx
import pytest
from PIL import Image

from prismke.domain import Claim, DocumentIR, MediaAsset, OutputSchema, VisualExtractionRequest
from prismke.governance.risk import route_by_risk
from prismke.providers.vlm import OpenAICompatibleVLMProvider


def test_cmyk_request_copy_preserves_original(tmp_path):
    path = tmp_path / "source.jpg"
    Image.new("CMYK", (80, 120), (0, 80, 40, 0)).save(path)
    original = path.read_bytes()
    provider = OpenAICompatibleVLMProvider("https://example.test/v1", "test", "test")
    result = provider._image_data_url(str(path))
    with Image.open(BytesIO(base64.b64decode(result.split(",", 1)[1]))) as image:
        assert image.mode == "RGB"
        assert image.size == (80, 120)
    assert path.read_bytes() == original


@pytest.mark.asyncio
@pytest.mark.parametrize("confidence", ["high", None, 2, "NaN"])
async def test_invalid_observation_confidence_is_flagged_for_review(tmp_path, confidence):
    path = tmp_path / "source.png"
    Image.new("RGB", (80, 120)).save(path)
    asset = MediaAsset(id="media", path=str(path), media_type="image/png", evidence_id="ev")
    document = DocumentIR(
        id="doc",
        source_path=str(path),
        source_hash="a" * 64,
        media_type="image/png",
        media_assets=[asset],
    )
    payload = {
        "observations": [{"label": "A B", "confidence": confidence, "bbox": [0.8, 0.2, 0.1, 0.9]}],
        "claims": [
            {
                "subject": "A",
                "subject_type": "Thing",
                "object": "B",
                "relation": "r",
                "confidence": 0.99,
                "observation_index": 0,
            }
        ],
    }

    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(payload)}}],
                "usage": {"total_tokens": 10},
            },
        )

    provider = OpenAICompatibleVLMProvider(
        "https://example.test/v1", "test", "test", transport=httpx.MockTransport(handler)
    )
    result = await provider.extract(
        VisualExtractionRequest(
            document=document,
            asset=asset,
            output_schema=OutputSchema(schema_id="s", version="1", entity_types=[], relations=[]),
        )
    )
    assert result.observations[0].confidence == 0
    assert result.observations[0].bbox is None
    assert result.candidates[0].uncalibrated_visual_confidence
    claim = Claim(
        id="c",
        subject_id="a",
        relation_id="r",
        object_literal="B",
        confidence=0.99,
        evidence_ids=["ev"],
        cross_modal_support=True,
        uncalibrated_visual_confidence=True,
    )
    _, reviews = route_by_risk("run", [claim], [])
    assert claim.status == "review_required"
    assert "uncalibrated_visual_confidence" in reviews[0].reasons
