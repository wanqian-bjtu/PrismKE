"""Verified, offline-only copies of completed extraction checkpoints."""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import orjson
from filelock import FileLock

from src.core.ids import canonical_hash, file_sha256
from src.domain import CanonicalEntity, Claim, EvidenceRef, WorkflowState
from src.persistence import FileEvidenceStore, JSONGraphStore, RunRepository
from src.persistence.checkpoints import open_checkpointer
from src.providers import DisabledEmbeddingProvider, DisabledOCRProvider, DisabledVLMProvider
from src.providers.mock import MockLLMProvider
from src.workflow.graph import PrismKEWorkflow

MARKER = "review-workspace.json"


def workspace_metadata(directory: Path) -> dict[str, Any] | None:
    path = directory / MARKER
    return dict(orjson.loads(path.read_bytes())) if path.is_file() else None


def validate_workspace_run(directory: Path, state: WorkflowState) -> None:
    metadata = workspace_metadata(directory)
    if metadata is None or not state.review_workspace or metadata["run_id"] != state.run_id:
        raise ValueError("run is not a verified isolated review import")
    if provenance(state) != metadata["provenance"]:
        raise ValueError("imported run provenance changed; refusing continuation")


def provenance(state: WorkflowState) -> dict[str, Any]:
    return {
        "pipeline": state.pipeline_version,
        "entity_policy": state.entity_resolution_policy_version,
        "llm": state.provider_fingerprint,
        "vlm": state.vlm_provider_fingerprint,
        "ocr": state.ocr_provider_fingerprint,
        "embedding": state.embedding_provider_fingerprint,
        "document_hash": state.document.source_hash if state.document else None,
        "schema_hash": canonical_hash(state.output_schema.model_dump(mode="json"))
        if state.output_schema
        else None,
    }


async def import_review_run(source: Path, run_id: str, target: Path) -> WorkflowState:
    source, target = source.resolve(), target.resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("source and target workspaces must be separate")
    if target.exists():
        raise ValueError("target workspace already exists; refusing overwrite")
    if not (source / "runs").is_dir() or not (source / "evidence" / "refs").is_dir():
        raise ValueError("source run and evidence directories are required")
    original = RunRepository(source / "runs").load(run_id)
    from src.governance.entity_resolution import ENTITY_RESOLUTION_POLICY_VERSION
    from src.workflow.service import PIPELINE_VERSION

    if (
        original.pipeline_version != PIPELINE_VERSION
        or original.entity_resolution_policy_version != ENTITY_RESOLUTION_POLICY_VERSION
    ):
        raise ValueError("run pipeline or entity policy is incompatible")
    if original.status != "awaiting_review" or original.current_node not in {
        "resolve_entities",
        "route_by_risk",
    }:
        raise ValueError("only a completed extraction paused for review can be imported")
    if original.document is None or original.output_schema is None:
        raise ValueError("document and schema are required")
    if any(
        not value or value == "legacy"
        for value in (
            original.provider_fingerprint,
            original.vlm_provider_fingerprint,
            original.ocr_provider_fingerprint,
            original.embedding_provider_fingerprint,
        )
    ):
        raise ValueError("provider provenance is incomplete")
    refs = {item.id: item for item in original.document.evidence}
    if len(refs) != len(original.document.evidence):
        raise ValueError("duplicate evidence IDs in document")
    evidence = FileEvidenceStore(source / "evidence")
    for ref in refs.values():
        if not await evidence.verify(ref.id) or await evidence.get(ref.id) != ref:
            raise ValueError(f"invalid source evidence: {ref.id}")
    for candidate in original.candidates:
        if not candidate.evidence_ids or not set(candidate.evidence_ids) <= refs.keys():
            raise ValueError(f"candidate has unknown evidence: {candidate.id}")
    from src.evaluation.document_review import document_coverage

    if document_coverage(original.model_dump(mode="json"))["invalid_bbox_ids"]:
        raise ValueError("document evidence contains invalid bounding boxes")
    graph_path = source / "graph" / "graph.json"
    with FileLock(str(graph_path.parent / "graph.lock")):
        graph_bytes = graph_path.read_bytes()
    graph = orjson.loads(graph_bytes)
    entity_ids = set(graph["entities"]) | {item.id for item in original.entities}
    for item in graph["entities"].values():
        CanonicalEntity.model_validate(item)
    for item in graph["evidence"].values():
        ref = EvidenceRef.model_validate(item)
        if not await evidence.verify(ref.id):
            raise ValueError(f"invalid graph evidence: {ref.id}")
    for item in graph["claims"].values():
        claim = Claim.model_validate(item)
        if (
            claim.subject_id not in entity_ids
            or (claim.object_entity_id and claim.object_entity_id not in entity_ids)
            or not set(claim.evidence_ids) <= graph["evidence"].keys()
        ):
            raise ValueError(f"invalid graph claim references: {claim.id}")
    for item in graph["conflicts"].values():
        if not set(item["claim_ids"]) <= graph["claims"].keys():
            raise ValueError("graph conflict references unknown claims")
    for task in original.entity_review_tasks:
        if not {item.entity_id for item in task.candidates} <= entity_ids:
            raise ValueError(f"review task references unknown candidate entities: {task.id}")
    if any(value not in entity_ids for value in original.mention_to_entity.values()):
        raise ValueError("run references unknown canonical entities")
    # SQLite backup includes committed WAL data without touching the source database.
    target.mkdir(parents=True)
    try:
        checkpoint = target / "checkpoints.sqlite3"
        with (
            closing(
                sqlite3.connect(f"{(source / 'checkpoints.sqlite3').as_uri()}?mode=ro", uri=True)
            ) as src,
            closing(sqlite3.connect(checkpoint)) as dst,
        ):
            src.backup(dst)
        shutil.copytree(source / "evidence", target / "evidence")
        from src.persistence.reviews import ReviewRepository

        source_reviews = source / "reviews.sqlite"
        if not source_reviews.is_file():
            raise ValueError("v0.6 candidate archive and review ledger are required")
        destination_reviews = ReviewRepository(target / "reviews.sqlite")
        with closing(sqlite3.connect(f"{source_reviews.as_uri()}?mode=ro", uri=True)) as src:
            src.execute("BEGIN")
            versions = dict(
                src.execute("SELECT task_id,version FROM versions WHERE run_id=?", (run_id,))
            )
            if any(
                versions.get(task.id, 0) != task.version for task in original.entity_review_tasks
            ) or any(versions.get(task.id, 0) != task.version for task in original.review_tasks):
                raise ValueError("source task versions and summary disagree; recover before import")
            if src.execute(
                "SELECT 1 FROM events e JOIN outbox o ON o.event_id=e.id "
                "WHERE e.run_id=? AND o.delivered=0",
                (run_id,),
            ).fetchone():
                raise ValueError("source review projection pending; recover before import")
            with closing(destination_reviews.connect()) as dst, dst:
                for table, condition in (
                    ("archives", "run_id=?"),
                    ("events", "run_id=?"),
                    ("versions", "run_id=?"),
                    ("outbox", "event_id IN (SELECT id FROM events WHERE run_id=?)"),
                ):
                    rows = src.execute(f"SELECT * FROM {table} WHERE {condition}", (run_id,))
                    for row in rows:
                        placeholders = ",".join("?" for _ in row)
                        dst.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
        (target / "graph").mkdir()
        (target / "graph" / "graph.json").write_bytes(graph_bytes)
        state = original.model_copy(deep=True)
        assert state.document is not None and state.output_schema is not None
        copied_evidence = FileEvidenceStore(target / "evidence")
        for ref in refs.values():
            if not await copied_evidence.verify(ref.id):
                raise ValueError(f"copied evidence failed verification: {ref.id}")
        state.review_workspace = True
        state.submission_confirmed = False
        state.document.source_filename = (
            original.document.source_filename or Path(original.document.source_path).name
        )
        state.document.source_path = str(copied_evidence._blob_path(state.document.source_hash))
        state.input_path = state.document.source_path
        for asset in state.document.media_assets:
            if asset.blob_hash is None:
                raise ValueError(f"asset hash missing: {asset.id}")
            await copied_evidence.get_blob(asset.blob_hash)
            asset.path = str(copied_evidence._blob_path(asset.blob_hash))
        state.schema_path = str(target / "schema.json")
        Path(state.schema_path).write_bytes(
            orjson.dumps(state.output_schema.model_dump(mode="json"))
        )
        runs = RunRepository(target / "runs")
        workflow = PrismKEWorkflow(
            MockLLMProvider(),
            DisabledOCRProvider(),
            DisabledVLMProvider(),
            JSONGraphStore(target / "graph"),
            copied_evidence,
            checkpoint,
            runs,
            embedding_provider=DisabledEmbeddingProvider(),
            review_only=True,
        )
        async with open_checkpointer(checkpoint) as saver:
            compiled = workflow._build_graph(saver)
            config = workflow._config(run_id)
            snapshot = await compiled.aget_state(config)
            if (
                not snapshot.values
                or snapshot.next
                or WorkflowState.model_validate(snapshot.values.get("payload")) != original
            ):
                raise ValueError("checkpoint does not match the paused run summary")
            await compiled.aupdate_state(
                config,
                {"payload": state.model_dump(mode="json")},
                as_node=original.current_node,
            )
        runs.save(state)
        (target / MARKER).write_bytes(
            orjson.dumps(
                {
                    "run_id": run_id,
                    "provenance": provenance(state),
                    "source_summary_sha256": file_sha256(
                        RunRepository(source / "runs")._target(run_id)
                    ),
                    "source_graph_sha256": canonical_hash(graph),
                    "offline_only": True,
                },
                option=orjson.OPT_INDENT_2,
            )
        )
        return state
    except Exception:
        # Only remove the freshly created target, never the user's source directory.
        shutil.rmtree(target)
        raise
