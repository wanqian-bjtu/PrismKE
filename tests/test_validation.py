"""Unified quarantine and non-bypassable persistence boundary regression tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from test_store import versioned_transaction
from validated_fixtures import prepare_fixture_commit

from prismke.api import create_app
from prismke.core.errors import GraphIntegrityError, LegacyCheckpointError, ProviderResponseError
from prismke.core.ids import file_sha256
from prismke.core.settings import Settings
from prismke.domain import (
    BBox,
    EvidenceKind,
    EvidenceRef,
    GraphChange,
    GraphCommit,
    GraphRevision,
    Modality,
    ValidationResult,
)
from prismke.governance.validation import ValidationService
from prismke.persistence import JSONGraphStore, Neo4jGraphStore
from prismke.providers import MockLLMProvider, OpenAICompatibleLLMProvider
from prismke.providers.validation import summarize, validate_item
from prismke.workflow import PrismKEService


@pytest.mark.parametrize(
    "field,value",
    [
        ("subject", None),
        ("subject", ""),
        ("relation", []),
        ("object", {}),
        ("confidence", 1.2),
        ("confidence", "0.9"),
        ("confidence", True),
        ("confidence", float("nan")),
        ("qualifiers", []),
        ("evidence_ids", []),
        ("evidence_ids", [None]),
    ],
)
def test_per_item_structure_errors_preserve_safe_summary(field: str, value: object) -> None:
    item = {
        "subject": "PrismKE",
        "subject_type": "Software",
        "relation": "developed_by",
        "object": "OpenAI",
        "confidence": 0.9,
        "authorization": "secret",
    }
    item[field] = value
    issue = validate_item(item, "document:test", 1)
    assert issue is not None and issue.allowed_actions == ["exclude"]
    assert "authorization" not in issue.candidate_summary
    assert issue.id == validate_item(item, "document:test", 1).id


def test_summary_never_records_secrets_or_image_payload() -> None:
    assert (
        summarize(
            {
                "subject": "sk-secret",
                "object": "data:image/png;base64,secret",
                "Authorization": "Bearer secret",
            }
        )
        == {}
    )
    assert validate_item([], "document", 0) is not None


@pytest.mark.asyncio
async def test_direct_commit_requires_schema_and_real_evidence(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="MISSING_SCHEMA_CONTEXT"):
        await store.commit(transaction)
    assert store.path.read_bytes() == before
    await prepare_fixture_commit(store, transaction)
    await store.commit(transaction)
    assert (await store.latest_revision()).validation_context is not None
    # Even the already previewed transaction must reverify the current blob.
    next_commit = transaction.model_copy(deep=True)
    next_commit.revision.id = "revision:damaged"
    next_commit.revision.parent_id = transaction.revision.id
    store.evidence_store._blob_path(transaction.evidence[0].source_hash).write_bytes(b"tampered")
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="CORRUPT_EVIDENCE"):
        await store.commit(next_commit)
    assert store.path.read_bytes() == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutation,code",
    [
        ("relation", "UNKNOWN_RELATION"),
        ("schema", "MISSING_SCHEMA_CONTEXT"),
        ("evidence", "UNKNOWN_EVIDENCE"),
        ("entity", "MISSING_ENTITY_REFERENCE"),
    ],
)
async def test_direct_commit_rejects_invalid_final_state(
    tmp_path: Path, mutation: str, code: str
) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    await prepare_fixture_commit(store, transaction)
    if mutation == "relation":
        transaction.claims[0].relation_id = "undeclared"
    elif mutation == "schema":
        transaction.validation_context.claim_schema_ids.clear()
    elif mutation == "evidence":
        transaction.claims[0].evidence_ids = ["unknown"]
    else:
        transaction.entities[0].active = False
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match=code):
        await store.commit(transaction)
    assert store.path.read_bytes() == before


class MixedProvider(MockLLMProvider):
    def fingerprint(self) -> str:
        return "mock:mixed-validation"

    async def extract(self, request: object) -> object:
        result = await super().extract(request)
        invalid = result.candidates[0].model_copy(deep=True)
        invalid.id = "candidate:invalid-relation"
        invalid.relation = "undeclared"
        result.candidates.append(invalid)
        return result


async def mixed_run(
    tmp_path: Path, schema_path: Path, graph_store: object = None
) -> tuple[PrismKEService, object]:
    source = tmp_path / "document.md"
    source.write_text(
        f"ValidationDemo-{tmp_path.parent.name}-{tmp_path.name} | developed_by | OpenAI"
        " | Software | Organization | 0.95",
        encoding="utf-8",
    )
    service = PrismKEService(
        Settings(_env_file=None, runtime_dir=tmp_path / "runtime"), graph_store=graph_store
    )
    state, _ = service.create_run(source, schema_path, "mock")
    workflow = service._workflow(
        MixedProvider(), service.ocr_provider("disabled"), service.vlm_provider("disabled"), False
    )
    return service, await workflow.invoke(state)


@pytest.mark.asyncio
@pytest.mark.parametrize("backend", ["json", "neo4j"])
async def test_quarantine_exclusion_and_continuation_without_model_calls(
    tmp_path: Path, schema_path: Path, backend: str
) -> None:
    store = None
    if backend == "neo4j":
        if os.getenv("PRISMKE_TEST_NEO4J") != "1":
            pytest.skip("requires dedicated Neo4j test instance")
        settings = Settings()
        assert settings.neo4j_uri == "bolt://127.0.0.1:17687"
        store = Neo4jGraphStore(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password or "test",
            settings.neo4j_database,
        )
    service, state = await mixed_run(tmp_path, schema_path, store)
    initial_claim_count = len(await service.graph_store.list_claims())
    assert state.status == "awaiting_review"
    assert len(state.candidates) == 2
    assert state.validation.blocking_count == 1
    with pytest.raises(ValueError):
        await service.resume(state.run_id)
    issue = state.validation.issues[0]
    before = file_sha256(service.runs._target(state.run_id))
    report = await service.validate_run(state.run_id)
    assert report.blocking_count == 1
    assert file_sha256(service.runs._target(state.run_id)) == before
    await service.exclude_validation_issue(state.run_id, issue.id, "tester", "exclude invalid")
    with pytest.raises(ValueError):
        await service.exclude_validation_issue(state.run_id, issue.id, "tester")
    completed = await service.resume(state.run_id)
    assert completed.status == "completed"
    assert len(completed.claims) == 1
    assert len(completed.validation_decisions) == 1
    assert len(await service.graph_store.list_claims()) == initial_claim_count + 1
    assert completed.validation.issues[0].status == "excluded"
    assert completed.review_tasks == []
    await service.graph_store.rollback_revision(completed.revision.id)
    await service.close()


def test_validation_api_auth_exclusion_and_conflict(tmp_path: Path, schema_path: Path) -> None:
    import asyncio

    service, state = asyncio.run(mixed_run(tmp_path, schema_path))
    settings = service.settings.model_copy(update={"api_token": "test-api-token"})
    issue_id = state.validation.issues[0].id
    with TestClient(create_app(settings, service, mount_ui=False)) as client:
        url = f"/api/v1/runs/{state.run_id}/validation"
        assert client.get(url).status_code == 401
        headers = {"Authorization": "Bearer test-api-token"}
        assert client.get(url, headers=headers).json()["blocking_count"] == 1
        exclude = f"/api/v1/runs/{state.run_id}/validation-issues/{issue_id}/exclude"
        assert client.post(exclude, json={"reviewer": ""}, headers=headers).status_code == 422
        assert client.post(exclude, json={"reviewer": "tester"}, headers=headers).status_code == 200
        assert client.post(exclude, json={"reviewer": "tester"}, headers=headers).status_code == 409


@pytest.mark.asyncio
async def test_legacy_resume_is_rejected_without_extraction(
    tmp_path: Path, schema_path: Path
) -> None:
    service, state = await mixed_run(tmp_path, schema_path)
    state.pipeline_version = "0.4.0"
    service.runs.save(state)
    with pytest.raises(LegacyCheckpointError):
        await service.resume(state.run_id)


@pytest.mark.asyncio
async def test_permissive_schema_does_not_allow_unknown_relation(
    tmp_path: Path, schema_path: Path
) -> None:
    schema_path.write_text(
        schema_path.read_text(encoding="utf-8").replace("strict: true", "strict: false"),
        encoding="utf-8",
    )
    service, state = await mixed_run(tmp_path, schema_path)
    assert state.validation.blocking_count == 1
    assert state.validation.issues[0].code == "UNKNOWN_RELATION"
    assert not await service.graph_store.list_claims()


@pytest.mark.asyncio
async def test_same_revision_different_transaction_cannot_be_noop(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    await prepare_fixture_commit(store, transaction)
    await store.commit(transaction)
    changed = transaction.model_copy(deep=True)
    changed.claims[0].object_literal = "changed"
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="different content"):
        await store.commit(changed)
    assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "update",
    [
        {"char_start": 0},
        {"char_start": -1, "char_end": 3},
        {"char_start": 3, "char_end": 2},
        {"page_number": 0},
        {"bbox": BBox(x0=0, y0=0, x1=10, y1=10)},
        {
            "bbox": BBox(x0=0, y0=0, x1=101, y1=10),
            "coordinate_space": "image_pixels",
            "canvas_width": 100,
            "canvas_height": 100,
        },
        {
            "bbox": BBox(x0=-0.1, y0=0, x1=0.5, y1=0.5),
            "coordinate_space": "normalized",
            "canvas_width": 100,
            "canvas_height": 100,
        },
    ],
)
def test_evidence_location_boundaries(update: dict[str, object]) -> None:
    ref = EvidenceRef(
        id="ev:location",
        kind=EvidenceKind.TEXT_SPAN,
        document_id="document:test",
        source_hash="a" * 64,
        modality=Modality.TEXT,
    )
    assert ValidationService.location_error(ref.model_copy(update=update)) is not None


@pytest.mark.asyncio
async def test_unavailable_evidence_store_is_not_an_excludable_candidate(
    tmp_path: Path, schema_path: Path
) -> None:
    service, state = await mixed_run(tmp_path, schema_path)
    service.evidence_store.blobs_dir.rename(tmp_path / "offline-blobs")
    with pytest.raises(OSError):
        await service.validate_run(state.run_id)


def test_validation_report_merge_preserves_audit_status() -> None:
    issue = ValidationService.issue(
        "UNKNOWN_RELATION", "schema", "candidate", "c1", "relation", "未知关系"
    )
    previous = ValidationResult(issues=[issue], blocking_count=1)
    issue.status = "excluded"
    result = ValidationService.merge(previous, [issue.model_copy(update={"status": "open"})])
    assert result.blocking_count == 0 and len(result.issues) == 1
    assert result.issues[0].status == "excluded"


@pytest.mark.asyncio
async def test_entity_type_update_cannot_bypass_existing_claim_validation(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    await prepare_fixture_commit(store, transaction)
    await store.commit(transaction)
    updated = transaction.entities[0].model_copy(update={"entity_type": "Undeclared"})
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="UNKNOWN_ENTITY_TYPE"):
        await store.commit(
            GraphCommit(
                entities=[updated],
                revision=GraphRevision(
                    id="revision:type-change",
                    run_id="type-change",
                    parent_id=transaction.revision.id,
                ),
            )
        )
    assert store.path.read_bytes() == before


@pytest.mark.asyncio
async def test_only_closing_legacy_claim_does_not_require_schema(tmp_path: Path) -> None:
    from prismke.domain import utc_now

    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    await prepare_fixture_commit(store, transaction)
    await store.commit(transaction)
    closing = transaction.claims[0].model_copy(update={"tx_to": utc_now()})
    await store.commit(
        GraphCommit(
            claims=[closing],
            revision=GraphRevision(
                id="revision:close", run_id="close", parent_id=transaction.revision.id
            ),
        )
    )
    assert (await store.get_claim(closing.id)).tx_to is not None


@pytest.mark.asyncio
async def test_entity_only_rollback_revalidates_later_active_claims(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    entity = transaction.entities[0]
    original = entity.model_copy(update={"entity_type": "Undeclared"})
    await store.commit(
        GraphCommit(
            entities=[original], revision=GraphRevision(id="rev:original", run_id="original")
        )
    )
    await store.commit(
        GraphCommit(
            entities=[entity],
            revision=GraphRevision(
                id="rev:entity-only",
                run_id="entity-only",
                parent_id="rev:original",
                entity_ids=[entity.id],
                changes=[
                    GraphChange(
                        resource_type="entity",
                        resource_id=entity.id,
                        action="update",
                        before=original.model_dump(mode="json"),
                        after=entity.model_dump(mode="json"),
                    )
                ],
            ),
        )
    )
    transaction.revision.parent_id = "rev:entity-only"
    await prepare_fixture_commit(store, transaction)
    await store.commit(transaction)
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="UNKNOWN_ENTITY_TYPE"):
        await store.rollback_revision("rev:entity-only")
    assert store.path.read_bytes() == before


@pytest.mark.asyncio
async def test_unsupported_validation_policy_is_not_silently_replaced(tmp_path: Path) -> None:
    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    await prepare_fixture_commit(store, transaction)
    transaction.validation_context.policy_version = "unsupported"
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="MISSING_SCHEMA_CONTEXT"):
        await store.commit(transaction)
    assert store.path.read_bytes() == before


@pytest.mark.asyncio
async def test_readonly_validation_checks_claims_not_only_candidates(
    tmp_path: Path, schema_path: Path
) -> None:
    service, state = await mixed_run(tmp_path, schema_path)
    await service.exclude_validation_issue(state.run_id, state.validation.issues[0].id, "tester")
    state = await service.resume(state.run_id)
    state.claims[0].relation_id = "undeclared"
    service.runs.save(state)
    before = file_sha256(service.runs._target(state.run_id))
    report = await service.validate_run(state.run_id)
    assert any(i.code == "UNKNOWN_RELATION" and i.target_type == "claim" for i in report.issues)
    assert all(not i.allowed_actions for i in report.issues if i.target_type == "claim")
    assert file_sha256(service.runs._target(state.run_id)) == before


@pytest.mark.asyncio
async def test_literal_cannot_bypass_declared_entity_range(tmp_path: Path) -> None:
    from prismke.core.ids import canonical_hash

    store = JSONGraphStore(tmp_path / "graph")
    transaction = versioned_transaction()
    await prepare_fixture_commit(store, transaction)
    context = transaction.validation_context
    schema = next(iter(context.schemas.values())).model_copy(deep=True)
    next(r for r in schema.relations if r.id == "version").range = ["Software"]
    sid = canonical_hash(schema.model_dump(mode="json"))
    context.schemas = {sid: schema}
    context.claim_schema_ids = {transaction.claims[0].id: sid}
    before = store.path.read_bytes()
    with pytest.raises(GraphIntegrityError, match="SCHEMA_DOMAIN_RANGE"):
        await store.commit(transaction)
    assert store.path.read_bytes() == before


@pytest.mark.asyncio
async def test_provider_mixed_items_and_whole_batch_failure(
    tmp_path: Path, schema_path: Path
) -> None:
    from prismke.domain import ExtractionRequest, SourceDocument, load_schema
    from prismke.parsing import ParserRegistry

    source = tmp_path / "text.md"
    source.write_text("PrismKE developed by OpenAI", encoding="utf-8")
    document = await ParserRegistry().parse(SourceDocument(path=source))
    valid = {
        "subject": "PrismKE",
        "subject_type": "Software",
        "relation": "developed_by",
        "object": "OpenAI",
        "object_type": "Organization",
        "confidence": 0.95,
        "evidence_id": document.evidence[0].id,
    }
    payload = {
        "claims": [valid, None, {**valid, "confidence": "bad"}, {**valid, "evidence_id": "unknown"}]
    }

    def response(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(payload)}}]}
        )

    provider = OpenAICompatibleLLMProvider(
        "https://example.test/v1", "secret", "test", transport=httpx.MockTransport(response)
    )
    result = await provider.extract(
        ExtractionRequest(document=document, schema=load_schema(schema_path))
    )
    assert len(result.candidates) == 1 and result.validation.blocking_count == 3
    payload["claims"] = "invalid whole batch"
    with pytest.raises(ProviderResponseError):
        await provider.extract(
            ExtractionRequest(document=document, schema=load_schema(schema_path))
        )
