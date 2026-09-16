from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

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


@pytest.mark.asyncio
async def test_dual_retrieval_rank_eleven_is_not_a_top_ten_hit(tmp_path, monkeypatch) -> None:
    from prismke.domain import EntityCandidate, EntityResolutionDecision
    from prismke.governance.entity_resolution import SemanticEntityResolver

    entities = [{"id": f"E{i}", "name": f"Name{i}", "entity_type": "Person"} for i in range(1, 12)]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "test",
                "entities": entities,
                "mentions": [
                    {
                        "id": "M1",
                        "name": "query",
                        "entity_type": "Person",
                        "cluster_id": "E11",
                        "expected_entity_id": "E11",
                    },
                ],
            }
        )
    )

    async def resolve(self, mentions):
        candidates = [
            EntityCandidate(
                entity_id=f"E{i}",
                retrieval_score=0.5,
                name_score=0.5,
                context_score=0.5,
                neighborhood_score=0.5,
                final_score=0.5,
                reasons=[],
            )
            for i in range(1, 12)
        ]
        return SimpleNamespace(
            decisions=[
                EntityResolutionDecision(
                    mention_id="M1",
                    candidates=candidates,
                    selected_entity_id=None,
                    method="review",
                    confidence=0.5,
                    margin=0.0,
                    requires_review=True,
                    reasons=[],
                )
            ]
        )

    monkeypatch.setattr(SemanticEntityResolver, "resolve", resolve)
    report = await evaluate_entity_linking_manifest(manifest, MockEmbeddingProvider())
    assert report.top_10_recall == 0.0
    assert len(report.details[0]["ranked_entity_ids"]) == 11
