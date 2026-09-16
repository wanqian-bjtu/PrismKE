"""Reproducible evaluation for v0.4 entity linking and deduplication."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal

from pydantic import BaseModel, Field

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
from prismke.governance.entity_resolution import (
    ENTITY_RESOLUTION_POLICY_VERSION,
    SemanticEntityResolver,
)
from prismke.persistence.json_graph import JSONGraphStore
from prismke.providers.base import EmbeddingProvider


class EntityLinkingEvaluationReport(BaseModel):
    protocol: Literal["fixed", "sequential"] = "fixed"
    provenance: dict[str, Any] = Field(default_factory=dict)
    denominators: dict[str, int] = Field(default_factory=dict)
    modality_summary: dict[str, dict[str, Any]] = Field(default_factory=dict)
    auto_link_coverage: float = 0.0
    auto_link_accuracy: float = 0.0
    auto_resolution_coverage: float = 0.0
    created_entities: int = 0
    duplicate_creation_count: int = 0
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
    protocol: Literal["fixed", "sequential"] | None = None,
) -> EntityLinkingEvaluationReport:
    total_started = time.perf_counter()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entities = [CanonicalEntity.model_validate(item) for item in manifest["entities"]]
    selected_protocol = protocol or manifest.get("protocol", "fixed")
    if selected_protocol not in {"fixed", "sequential"}:
        raise ValueError("protocol must be fixed or sequential")
    mentions_payload = manifest["mentions"]
    if len({item["id"] for item in mentions_payload}) != len(mentions_payload):
        raise ValueError("duplicate mention IDs")
    if len({item.id for item in entities}) != len(entities):
        raise ValueError("duplicate entity IDs")
    types = sorted(
        {item.entity_type for item in entities} | {item["entity_type"] for item in mentions_payload}
    )
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
        reviews = false_auto_links = auto_links = 0
        link_cases = created_entities = duplicate_creations = 0
        # Ground-truth bookkeeping is used ONLY for scoring, never resolver input.
        identities: dict[str, str] = {entity.id: entity.id for entity in entities}
        initial_clusters = set(identities.values())
        created_clusters: set[str] = set()
        resolution_started = time.perf_counter()
        for payload in manifest["mentions"]:
            cluster = str(payload["cluster_id"])
            expected = payload.get("expected_entity_id")
            targets = (
                {entity_id for entity_id, identity in identities.items() if identity == cluster}
                if selected_protocol == "sequential"
                else ({expected} if expected is not None else set())
            )
            link_cases += bool(targets)
            mention = EntityMention(
                id=payload["id"],
                name=payload["name"],
                entity_type=payload["entity_type"],
                context=payload.get("context", ""),
                modality=payload.get("modality", "text"),
                evidence_ids=payload.get("evidence_ids", [f"evidence:{payload['id']}"]),
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
            if any("unavailable" in reason for reason in decision.reasons):
                raise RuntimeError(f"embedding/index unavailable at mention {mention.id}")
            ranked = [item.entity_id for item in decision.candidates]
            top_1 = (
                ranked[0]
                if ranked
                else (decision.selected_entity_id if decision.method == "exact" else None)
            )
            top_10_correct = bool(targets & set(ranked)) or (
                decision.method == "exact" and decision.selected_entity_id in targets
            )
            top_1_correct = bool(targets) and top_1 in targets
            if targets and top_10_correct:
                top_10_hits += 1
            if top_1_correct:
                top_1_hits += 1
            is_true_nil = not targets
            is_predicted_nil = decision.method == "nil"
            true_nil += int(is_true_nil)
            predicted_nil += int(is_predicted_nil)
            correct_nil += int(is_true_nil and is_predicted_nil)
            reviews += int(decision.requires_review)
            automatic_link = decision.method in {"exact", "vector"} and not decision.requires_review
            wrong_auto_link = automatic_link and decision.selected_entity_id not in targets
            auto_links += int(automatic_link)
            false_auto_links += int(wrong_auto_link)
            actual_cluster = cluster
            predicted_cluster = decision.selected_entity_id or f"unresolved:{mention.id}"
            actual_clusters.append(actual_cluster)
            predicted_clusters.append(predicted_cluster)
            details.append(
                {
                    "mention_id": mention.id,
                    "category": payload.get("category", "unspecified"),
                    "document_id": payload.get("document_id"),
                    "name": mention.name,
                    "entity_type": mention.entity_type,
                    "modality": mention.modality.value,
                    "gold_cluster_id": cluster,
                    "expected_entity_id": expected,
                    "expected_current_entity_ids": sorted(targets),
                    "expected_current_action": "create_new" if is_true_nil else "link_existing",
                    "predicted_entity_id": decision.selected_entity_id,
                    "method": decision.method,
                    "requires_review": decision.requires_review,
                    "ranked_entity_ids": ranked,
                    "candidates": [item.model_dump(mode="json") for item in decision.candidates],
                    "confidence": decision.confidence,
                    "margin": decision.margin,
                    "reasons": decision.reasons,
                    "evidence_ids": mention.evidence_ids,
                    "evidence": payload.get("evidence"),
                    "top_1_correct": top_1_correct if targets else None,
                    "top_10_correct": top_10_correct if targets else None,
                    "false_auto_link": wrong_auto_link,
                    "nil_correct": is_true_nil if is_predicted_nil else None,
                    "decision_correct": (
                        None
                        if decision.requires_review
                        else is_true_nil
                        if is_predicted_nil
                        else not wrong_auto_link
                    ),
                }
            )
            if selected_protocol == "sequential" and not decision.requires_review:
                selected = decision.selected_entity_id
                if selected is None:
                    raise ValueError("automatic resolution has no selected entity")
                resolved_entity = next(item for item in result.entities if item.id == selected)
                if selected not in identities:
                    created_entities += 1
                    duplicate_creations += int(cluster in initial_clusters | created_clusters)
                    created_clusters.add(cluster)
                    identities[selected] = cluster
                parent = await store.latest_revision()
                await store.commit(
                    GraphCommit(
                        entities=[resolved_entity],
                        revision=GraphRevision(
                            id=f"revision:entity-eval:{mention.id}",
                            run_id=f"eval:{mention.id}",
                            parent_id=parent.id if parent else None,
                            entity_ids=[selected],
                        ),
                    )
                )
                await rebuild_entity_index(
                    store,
                    provider,
                    backend="json",
                    batch_size=32,
                    dry_run=False,
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
    try:
        code_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        code_commit = "unknown"
    modality_summary = {}
    for modality in sorted({item["modality"] for item in details}):
        group = [item for item in details if item["modality"] == modality]
        known = [item for item in group if item["top_1_correct"] is not None]
        modality_summary[modality] = {
            "cases": len(group),
            "link_cases": len(known),
            "top_1_accuracy": sum(bool(item["top_1_correct"]) for item in known) / len(known)
            if known
            else None,
            "review_cases": sum(item["requires_review"] for item in group),
            "false_auto_links": sum(item["false_auto_link"] for item in group),
        }
    return EntityLinkingEvaluationReport(
        protocol=selected_protocol,
        provenance={
            **manifest.get("provenance", {}),
            "model_fingerprint": provider.fingerprint(),
            "entity_resolution_policy_version": ENTITY_RESOLUTION_POLICY_VERSION,
            "code_commit": code_commit,
            "top_k": top_k,
            "auto_link_threshold": auto_link_threshold,
            "review_threshold": review_threshold,
            "min_margin": min_margin,
            "graph_backend": "isolated_json",
            "api_calls": 0,
            "graph_neighborhood_coverage": "no_claim_neighborhoods",
            "vision_extraction_evaluated": False,
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "embedding_model": getattr(provider, "model_name", "mock"),
            "embedding_revision": getattr(provider, "model_revision", "mock"),
            "embedding_device": getattr(provider, "device", "cpu"),
        },
        denominators={
            "link_cases": link_cases,
            "true_nil": true_nil,
            "predicted_nil": predicted_nil,
            "correct_nil": correct_nil,
            "auto_links": auto_links,
            "false_auto_links": false_auto_links,
            "reviews": reviews,
            "top_1_hits": top_1_hits,
            "top_10_hits": top_10_hits,
        },
        modality_summary=modality_summary,
        auto_link_coverage=auto_links / count if count else 0.0,
        auto_link_accuracy=(auto_links - false_auto_links) / auto_links if auto_links else 0.0,
        auto_resolution_coverage=(auto_links + predicted_nil) / count if count else 0.0,
        created_entities=created_entities,
        duplicate_creation_count=duplicate_creations,
        cases=count,
        governance_cases=len(manifest.get("governance", [])),
        top_10_recall=top_10_hits / link_cases if link_cases else 0.0,
        top_1_accuracy=top_1_hits / link_cases if link_cases else 0.0,
        nil_precision=nil_precision,
        nil_recall=nil_recall,
        nil_f1=nil_f1,
        b_cubed_precision=bc_precision,
        b_cubed_recall=bc_recall,
        b_cubed_f1=bc_f1,
        review_rate=reviews / count if count else 0.0,
        false_auto_link_rate=false_auto_links / auto_links if auto_links else 0.0,
        index_build_seconds=index_build_seconds,
        resolution_seconds=resolution_seconds,
        total_seconds=time.perf_counter() - total_started,
        indexed_entities_per_second=(
            len(entities) / index_build_seconds if index_build_seconds else 0.0
        ),
        mean_resolution_ms=(resolution_seconds * 1000 / count if count else 0.0),
        details=details,
    )
