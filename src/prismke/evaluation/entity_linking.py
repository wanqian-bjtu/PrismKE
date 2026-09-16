"""Reproducible evaluation for v0.4 entity linking and deduplication."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from pydantic import BaseModel

from prismke.domain import (
    CanonicalEntity,
    EntityMention,
    EntityTypeDef,
    GraphCommit,
    GraphRevision,
    OutputSchema,
    SchemaIndex,
)
from prismke.governance.entity_index import rebuild_entity_index
from prismke.governance.entity_resolution import SemanticEntityResolver
from prismke.persistence.json_graph import JSONGraphStore
from prismke.providers.base import EmbeddingProvider


class EntityLinkingEvaluationReport(BaseModel):
    cases: int
    governance_cases: int
    top_10_recall: float
    top_1_accuracy: float
    nil_precision: float
    nil_recall: float
    nil_f1: float
    b_cubed_precision: float
    b_cubed_recall: float
    b_cubed_f1: float
    review_rate: float
    false_auto_link_rate: float
    index_build_seconds: float
    resolution_seconds: float
    total_seconds: float
    indexed_entities_per_second: float
    mean_resolution_ms: float
    details: list[dict[str, Any]]


def _bcubed(actual: list[str], predicted: list[str]) -> tuple[float, float, float]:
    actual_groups: dict[str, set[int]] = defaultdict(set)
    predicted_groups: dict[str, set[int]] = defaultdict(set)
    for index, (actual_id, predicted_id) in enumerate(zip(actual, predicted, strict=True)):
        actual_groups[actual_id].add(index)
        predicted_groups[predicted_id].add(index)
    precisions: list[float] = []
    recalls: list[float] = []
    for index, (actual_id, predicted_id) in enumerate(zip(actual, predicted, strict=True)):
        del index
        overlap = actual_groups[actual_id] & predicted_groups[predicted_id]
        precisions.append(len(overlap) / len(predicted_groups[predicted_id]))
        recalls.append(len(overlap) / len(actual_groups[actual_id]))
    precision = sum(precisions) / len(precisions) if precisions else 0.0
    recall = sum(recalls) / len(recalls) if recalls else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


async def evaluate_entity_linking_manifest(
    manifest_path: Path,
    provider: EmbeddingProvider,
    *,
    top_k: int = 10,
    auto_link_threshold: float = 0.88,
    review_threshold: float = 0.65,
    min_margin: float = 0.08,
) -> EntityLinkingEvaluationReport:
    total_started = time.perf_counter()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entities = [CanonicalEntity.model_validate(item) for item in manifest["entities"]]
    types = sorted({item.entity_type for item in entities})
    schema = SchemaIndex(
        OutputSchema(
            schema_id="entity-eval-v0.4",
            version=str(manifest["version"]),
            strict=False,
            entity_types=[EntityTypeDef(id=item) for item in types],
            relations=[],
        )
    )
    with TemporaryDirectory(prefix="prismke-entity-eval-") as directory:
        store = JSONGraphStore(Path(directory) / "graph")
        await store.commit(
            GraphCommit(
                entities=entities,
                revision=GraphRevision(
                    id="revision:entity-eval",
                    run_id="entity-eval",
                    entity_ids=[item.id for item in entities],
                ),
            )
        )
        index_started = time.perf_counter()
        await rebuild_entity_index(
            store,
            provider,
            backend="json",
            batch_size=32,
            dry_run=False,
        )
        index_build_seconds = time.perf_counter() - index_started
        details: list[dict[str, Any]] = []
        actual_clusters: list[str] = []
        predicted_clusters: list[str] = []
        top_10_hits = 0
        top_1_hits = 0
        true_nil = predicted_nil = correct_nil = 0
        reviews = false_auto_links = 0
        resolution_started = time.perf_counter()
        for payload in manifest["mentions"]:
            expected = payload.get("expected_entity_id")
            mention = EntityMention(
                id=payload["id"],
                name=payload["name"],
                entity_type=payload["entity_type"],
                context=payload.get("context", ""),
                evidence_ids=[f"evidence:{payload['id']}"],
            )
            resolver = SemanticEntityResolver(
                schema,
                store,
                provider,
                run_id=f"eval:{mention.id}",
                top_k=top_k,
                auto_link_threshold=auto_link_threshold,
                review_threshold=review_threshold,
                min_margin=min_margin,
            )
            result = await resolver.resolve([mention])
            decision = (result.decisions or [])[0]
            ranked = [item.entity_id for item in decision.candidates]
            top_1 = decision.selected_entity_id or (ranked[0] if ranked else None)
            if expected is not None and (
                decision.selected_entity_id == expected or expected in ranked
            ):
                top_10_hits += 1
            if expected is not None and top_1 == expected:
                top_1_hits += 1
            is_true_nil = expected is None
            is_predicted_nil = decision.method == "nil"
            true_nil += int(is_true_nil)
            predicted_nil += int(is_predicted_nil)
            correct_nil += int(is_true_nil and is_predicted_nil)
            reviews += int(decision.requires_review)
            false_auto_links += int(
                expected is not None
                and decision.method in {"exact", "vector"}
                and decision.selected_entity_id != expected
            )
            actual_cluster = str(payload["cluster_id"])
            predicted_cluster = decision.selected_entity_id or f"unresolved:{mention.id}"
            actual_clusters.append(actual_cluster)
            predicted_clusters.append(predicted_cluster)
            details.append(
                {
                    "mention_id": mention.id,
                    "category": payload["category"],
                    "expected_entity_id": expected,
                    "predicted_entity_id": decision.selected_entity_id,
                    "method": decision.method,
                    "requires_review": decision.requires_review,
                    "ranked_entity_ids": ranked,
                }
            )
        resolution_seconds = time.perf_counter() - resolution_started
    count = len(details)
    nil_precision = correct_nil / predicted_nil if predicted_nil else 0.0
    nil_recall = correct_nil / true_nil if true_nil else 0.0
    nil_f1 = (
        2 * nil_precision * nil_recall / (nil_precision + nil_recall)
        if nil_precision + nil_recall
        else 0.0
    )
    bc_precision, bc_recall, bc_f1 = _bcubed(actual_clusters, predicted_clusters)
    link_cases = count - true_nil
    return EntityLinkingEvaluationReport(
        cases=count,
        governance_cases=len(manifest["governance"]),
        top_10_recall=top_10_hits / link_cases if link_cases else 0.0,
        top_1_accuracy=top_1_hits / link_cases if link_cases else 0.0,
        nil_precision=nil_precision,
        nil_recall=nil_recall,
        nil_f1=nil_f1,
        b_cubed_precision=bc_precision,
        b_cubed_recall=bc_recall,
        b_cubed_f1=bc_f1,
        review_rate=reviews / count if count else 0.0,
        false_auto_link_rate=false_auto_links / link_cases if link_cases else 0.0,
        index_build_seconds=index_build_seconds,
        resolution_seconds=resolution_seconds,
        total_seconds=time.perf_counter() - total_started,
        indexed_entities_per_second=(
            len(entities) / index_build_seconds if index_build_seconds else 0.0
        ),
        mean_resolution_ms=(resolution_seconds * 1000 / count if count else 0.0),
        details=details,
    )
