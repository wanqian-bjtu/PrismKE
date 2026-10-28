from __future__ import annotations

from pathlib import Path

import pytest

from src.core.settings import Settings
from src.domain import CanonicalEntity, TaskMode
from src.workflow import PrismKEService
from src.workflow.result_projection import (
    aggregate_entity_mentions,
    candidate_graph,
    mention_occurrences,
    run_insight,
)


@pytest.mark.asyncio
async def test_entity_projection_keeps_mentions_and_groups_same_names(
    tmp_path: Path, schema_path: Path
) -> None:
    source = tmp_path / "mentions.txt"
    source.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.95\n"
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.91\n",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        state = await service.run(
            source,
            schema_path,
            "mock",
            task_mode=TaskMode.ENTITY_EXTRACTION,
        )
        groups = aggregate_entity_mentions(state)
        mentions = mention_occurrences(state)
        graph = candidate_graph(state)
        insight = run_insight(state)

        assert state.extraction_result is not None
        assert len(mentions) == len(state.extraction_result.entities)
        assert len(groups) < len(mentions)
        assert all(item["grouping"] == "same_name_mentions" for item in groups)
        assert sum(item["occurrence_count"] for item in groups) == len(mentions)
        assert len(graph["nodes"]) == len(groups)
        assert graph["edges"] == []
        assert insight["task_mode_scope"] == "entities_only"
        assert insight["entity_mention_count"] == len(mentions)
        assert insight["aggregated_entity_count"] == len(groups)
        assert await service.graph_store.list_revisions() == []
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_entity_projection_prefers_canonical_entity_ids_after_resolution(
    tmp_path: Path, schema_path: Path
) -> None:
    source = tmp_path / "canonical-mentions.txt"
    source.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.95\n"
        "Prism KE | developed_by | OpenAI | Software | Organization | 0.91\n",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        state = await service.run(
            source,
            schema_path,
            "mock",
            task_mode=TaskMode.ENTITY_EXTRACTION,
        )
        assert state.extraction_result is not None
        software_mentions = [
            item
            for item in state.extraction_result.entities
            if item.entity_type == "Software"
        ]
        assert len(software_mentions) >= 2
        canonical = CanonicalEntity(
            id="entity:prismke",
            name="PrismKE",
            entity_type="Software",
            aliases=["Prism KE"],
            source_evidence_ids=list(
                dict.fromkeys(
                    evidence_id
                    for item in software_mentions
                    for evidence_id in item.evidence_ids
                )
            ),
        )
        state.extraction_result.canonical_entities = [canonical]
        state.extraction_result.mention_to_entity.update(
            {item.id: canonical.id for item in software_mentions}
        )

        groups = aggregate_entity_mentions(state)
        prismke_group = next(item for item in groups if item["group_id"] == canonical.id)

        assert prismke_group["canonical_entity_id"] == canonical.id
        assert prismke_group["grouping"] == "canonical_entity"
        assert prismke_group["occurrence_count"] == len(software_mentions)
        assert prismke_group["name"] == "PrismKE"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_research_pdf_insight_reports_pages_media_and_read_only_candidates(
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    source = repository_root / "data/synthetic/native/research-brief.pdf"
    schema = repository_root / "configs/schemas/research_documents.yaml"
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        state = await service.run(
            source,
            schema,
            "mock",
            task_mode=TaskMode.JOINT_ENTITY_RELATION_DISAMBIGUATION,
        )
        insight = run_insight(state)
        graph = candidate_graph(state)

        assert insight["page_count"] == 4
        assert insight["media_asset_count"] == 1
        assert insight["pdf_actual_parser"] == "pymupdf"
        assert insight["task_mode_scope"] == "entities_relations_and_disambiguation"
        assert graph["semantics"] == "candidate_only"
        assert await service.graph_store.list_revisions() == []
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_disambiguation_result_can_finish_after_invalid_candidates_are_excluded(
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    schema = repository_root / "configs/schemas/research_documents.yaml"
    source = tmp_path / "invalid-relations.txt"
    source.write_text(
        "Nebula Technology | developed_by | AtlasVision X1 | Organization | SoftwareSystem | 0.95\n"
        "AtlasVision X1 | evaluated_on | Harbor Laboratory | SoftwareSystem | "
        "Organization | 0.90\n",
        encoding="utf-8",
    )
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    try:
        state = await service.run(
            source,
            schema,
            "mock",
            task_mode=TaskMode.JOINT_ENTITY_RELATION_DISAMBIGUATION,
        )
        assert state.status == "awaiting_review"
        assert state.validation.blocking_count >= 2

        for issue in [item for item in state.validation.issues if item.status == "open"]:
            state = await service.exclude_validation_issue(
                state.run_id,
                issue.id,
                "tester",
                "synthetic candidate violates schema",
            )

        completed = await service.resume(state.run_id)
        assert completed.status == "completed"
        assert completed.extraction_result is not None
        assert completed.extraction_result.validation_issues
        assert all(
            item.status != "open"
            for item in completed.extraction_result.validation_issues
            if item.severity == "blocking"
        )
        assert await service.graph_store.list_revisions() == []
    finally:
        await service.close()
