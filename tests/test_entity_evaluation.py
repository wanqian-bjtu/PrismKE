from __future__ import annotations

from pathlib import Path

import pytest

from prismke.evaluation import evaluate_entity_linking_manifest
from prismke.providers import MockEmbeddingProvider


@pytest.mark.asyncio
async def test_public_entity_manifest_is_reproducible() -> None:
    manifest = Path("examples/entity_resolution_v0_4/manifest.json")
    report = await evaluate_entity_linking_manifest(manifest, MockEmbeddingProvider())
    assert report.cases == 60
    assert report.governance_cases == 10
    assert 0.0 <= report.top_10_recall <= 1.0
    assert 0.0 <= report.top_1_accuracy <= 1.0
    assert 0.0 <= report.nil_f1 <= 1.0
    assert 0.0 <= report.b_cubed_f1 <= 1.0
    assert len(report.details) == 60
