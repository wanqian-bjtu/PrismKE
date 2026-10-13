from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.api import create_app
from src.core.errors import EvidenceIntegrityError, GraphIntegrityError
from src.core.settings import Settings
from src.domain import (
    AttributeDef,
    CandidateAttribute,
    CandidateMediaRelation,
    CanonicalEntity,
    DocumentIR,
    EntityMention,
    EntityTypeDef,
    GraphChange,
    GraphCommit,
    GraphDocument,
    GraphMediaContent,
    GraphMediaOccurrence,
    GraphMediaRelation,
    GraphRevision,
    MediaKnowledgeType,
    MediaRelationType,
    Modality,
    OutputSchema,
    SourceDocument,
    TaskMode,
    VisualObservation,
    VisualReviewEvent,
    VisualReviewTask,
    WorkflowState,
)
from src.governance.media import MediaKnowledgeProjector
from src.parsing import ParserRegistry
from src.persistence import FileEvidenceStore, JSONGraphStore
from src.workflow import PrismKEService


async def _image_fixture(tmp_path: Path) -> tuple[FileEvidenceStore, DocumentIR]:
    source = tmp_path / "product.png"
    Image.new("RGB", (120, 80), "white").save(source)
    document = await ParserRegistry(asset_dir=tmp_path / "assets").parse(
        SourceDocument(path=source)
    )
    evidence_store = FileEvidenceStore(tmp_path / "evidence")
    await evidence_store.put_document(document)
    return evidence_store, document


def _media_commit(document: DocumentIR, *, decision: str = "approve") -> GraphCommit:
    parsed = document
    asset = parsed.media_assets[0]
    evidence = next(item for item in parsed.evidence if item.id == asset.evidence_id)
    assert asset.blob_hash is not None
    content = GraphMediaContent(
        id="media-content:product",
        content_hash=asset.blob_hash,
        blob_hash=asset.blob_hash,
        media_type=asset.media_type,
        asset_type=MediaKnowledgeType.IMAGE,
        width=asset.width,
        height=asset.height,
    )
    occurrence = GraphMediaOccurrence(
        id="media-occurrence:product",
        document_id=parsed.id,
        media_content_id=content.id,
        evidence_id=evidence.id,
        page_number=evidence.page_number,
        bbox=evidence.bbox,
        canvas_width=evidence.canvas_width or float(asset.width or 120),
        canvas_height=evidence.canvas_height or float(asset.height or 80),
        source_type=asset.origin,
    )
    entity = CanonicalEntity(id="entity:product", name="PrismKE", entity_type="Product")
    event = VisualReviewEvent(
        id="visual-event:product",
        request_id="request:product",
        run_id="run:media",
        task_id="task:product",
        target_type="media_relation",
        target_id="candidate:depicts",
        decision=decision,
        reviewer="管理员",
        reason="区域证据与实体候选一致",
        expected_version=0,
        resulting_version=1,
    )
    relation = GraphMediaRelation(
        id="media-relation:product",
        occurrence_id=occurrence.id,
        relation_type=MediaRelationType.DEPICTS,
        target_entity_id=entity.id,
        evidence_ids=[evidence.id],
        source_candidate_id="candidate:depicts",
        approved_review_event_id=event.id,
    )
    changes = [
        GraphChange(
            resource_type="media_content",
            resource_id=content.id,
            action="create",
            after=content.model_dump(mode="json"),
        ),
        GraphChange(
            resource_type="media_occurrence",
            resource_id=occurrence.id,
            action="create",
            after=occurrence.model_dump(mode="json"),
        ),
        GraphChange(
            resource_type="media_relation",
            resource_id=relation.id,
            action="create",
            after=relation.model_dump(mode="json"),
        ),
    ]
    return GraphCommit(
        documents=[
            GraphDocument(
                id=parsed.id,
                filename=parsed.source_filename or "product.png",
                content_hash=parsed.source_hash,
                media_type=parsed.media_type,
            )
        ],
        evidence=[evidence],
        entities=[entity],
        media_contents=[content],
        media_occurrences=[occurrence],
        media_relations=[relation],
        visual_review_events=[event],
        revision=GraphRevision(
            id="revision:media",
            run_id="run:media",
            entity_ids=[entity.id],
            media_content_ids=[content.id],
            media_occurrence_ids=[occurrence.id],
            media_relation_ids=[relation.id],
            changes=changes,
        ),
    )


@pytest.mark.asyncio
async def test_media_commit_is_queryable_and_evidence_verified(tmp_path: Path) -> None:
    evidence_store, document = await _image_fixture(tmp_path)
    store = JSONGraphStore(tmp_path / "graph", evidence_store=evidence_store)
    commit = _media_commit(document)
    await store.commit(commit)

    assert len(await store.list_media_contents()) == 1
    assert await store.get_media_occurrence("media-occurrence:product") is not None
    assert [item.id for item in await store.list_media_relations()] == [
        "media-relation:product"
    ]
    assert await evidence_store.verify(commit.media_occurrences[0].evidence_id)


@pytest.mark.asyncio
async def test_projector_separates_media_content_occurrence_and_semantic_entity(
    tmp_path: Path,
) -> None:
    _, document = await _image_fixture(tmp_path)
    asset = document.media_assets[0]
    region_evidence = document.evidence[0].model_copy(update={"id": "evidence:product-region"})
    document.evidence.append(region_evidence)
    document.visual_observations = [
        VisualObservation(
            id="observation:product",
            media_asset_id=asset.id,
            label="PrismKE product",
            confidence=0.88,
            evidence_id=region_evidence.id,
            attributes={"component_count": 3, "left_of": "logo"},
        )
    ]
    mention = EntityMention(
        id="mention:product",
        name="PrismKE",
        entity_type="Product",
        modality=Modality.IMAGE,
        evidence_ids=[asset.evidence_id],
        confidence=0.91,
    )
    text_mention = mention.model_copy(
        update={
            "id": "mention:product:text",
            "modality": Modality.TEXT,
            "evidence_ids": ["evidence:text"],
        }
    )
    state = WorkflowState(
        run_id="run:projector",
        input_path=document.source_path,
        schema_path="schema.yaml",
        document=document,
        extracted_entities=[mention, text_mention],
        candidate_attributes=[
            CandidateAttribute(
                id="attribute:text-count",
                subject=text_mention,
                field="component_count",
                value=4,
                confidence=0.9,
                evidence_ids=["evidence:text"],
            )
        ],
        entities=[CanonicalEntity(id="entity:product", name="PrismKE", entity_type="Product")],
        mention_to_entity={
            mention.id: "entity:product",
            text_mention.id: "entity:product",
        },
        schema=OutputSchema(
            schema_id="media-schema",
            version="1",
            entity_types=[EntityTypeDef(id="Product")],
            relations=[],
            attributes=[
                AttributeDef(
                    id="component_count",
                    subject_types=["Product"],
                    value_type="integer",
                ),
                AttributeDef(id="left_of", subject_types=["Product"], value_type="string"),
            ],
        ),
    )

    projected = MediaKnowledgeProjector().project(state)

    assert len(projected.media_contents) == 1
    assert len(projected.media_occurrences) == 1
    assert projected.candidate_media_relations[0].target_entity_id == "entity:product"
    assert projected.candidate_media_relations[0].relation_type is MediaRelationType.DEPICTS
    assertion_kinds = {
        item.predicate: item.assertion_kind.value
        for item in projected.candidate_visual_assertions
    }
    assert assertion_kinds == {
        "component_count": "count",
        "left_of": "spatial_relation",
    }
    assert projected.visual_review_tasks[0].status == "pending"
    count_task = next(
        item
        for item in projected.visual_review_tasks
        if item.target_id
        == next(
            assertion.id
            for assertion in projected.candidate_visual_assertions
            if assertion.predicate == "component_count"
        )
    )
    assert "cross_modal_attribute_conflict" in count_task.reasons
    assert projected.status == "awaiting_review"


@pytest.mark.asyncio
async def test_visual_relation_requires_matching_approval_event(tmp_path: Path) -> None:
    evidence_store, document = await _image_fixture(tmp_path)
    store = JSONGraphStore(tmp_path / "graph", evidence_store=evidence_store)
    rejected = _media_commit(document, decision="reject")

    with pytest.raises(GraphIntegrityError, match="does not approve relation"):
        await store.commit(rejected)
    assert await store.latest_revision() is None
    assert await store.list_media_occurrences() == []


@pytest.mark.asyncio
async def test_tampered_media_blob_blocks_atomic_commit(tmp_path: Path) -> None:
    evidence_store, document = await _image_fixture(tmp_path)
    commit = _media_commit(document)
    blob = evidence_store._blob_path(commit.media_contents[0].blob_hash)
    blob.write_bytes(b"tampered")
    store = JSONGraphStore(tmp_path / "graph", evidence_store=evidence_store)

    with pytest.raises(
        (EvidenceIntegrityError, GraphIntegrityError, OSError),
        match="hash|checksum|corrupt",
    ):
        await store.commit(commit)
    assert await store.latest_revision() is None


@pytest.mark.asyncio
async def test_shared_media_content_survives_compensating_rollback(tmp_path: Path) -> None:
    evidence_store, document = await _image_fixture(tmp_path)
    store = JSONGraphStore(tmp_path / "graph", evidence_store=evidence_store)
    first = _media_commit(document)
    await store.commit(first)

    second_occurrence = first.media_occurrences[0].model_copy(
        update={"id": "media-occurrence:second"}
    )
    second = GraphCommit(
        media_occurrences=[second_occurrence],
        revision=GraphRevision(
            id="revision:second",
            run_id="run:second",
            parent_id=first.revision.id,
            media_occurrence_ids=[second_occurrence.id],
            changes=[
                GraphChange(
                    resource_type="media_occurrence",
                    resource_id=second_occurrence.id,
                    action="create",
                    after=second_occurrence.model_dump(mode="json"),
                )
            ],
        ),
    )
    await store.commit(second)
    compensation = await store.rollback_revision(first.revision.id)

    occurrences = {item.id: item for item in await store.list_media_occurrences()}
    assert not occurrences["media-occurrence:product"].active
    assert occurrences["media-occurrence:second"].active
    assert len(await store.list_media_contents()) == 1
    assert compensation.media_occurrence_ids == ["media-occurrence:product"]


@pytest.mark.asyncio
async def test_visual_review_is_idempotent_and_version_guarded(tmp_path: Path) -> None:
    service = PrismKEService(Settings(_env_file=None, runtime_dir=tmp_path / "runtime"))
    candidate = CandidateMediaRelation(
        id="candidate:depicts",
        occurrence_id="media-occurrence:product",
        relation_type=MediaRelationType.DEPICTS,
        target_entity_id="entity:product",
        evidence_ids=["evidence:product"],
        confidence=0.9,
    )
    task = VisualReviewTask(
        id="visual-task:product",
        run_id="run:visual-review",
        target_type="media_relation",
        target_id=candidate.id,
        reasons=["visual_only_knowledge_requires_human_review"],
    )
    state = WorkflowState(
        run_id=task.run_id,
        input_path="product.png",
        schema_path="schema.yaml",
        task_mode=TaskMode.ENTITY_EXTRACTION,
        candidate_media_relations=[candidate],
        visual_review_tasks=[task],
        status="awaiting_review",
    )
    service.runs.save(state)

    first = await service.review_visual(
        state.run_id,
        task.id,
        "approve",
        "管理员",
        "区域证据已核验",
        "request:visual",
        0,
    )
    replay = await service.review_visual(
        state.run_id,
        task.id,
        "approve",
        "管理员",
        "区域证据已核验",
        "request:visual",
        0,
    )
    assert first.visual_review_events == replay.visual_review_events
    assert len(replay.visual_review_events) == 1
    assert replay.visual_review_tasks[0].status == "resolved"
    assert replay.media_relations[0].source_candidate_id == candidate.id

    with pytest.raises(ValueError, match="REQUEST_CONFLICT"):
        await service.review_visual(
            state.run_id,
            task.id,
            "reject",
            "管理员",
            "冲突决定",
            "request:visual",
            0,
        )


def test_visual_review_api_exposes_no_blob_or_server_path(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, runtime_dir=tmp_path / "runtime")
    service = PrismKEService(settings)
    candidate = CandidateMediaRelation(
        id="candidate:api",
        occurrence_id="media-occurrence:api",
        relation_type=MediaRelationType.DEPICTS,
        target_entity_id="entity:api",
        evidence_ids=["evidence:api"],
        confidence=0.8,
    )
    task = VisualReviewTask(
        id="visual-task:api",
        run_id="run:api",
        target_type="media_relation",
        target_id=candidate.id,
        reasons=["visual_only_knowledge_requires_human_review"],
    )
    service.runs.save(
        WorkflowState(
            run_id="run:api",
            input_path="product.png",
            schema_path="schema.yaml",
            task_mode=TaskMode.ENTITY_EXTRACTION,
            candidate_media_relations=[candidate],
            visual_review_tasks=[task],
            status="awaiting_review",
        )
    )
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        listing = client.get("/api/v1/runs/run:api/visual-reviews")
        assert listing.status_code == 200
        response = client.post(
            "/api/v1/runs/run:api/visual-reviews/visual-task:api/decision",
            json={
                "decision": "approve",
                "reviewer": "管理员",
                "reason": "证据一致",
                "request_id": "request:api",
                "expected_version": 0,
            },
        )
    assert response.status_code == 200
    assert response.json()["visual_review_tasks"][0]["status"] == "resolved"
    assert "base64" not in listing.text.casefold()
    assert str(tmp_path).casefold() not in listing.text.casefold()
